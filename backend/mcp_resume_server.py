"""
MCP Server: Resume Vault
========================
FastMCP stdio server providing secure filesystem resume access and
pgvector-powered semantic search for Job Description (JD) candidate matching.

Architecture Role:
    - Provides safe candidate resume file retrieval with path traversal attack protection.
    - Executes pgvector cosine distance queries against chunked CV embeddings in Neon.
    - Exposes a catalog resource (`resume://catalog`) listing all CV files.
    - Guarantees deduplication across multi-section embeddings when matching candidates.

Transport:
    stdio (Standard Input / Output) via Model Context Protocol (MCP).
"""

import os
import re
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from embeddings import get_embedding

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
RESUMES_DIR = Path(__file__).parent / "resumes"
if not RESUMES_DIR.exists():
    RESUMES_DIR = Path(__file__).parent.parent / "resumes"

# Initialize FastMCP Server for Resume Vault
mcp = FastMCP("resume-vault")

def get_db_connection():
    """
    Establishes and returns a live connection to the Neon Cloud PostgreSQL database.
    
    Returns:
        psycopg2.extensions.connection: Active database connection.
    """
    return psycopg2.connect(DATABASE_URL)


@mcp.resource("resume://catalog")
def resume_catalog() -> str:
    """
    Catalog of all candidate resume files currently stored in the secure resume vault.

    URI:
        resume://catalog

    Returns:
        str: List of filenames stored in the resumes directory.
    """
    if not RESUMES_DIR.exists():
        return "Resume vault directory is empty."
    files = list(RESUMES_DIR.glob("*.md"))
    if not files:
        return "No resumes found in vault."
    return "\n".join(f"- {f.name}" for f in files)


@mcp.tool()
def read_candidate_cv(candidate_name: str) -> str:
    """
    Safely reads the complete Markdown resume for a given candidate from the secure filesystem vault.
    Guards against path traversal attacks by validating resolved path ancestry.

    Parameters:
        candidate_name: Name of the candidate (e.g. 'Rohan Kulkarni' or 'rohan_kulkarni').

    Returns:
        str: Full Markdown content of the candidate's resume, or a secure error message.
    """
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', candidate_name.lower().strip())
    
    # Attempt direct exact match first
    target_file = RESUMES_DIR / f"{safe_name}.md"
    
    # If not found, fuzzy match against file stems in the resumes directory
    if not target_file.exists():
        matches = [f for f in RESUMES_DIR.glob("*.md") if safe_name in f.stem.lower()]
        if matches:
            target_file = matches[0]
        else:
            return f"Error: No resume found for candidate '{candidate_name}'."

    # Validate path is strictly inside RESUMES_DIR (Path Traversal & DPDP compliance defense)
    try:
        target_file.resolve().relative_to(RESUMES_DIR.resolve())
    except ValueError:
        return "Security Violation: Access denied outside the resume vault."

    with open(target_file, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool()
def match_candidates_by_jd(job_description: str, top_k: int = 3) -> str:
    """
    Performs hybrid semantic search over CV embeddings in Neon PostgreSQL using pgvector.
    Finds the best matching candidates for a given Job Description (JD) and returns
    relevance scores, candidate details, and matching resume text quotes.

    Parameters:
        job_description: Full job description text to match candidates against.
        top_k: Number of unique top matching candidates to return (default: 3).

    Returns:
        str: JSON-serialized list of candidate match objects containing candidate details,
             match percentage, matching section, and extracted resume proof quote.
    """
    query_vec = get_embedding(job_description)
    query_vec_str = "[" + ",".join(f"{x:.6f}" for x in query_vec) + "]"

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT 
                c.id AS candidate_id,
                c.name,
                c.role,
                c.experience_years,
                c.expected_ctc_lpa,
                c.stage,
                c.score AS screening_score,
                e.section_name,
                e.content AS matching_quote,
                ROUND((1 - (e.embedding <=> %s::vector))::numeric, 4) AS similarity_score
            FROM cv_embeddings e
            JOIN candidates c ON c.id = e.candidate_id
            WHERE e.section_name IN ('Experience', 'Skills', 'Summary')
            ORDER BY e.embedding <=> %s::vector ASC
            LIMIT %s;
            """,
            (query_vec_str, query_vec_str, top_k * 2)
        )
        rows = cur.fetchall()
    conn.close()

    # Deduplicate by candidate while keeping the highest similarity section
    seen = set()
    ranked = []
    for r in rows:
        cid = r["candidate_id"]
        if cid not in seen:
            seen.add(cid)
            match_pct = round(float(r["similarity_score"]) * 100, 1)
            ranked.append({
                "candidate_id": cid,
                "name": r["name"],
                "role": r["role"],
                "experience_years": float(r["experience_years"]),
                "expected_ctc_lpa": float(r["expected_ctc_lpa"]) if r["expected_ctc_lpa"] else None,
                "stage": r["stage"],
                "screening_score": r["screening_score"],
                "match_percentage": match_pct,
                "matching_section": r["section_name"],
                "resume_proof": r["matching_quote"]
            })
            if len(ranked) >= top_k:
                break

    return json.dumps(ranked)


if __name__ == "__main__":
    # Start the resume-vault FastMCP server over stdio transport
    mcp.run(transport="stdio")
