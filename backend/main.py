"""
Recruitment Copilot FastAPI Application
======================================
REST API backend connecting the React frontend to the Neon PostgreSQL database
and the Dual Model Context Protocol (MCP) servers.

Endpoints:
    - GET  /                     : Health check and service metadata.
    - GET  /api/candidates       : List all candidates ordered by score.
    - GET  /api/pipeline/summary : Real-time pipeline aggregation from MCP resource.
    - GET  /api/resumes/{name}   : Retrieve full candidate Markdown CV.
    - POST /api/chat             : Interactive ReAct agent chat with MCP tool tracing.
    - POST /api/match-jd         : Semantic JD candidate matching via pgvector.
    - PATCH /api/candidates/stage: Update candidate stage and screening score.
    - POST /api/candidates/upload: End-to-end CV ingestion and embedding.
"""

import os
import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

from agent_host import MCPRecruiterHost
from ingestion import ingest_new_cv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
RESUMES_DIR = Path(__file__).parent / "resumes"
if not RESUMES_DIR.exists():
    RESUMES_DIR = Path(__file__).parent.parent / "resumes"

# Global MCP Host instance managing stdio child processes
host = MCPRecruiterHost()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifecycle of the FastAPI application and MCP servers.
    Initializes both MCP child processes on startup and shuts them down on exit.
    """
    print("[API] Initializing MCP Recruiter Host...")
    await host.initialize()
    print("[API] MCP Recruiter Host ready!")
    yield
    print("[API] Shutting down MCP Recruiter Host...")
    await host.close()

app = FastAPI(
    title="Recruitment Copilot API",
    description="Backend API powered by Neon PostgreSQL (pgvector) and Dual MCP Servers",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend (Vite defaults to port 5173 / 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    """Returns a new psycopg2 connection to Neon PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)


# --- Pydantic Request Schemas ---

class ChatRequest(BaseModel):
    """Schema for recruiter chat message and conversation history."""
    message: str
    history: list[dict] = []

class MatchJDRequest(BaseModel):
    """Schema for Job Description matching request."""
    job_description: str
    top_k: int = 3

class UpdateStageRequest(BaseModel):
    """Schema for updating candidate stage and score."""
    candidate_id: int
    new_stage: Literal["Applied", "Shortlisted", "Interview", "Offer", "Rejected"]
    score: int | None = None
    notes: str | None = None

class UploadCVRequest(BaseModel):
    """Schema for manual or automated CV upload and ingestion."""
    name: str
    email: EmailStr
    role: str
    experience_years: float
    skills: list[str]
    cv_markdown: str
    expected_ctc_lpa: float | None = None
    stage: Literal["Applied", "Shortlisted", "Interview", "Offer", "Rejected"] = "Applied"
    score: int = 50
    notes: str = ""


# --- REST Endpoints ---

@app.get("/")
def health_check():
    """
    Service health check returning online status, database type, and active MCP servers.
    """
    return {
        "status": "online",
        "service": "Recruitment Copilot API",
        "database": "Neon PostgreSQL (pgvector)",
        "mcp_servers": ["candidate-tracker", "resume-vault"]
    }


@app.get("/api/candidates")
def list_all_candidates():
    """
    Returns all candidates from the Neon ATS table ordered by score descending.
    """
    conn = get_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM candidates ORDER BY score DESC, id ASC;")
        rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/pipeline/summary")
async def get_pipeline_summary():
    """
    Fetches real-time pipeline aggregation from the 'hiring://pipeline-summary' MCP resource
    and supplements it with SQL group-by counts and average scores.
    """
    summary_text = await host.get_pipeline_resource()
    conn = get_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT stage, COUNT(*) AS count, ROUND(AVG(score), 1) AS avg_score
            FROM candidates
            GROUP BY stage;
            """
        )
        stages = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM candidates;")
        total = cur.fetchone()["count"]
    conn.close()
    return {
        "summary_text": summary_text,
        "total_candidates": total,
        "stages": [dict(s) for s in stages]
    }


@app.get("/api/resumes/{candidate_name}")
def get_candidate_resume(candidate_name: str):
    """
    Retrieves the full Markdown resume for a given candidate from the secure filesystem vault.
    Guards against path traversal by resolving inside RESUMES_DIR.
    """
    safe_name = candidate_name.lower().replace(" ", "_").strip()
    target = RESUMES_DIR / f"{safe_name}.md"
    if not target.exists():
        matches = [f for f in RESUMES_DIR.glob("*.md") if safe_name in f.stem.lower()]
        if matches:
            target = matches[0]
        else:
            raise HTTPException(status_code=404, detail=f"Resume for '{candidate_name}' not found.")
    
    with open(target, "r", encoding="utf-8") as f:
        content = f.read()
    return {"candidate_name": candidate_name, "content": content}


@app.post("/api/chat")
async def chat_with_copilot(req: ChatRequest):
    """
    Interactive conversational endpoint executing the multi-turn ReAct agent loop
    against OpenRouter and returning both LLM response and MCP tool execution logs.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    result = await host.chat(user_message=req.message, history=req.history)
    return result


@app.post("/api/match-jd")
async def match_job_description(req: MatchJDRequest):
    """
    Direct Job Description matching returning ranked candidates with cosine similarity percentages
    and extracted CV proof quotes using the resume-vault MCP tool.
    """
    if not req.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    
    if "resumes" in host.sessions:
        tool_res = await host.sessions["resumes"].call_tool(
            "match_candidates_by_jd",
            arguments={"job_description": req.job_description, "top_k": req.top_k}
        )
        import json
        import ast
        text_content = "".join(c.text for c in tool_res.content if hasattr(c, "text"))
        try:
            candidates = json.loads(text_content)
        except Exception:
            try:
                candidates = ast.literal_eval(text_content)
            except Exception:
                candidates = text_content
        return {"matches": candidates}
    raise HTTPException(status_code=500, detail="Resume vault server is unavailable.")


@app.patch("/api/candidates/stage")
async def update_candidate_stage(req: UpdateStageRequest):
    """
    Updates candidate hiring stage, screening score, and recruiter notes via the candidate-tracker MCP tool.
    """
    if "tracker" in host.sessions:
        res = await host.sessions["tracker"].call_tool(
            "update_candidate_stage",
            arguments={
                "candidate_id": req.candidate_id,
                "new_stage": req.new_stage,
                "score": req.score,
                "notes": req.notes
            }
        )
        import json
        text_content = "".join(c.text for c in res.content if hasattr(c, "text"))
        try:
            return json.loads(text_content)
        except Exception:
            return {"raw": text_content}
    raise HTTPException(status_code=500, detail="Candidate tracker server is unavailable.")


@app.post("/api/candidates/upload")
def upload_and_ingest_cv(req: UploadCVRequest):
    """
    Ingests a new CV into Neon ATS table, generates vector embeddings with Qwen,
    and stores the markdown resume in the secure resume vault.
    """
    result = ingest_new_cv(
        name=req.name,
        email=req.email,
        role=req.role,
        experience_years=req.experience_years,
        skills=req.skills,
        cv_markdown=req.cv_markdown,
        expected_ctc_lpa=req.expected_ctc_lpa,
        stage=req.stage,
        score=req.score,
        notes=req.notes
    )
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
