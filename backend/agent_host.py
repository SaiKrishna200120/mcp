"""
MCP Recruiter Host & ReAct Agent
================================
Orchestrates multi-turn Reasoning & Action (ReAct) agent execution over
Model Context Protocol (MCP) tools.

Architecture:
    1. Subprocess Management: Spawns both `candidate-tracker` and `resume-vault`
       MCP servers as stdio child processes.
    2. Tool Router: Namespaces tools with prefixes (`tracker__*`, `resumes__*`)
       and converts FastMCP input schemas into OpenAI function calling format.
    3. Resource Reader: Reads the live `hiring://pipeline-summary` resource.
    4. Bounded ReAct Loop: Runs up to `max_turns=5` autonomous reasoning iterations,
       handling tool execution, error recovery, and tool call tracing.
"""

import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

load_dotenv()
PROJECT_DIR = Path(__file__).parent.resolve()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "openrouter/free")


class MCPRecruiterHost:
    """
    Multi-server MCP Client and ReAct Agent Host for the AI Recruitment Copilot.
    """

    def __init__(self):
        """Initializes the host, exit stack, session storage, and OpenAI API client."""
        self.stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.tool_router: dict[str, tuple[str, str]] = {}
        self.openai_tools: list[dict] = []
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://localhost:8000",
                "X-Title": "Recruitment Copilot Host",
            },
        )
        self.system_prompt = (
            "You are an expert AI HR Recruitment Copilot with direct access to an ATS candidate database "
            "and candidate CV vault via Model Context Protocol (MCP) tools.\n\n"
            "Guidelines:\n"
            "1. ALWAYS call MCP tools to fetch live database and resume facts before answering.\n"
            "2. When answering about top candidates, stages, or scores, query the 'tracker' tools.\n"
            "3. When asked to match a Job Description (JD), use 'resumes__match_candidates_by_jd' to find matches "
            "and cite evidence from their CV.\n"
            "4. When moving candidate stages or updating scores, call 'tracker__update_candidate_stage'.\n"
            "5. Format responses cleanly with Markdown tables, bold metrics, and structured bullet points.\n"
            "6. Never guess or hallucinate candidate records that do not exist in the database."
        )

    async def initialize(self):
        """
        Starts both stdio MCP servers (candidate-tracker and resume-vault) as child processes,
        initializes ClientSessions, lists exposed tools, and registers them in the tool router.
        """
        python_exe = sys.executable

        servers = {
            "tracker": StdioServerParameters(
                command=python_exe,
                args=[str(PROJECT_DIR / "mcp_candidate_server.py")],
                env=os.environ.copy()
            ),
            "resumes": StdioServerParameters(
                command=python_exe,
                args=[str(PROJECT_DIR / "mcp_resume_server.py")],
                env=os.environ.copy()
            )
        }

        self.tool_router.clear()
        self.openai_tools.clear()

        for srv_name, params in servers.items():
            read, write = await self.stack.enter_async_context(
                stdio_client(params, errlog=sys.stderr)
            )
            session = await self.stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[srv_name] = session

            tools_resp = await session.list_tools()
            for tool in tools_resp.tools:
                exposed_name = f"{srv_name}__{tool.name}"
                self.tool_router[exposed_name] = (srv_name, tool.name)
                self.openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": exposed_name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema,
                        },
                    }
                )

        print(f"[Host] Initialized {len(self.sessions)} servers with {len(self.openai_tools)} exposed tools.")

    async def get_pipeline_resource(self) -> str:
        """
        Directly reads the read-only 'hiring://pipeline-summary' MCP resource from the candidate-tracker server.

        Returns:
            str: Resource text content from the MCP server.
        """
        if "tracker" in self.sessions:
            try:
                res = await self.sessions["tracker"].read_resource("hiring://pipeline-summary")
                return "\n".join(c.text for c in res.contents if hasattr(c, "text"))
            except Exception as e:
                return f"Error reading pipeline resource: {e}"
        return "Tracker server not initialized."

    async def chat(self, user_message: str, history: list[dict] = None, max_turns: int = 5) -> dict:
        """
        Executes bounded ReAct agent loop against OpenRouter with tool execution trace.

        Parameters:
            user_message: Recruiter's prompt or question.
            history: Optional conversation history as list of dicts (role, content).
            max_turns: Maximum reasoning turns before returning (default: 5).

        Returns:
            dict: Response dictionary containing 'reply', 'tools_used', and 'turns'.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if history:
            for turn in history:
                if isinstance(turn, dict) and "role" in turn and "content" in turn:
                    messages.append({"role": turn["role"], "content": str(turn["content"])})

        messages.append({"role": "user", "content": user_message})
        tool_logs = []
        turn_count = 0

        while turn_count < max_turns:
            turn_count += 1
            try:
                resp = await self.client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=messages,
                    tools=self.openai_tools if self.openai_tools else None,
                    extra_body={"provider": {"require_parameters": True}},
                )
            except Exception as e:
                return {
                    "reply": f"API Error communicating with OpenRouter ({e}).",
                    "tools_used": tool_logs,
                    "error": str(e)
                }

            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            # If no tool calls, the model provided its final answer
            if not msg.tool_calls:
                return {
                    "reply": msg.content or "No response generated.",
                    "tools_used": tool_logs,
                    "turns": turn_count
                }

            # Execute tool calls
            for tc in msg.tool_calls:
                func_name = tc.function.name
                if func_name not in self.tool_router:
                    output_text = f"Error: Tool '{func_name}' is not recognized."
                else:
                    srv_name, orig_tool = self.tool_router[func_name]
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}

                    tool_logs.append({
                        "server": srv_name,
                        "tool": orig_tool,
                        "arguments": args
                    })

                    try:
                        result = await self.sessions[srv_name].call_tool(orig_tool, arguments=args)
                        if result.isError:
                            output_text = f"Tool Error: {result.content}"
                        else:
                            output_text = "\n".join(
                                c.text for c in result.content if hasattr(c, "text")
                            )
                    except Exception as e:
                        output_text = f"Execution Exception: {str(e)}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": output_text
                })

        return {
            "reply": "Reached maximum tool execution turns (5). Please narrow your query.",
            "tools_used": tool_logs,
            "turns": turn_count
        }

    async def close(self):
        """Gracefully closes all MCP child sessions and stdio pipes."""
        await self.stack.aclose()


if __name__ == "__main__":
    async def main():
        host = MCPRecruiterHost()
        await host.initialize()
        
        # Test 1: Resource read
        print("\n=== Reading Resource: hiring://pipeline-summary ===")
        res = await host.get_pipeline_resource()
        print(res)

        # Test 2: Top candidates query
        print("\n=== Test Prompt: Top candidates above 80 ===")
        ans = await host.chat("Who are the top candidates with a score above 80?")
        print("Tools Used:", ans["tools_used"])
        print("\nAgent Reply:\n", ans["reply"])

        await host.close()

    asyncio.run(main())
