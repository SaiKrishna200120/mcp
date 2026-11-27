/**
 * AI Copilot Chat Tab Component
 * ==============================
 * Interactive conversational interface connected to the backend ReAct agent.
 * Features:
 *   - Auto-scrolling chat history with role-based formatting.
 *   - Collapsible MCP tool execution trace drawer showing server, tool, and arguments.
 *   - Quick prompt chips for common recruiter workflows.
 */

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Wrench, Sparkles, ChevronDown, ChevronRight, CheckCircle2 } from "lucide-react";
import { sendChatMessage } from "../api";

export default function ChatTab() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hello! I am your **AI Recruitment Copilot**. I have live access to your **Neon PostgreSQL candidate database** and **secure resume vault** via Model Context Protocol (MCP) tools.\n\nYou can ask me to evaluate candidates, match job descriptions, move stages, or generate pipeline reports.",
      tools: []
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const samplePrompts = [
    "Who are the top candidates with a score above 80?",
    "Move Rohan Kulkarni to Shortlisted and update his score to 76.",
    "Give me a complete hiring pipeline summary grouped by stage.",
    "Compare Aarav Sharma and Rohan Kulkarni for a backend lead role."
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMessage = { role: "user", content: text };
    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    try {
      // Send conversation history to backend ReAct host
      const apiHistory = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await sendChatMessage(text, apiHistory);

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: response.reply,
          tools: response.tools_used || []
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error communicating with the backend. Please ensure the FastAPI server is running on port 8000.",
          tools: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "calc(100vh - 80px)",
      maxWidth: "1000px",
      margin: "0 auto",
      padding: "20px"
    }}>
      {/* Sample Quick Prompt Chips */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        overflowX: "auto",
        paddingBottom: "12px",
        marginBottom: "12px"
      }}>
        <Sparkles size={16} color="#818cf8" style={{ flexShrink: 0 }} />
        {samplePrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            style={{
              padding: "6px 14px",
              borderRadius: "20px",
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              color: "#cbd5e1",
              fontSize: "12px",
              whiteSpace: "nowrap",
              transition: "all 0.15s ease",
              flexShrink: 0
            }}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Message History Container */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        gap: "18px",
        paddingRight: "8px"
      }}>
        {messages.map((msg, index) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={index}
              style={{
                display: "flex",
                gap: "12px",
                alignSelf: isUser ? "flex-end" : "flex-start",
                maxWidth: "85%"
              }}
            >
              {!isUser && (
                <div style={{
                  width: "34px",
                  height: "34px",
                  borderRadius: "8px",
                  backgroundColor: "#4f46e5",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0
                }}>
                  <Bot size={18} color="#ffffff" />
                </div>
              )}

              <div style={{
                backgroundColor: isUser ? "#4f46e5" : "#1e293b",
                border: isUser ? "none" : "1px solid #334155",
                borderRadius: "14px",
                padding: "16px 20px",
                color: "#f8fafc",
                fontSize: "14px",
                lineHeight: "1.6",
                boxShadow: "0 4px 14px rgba(0,0,0,0.2)"
              }}>
                {/* Collapsible MCP Tool Calls Drawer */}
                {!isUser && msg.tools && msg.tools.length > 0 && (
                  <ToolExecutionTrace tools={msg.tools} />
                )}

                {/* Message Body */}
                <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {msg.content}
                </div>
              </div>

              {isUser && (
                <div style={{
                  width: "34px",
                  height: "34px",
                  borderRadius: "8px",
                  backgroundColor: "#334155",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0
                }}>
                  <User size={18} color="#cbd5e1" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div style={{ display: "flex", gap: "12px", alignSelf: "flex-start" }}>
            <div style={{
              width: "34px",
              height: "34px",
              borderRadius: "8px",
              backgroundColor: "#4f46e5",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <Bot size={18} color="#ffffff" />
            </div>
            <div style={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "14px",
              padding: "12px 18px",
              color: "#94a3b8",
              fontSize: "13px",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}>
              <span>Routing query across MCP servers & Neon database...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        style={{
          marginTop: "16px",
          display: "flex",
          gap: "10px",
          backgroundColor: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "12px",
          padding: "8px 12px",
          alignItems: "center"
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything (e.g. 'Move Rohan to Shortlisted' or 'Who knows Kubernetes?')..."
          disabled={loading}
          style={{
            flex: 1,
            backgroundColor: "transparent",
            border: "none",
            outline: "none",
            color: "#f8fafc",
            fontSize: "14px"
          }}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            backgroundColor: input.trim() ? "#4f46e5" : "#334155",
            color: "#ffffff",
            padding: "8px 16px",
            borderRadius: "8px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "13px",
            fontWeight: 600,
            transition: "all 0.2s"
          }}
        >
          <Send size={15} />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
}

/**
 * Collapsible Tool Execution Drawer
 * Visualizes the exact MCP tools invoked by the ReAct agent, including server origin and arguments.
 */
function ToolExecutionTrace({ tools }) {
  const [open, setOpen] = useState(false);

  return (
    <div style={{
      marginBottom: "12px",
      borderRadius: "8px",
      backgroundColor: "rgba(0,0,0,0.25)",
      border: "1px solid rgba(255,255,255,0.08)",
      fontSize: "12px",
      overflow: "hidden"
    }}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        style={{
          width: "100%",
          padding: "6px 12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          color: "#818cf8",
          fontWeight: 600,
          backgroundColor: "rgba(99, 102, 241, 0.08)"
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Wrench size={13} />
          <span>MCP Tools Executed ({tools.length})</span>
        </span>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>

      {open && (
        <div style={{ padding: "8px 12px", display: "flex", flexDirection: "column", gap: "6px" }}>
          {tools.map((t, idx) => (
            <div key={idx} style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "6px",
              fontFamily: "monospace",
              color: "#cbd5e1"
            }}>
              <CheckCircle2 size={13} color="#34d399" style={{ marginTop: "2px", flexShrink: 0 }} />
              <div>
                <strong style={{ color: "#38bdf8" }}>{t.server}</strong>.{t.tool}
                <span style={{ color: "#94a3b8" }}>({JSON.stringify(t.arguments)})</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
