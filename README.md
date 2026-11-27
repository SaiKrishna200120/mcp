<<<<<<< HEAD
# AI Recruitment Copilot

> An end-to-end **Agentic Hybrid RAG** system that combines **LLM + pgvector semantic search + Model Context Protocol (MCP)** to intelligently match candidates to job descriptions, manage an ATS pipeline, and provide an interactive AI recruiter chat — all powered by a React frontend, FastAPI backend, and Neon Cloud PostgreSQL.

---

## Architecture

```mermaid
graph TD
    UI["React Frontend<br/>(Vite + Lucide)"]
    API["FastAPI Backend<br/>(REST + CORS)"]
    HOST["MCP Agent Host<br/>(ReAct Loop)"]
    MCP1["MCP Server 1<br/>candidate-tracker"]
    MCP2["MCP Server 2<br/>resume-vault"]
    NEON["Neon PostgreSQL<br/>(pgvector)"]
    LLM["OpenRouter LLM<br/>(Free Tier)"]
    EMB["Qwen Embedding<br/>qwen3-embedding-8b"]

    UI -->|HTTP| API
    API --> HOST
    HOST -->|stdio| MCP1
    HOST -->|stdio| MCP2
    HOST -->|chat.completions| LLM
    MCP1 -->|SQL| NEON
    MCP2 -->|SQL + cosine| NEON
    MCP2 --> EMB
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Dual MCP servers** (tracker + vault) | Separation of concerns: ATS pipeline management vs. semantic CV search |
| **pgvector cosine similarity** | True semantic JD↔CV matching, not keyword search |
| **Qwen embeddings via OpenRouter** | Free cloud-hosted embedding model, no local GPU required |
| **ReAct agent loop (max 5 turns)** | Bounded reasoning prevents infinite loops; LLM autonomously decides which MCP tools to call |
| **FastAPI lifespan** | MCP servers initialize once at startup, shared across all requests |
| **Vite proxy** | Frontend dev server proxies `/api/*` to FastAPI; zero CORS issues in dev |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Database** | Neon Cloud PostgreSQL + pgvector (HNSW index) |
| **Embeddings** | Qwen `qwen3-embedding-8b` via OpenRouter API |
| **LLM** | `openrouter/free` (auto-routes to best free model) |
| **Backend** | Python 3.10 + FastAPI + FastMCP + OpenAI SDK |
| **Frontend** | React 19 + Vite + Lucide Icons |
| **Protocol** | Model Context Protocol (MCP) over stdio |

---

## Project Structure

```
project/
├── backend/                   # Python FastAPI & Dual MCP Servers
│   ├── main.py                # FastAPI backend (REST endpoints + MCP lifecycle)
│   ├── agent_host.py          # MCP Host — ReAct agent loop with tool routing
│   ├── mcp_candidate_server.py# MCP Server 1: candidate-tracker (ATS CRUD)
│   ├── mcp_resume_server.py   # MCP Server 2: resume-vault (CV search + pgvector)
│   ├── embeddings.py          # Qwen embedding pipeline (cloud + fallback)
│   ├── ingestion.py           # CV ingestion: parse → embed → insert into Neon
│   ├── seed_neon.py           # Database seed script (6 candidates + embeddings)
│   └── requirements.txt       # Backend dependencies
├── frontend/                  # React application (Vite)
│   ├── vite.config.js         # Proxy config → localhost:8000
│   └── src/
│       ├── App.jsx            # Tab router (Chat / JD Matcher / Pipeline)
│       ├── api.js             # API client for all backend endpoints
│       ├── index.css          # Dark theme global styles
│       └── components/
│           ├── Navbar.jsx     # Header with tabs + system telemetry badges
│           ├── ChatTab.jsx    # AI chat with MCP tool execution trace
│           ├── JDMatcherTab.jsx # JD paste → ranked candidate cards
│           ├── PipelineTab.jsx # ATS pipeline table with stage management
│           └── ResumeModal.jsx # Candidate CV viewer modal
├── evals/
│   └── test_suite.py          # 5-prompt deterministic eval suite
├── resumes/                   # Markdown CV files (6 candidates)
├── run_backend.bat            # One-click Windows batch script for backend
├── run_frontend.bat           # One-click Windows batch script for frontend
├── start_all.bat              # One-click master launcher (backend + frontend + browser)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── .gitignore
```

---

## How to Run

### Quick Start (Windows Batch Files)

Double-click or run:
- **`start_all.bat`**: Launches both backend and frontend servers in separate windows and automatically opens `http://localhost:5173` in your default browser.
- **`run_backend.bat`**: Runs the FastAPI backend and dual MCP servers.
- **`run_frontend.bat`**: Runs the React development server.

---

### Manual Run

#### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- A [Neon Cloud](https://neon.tech) PostgreSQL database with pgvector enabled
- An [OpenRouter](https://openrouter.ai) API key (free tier works)

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd project

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL and OPENROUTER_API_KEY
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed the Database

```bash
python seed_neon.py
```

This creates the `candidates` and `cv_embeddings` tables, inserts 6 sample candidates with realistic profiles, and generates embedding vectors for their CVs.

### 4. Start the Backend

```bash
python main.py
```

This starts:
- FastAPI server on `http://localhost:8000`
- Two MCP servers (candidate-tracker + resume-vault) as stdio subprocesses
- The ReAct agent host connected to OpenRouter

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 6. Run the Eval Suite

```bash
# With the backend running:
python evals/test_suite.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/candidates` | List all candidates (sorted by score) |
| `GET` | `/api/pipeline/summary` | Pipeline stage counts + averages |
| `GET` | `/api/resumes/{name}` | Get candidate's markdown CV |
| `POST` | `/api/chat` | AI chat (ReAct agent with MCP tools) |
| `POST` | `/api/match-jd` | JD → ranked candidate matches (pgvector) |
| `PATCH` | `/api/candidates/stage` | Update candidate stage/score |
| `POST` | `/api/candidates/upload` | Ingest new CV (parse + embed + insert) |

---

## Frontend Tabs

### 1. AI Copilot Chat
Interactive chat with the ReAct agent. The LLM autonomously calls MCP tools (tracker + resume vault) to answer questions. Features a collapsible tool execution trace showing exactly which MCP tools were called with what arguments.

**Sample prompts:**
- "Who are the top candidates with a score above 80?"
- "Move Rohan Kulkarni to Shortlisted and update his score to 76"
- "Compare Aarav Sharma and Rohan Kulkarni for a backend lead role"

### 2. JD Talent Matcher
Paste a Job Description → the system embeds it with Qwen, runs pgvector cosine similarity against all CV chunks, and returns ranked candidate cards with match percentages and CV evidence quotes.

### 3. ATS Candidate Pipeline
Full pipeline view with stage summary cards, sortable/filterable candidate table, inline stage dropdown to move candidates through the pipeline, and one-click resume viewing.

---

## MCP Servers

### candidate-tracker
- **Resource:** `hiring://pipeline-summary` — aggregated stage counts and average scores
- **Tools:** `list_candidates`, `get_candidate_profile`, `update_candidate_stage`, `add_candidate`
- All queries use parameterized SQL (`%s` placeholders)

### resume-vault
- **Resource:** `resume://catalog` — lists all CV files
- **Tools:** `read_candidate_cv` (with path traversal protection), `match_candidates_by_jd` (pgvector cosine search with deduplication)

---

## Eval Suite

The eval suite (`evals/test_suite.py`) runs 5 deterministic tests:

| # | Test | Validates |
|---|------|-----------|
| 1 | Top candidates ≥ 80 | LLM calls MCP tools, returns ≥3 known candidates |
| 2 | Update candidate stage | PATCH API modifies DB, verifies change |
| 3 | Pipeline summary | Stage counts match candidate list |
| 4 | JD matching | pgvector returns ranked matches with required fields |
| 5 | Path traversal | `../../etc/passwd` blocked by resume vault |

---

## Reviewer Feedback Addressed

| Issue | Resolution |
|-------|-----------|
| API key leaked in notebook | New key; `.env` + `.gitignore` protect credentials |
| Two duplicate server copies | Single `mcp_candidate_server.py` with full features |
| Client never reads MCP resource | `agent_host.py` has `get_pipeline_resource()` |
| Gradio async bug | Eliminated — replaced with FastAPI + React |
| No loop limit on tool calls | `max_turns=5` in ReAct loop |
| Unguarded `json.loads` / `tool_router` | Both wrapped in try/except |
| `result.isError` unchecked | Checked in agent_host.py |
| History as strings not dicts | Fixed — list[dict] throughout |
| "No candidates ≥ 80" wrong DB | Single Neon DB with 5 candidates scoring ≥80 |
| Missing filesystem/resume server | `mcp_resume_server.py` with path traversal guard |
| No requirements.txt | Created with all dependencies |
| No eval suite | 5-prompt eval suite in `evals/test_suite.py` |

---

## Environment Variables

```env
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=openrouter/free
EMBEDDING_MODEL=qwen/qwen3-embedding-8b
```

---

## License

This project is a capstone demonstration of Agentic AI, Hybrid RAG, and Model Context Protocol concepts. Built for educational purposes.
=======
# mcp
mcp
# HR Candidate Tracker — Model Context Protocol (MCP) Demo

 **Model Context Protocol (MCP)**, **SQLite**, **OpenRouter**, and **Gradio**. 

This project demonstrates how an LLM Host can dynamically discover and orchestrate tools across **two independent MCP servers**—a **custom Python FastMCP server** for structured database operations and a **built-in Filesystem MCP server** for reading local candidate resumes—through a natural-language chat interface.

---



>>>>>>> a62bcb4118a59f0fa2f8612c33ba17c49c9acb3a
