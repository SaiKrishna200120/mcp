"""
MCP Server: Candidate Tracker
=============================
FastMCP stdio server providing candidate tracking and ATS management tools.
Directly communicates with Neon Cloud PostgreSQL.

Architecture Role:
    - Provides ATS candidate listing, profile queries, stage progression, and insertion.
    - Exposes a read-only hiring pipeline summary resource (`hiring://pipeline-summary`).
    - Enforces parameterization against SQL injection attacks.
    - Uses strict Literal types and bounds checking (0-100 score).

Transport:
    stdio (Standard Input / Output) via Model Context Protocol (MCP).
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Literal
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize FastMCP Server for Candidate Tracking
mcp = FastMCP("candidate-tracker")

def get_db_connection():
    """
    Establishes and returns a live connection to the Neon Cloud PostgreSQL database.
    
    Returns:
        psycopg2.extensions.connection: Active database connection.
    """
    return psycopg2.connect(DATABASE_URL)


@mcp.resource("hiring://pipeline-summary")
def pipeline_summary() -> str:
    """
    Read-only resource summarizing candidate counts and average scores grouped by hiring stage.

    URI:
        hiring://pipeline-summary

    Returns:
        str: Human-readable multi-line summary of pipeline stages, counts, and average scores.
    """
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT stage, COUNT(*) AS total, ROUND(AVG(score), 1) AS avg_score
            FROM candidates
            GROUP BY stage
            ORDER BY total DESC;
            """
        )
        rows = cur.fetchall()
    conn.close()

    if not rows:
        return "No candidates in pipeline."
    return "\n".join(
        f"{r['stage']}: {r['total']} candidates (avg score: {r['avg_score']})"
        for r in rows
    )


@mcp.tool()
def list_candidates(
    stage: Literal["All", "Applied", "Shortlisted", "Interview", "Offer", "Rejected"] = "All",
    role_keyword: str = "",
    min_score: int = 0,
) -> list[dict]:
    """
    Fetch candidates from the Neon ATS table, optionally filtered by hiring stage, role keyword, or minimum score.

    Parameters:
        stage: Hiring stage to filter by ('All', 'Applied', 'Shortlisted', 'Interview', 'Offer', 'Rejected').
        role_keyword: Case-insensitive substring to search within candidate roles or skill sets.
        min_score: Minimum screening score (0 to 100). Default is 0.

    Returns:
        list[dict]: List of candidate records matching the search criteria.
    """
    query = (
        "SELECT id, name, email, role, experience_years, skills, stage, score, expected_ctc_lpa, notes "
        "FROM candidates WHERE COALESCE(score, 0) >= %s"
    )
    params = [min_score]

    if stage != "All":
        query += " AND stage = %s"
        params.append(stage)

    if role_keyword:
        query += " AND (role ILIKE %s OR %s = ANY(skills))"
        params.extend([f"%{role_keyword}%", role_keyword])

    query += " ORDER BY score DESC, id ASC;"

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@mcp.tool()
def get_candidate_profile(candidate_id: int) -> dict:
    """
    Retrieve full profile and ATS details for a specific candidate by their unique ID.

    Parameters:
        candidate_id: Integer primary key of the candidate in Neon PostgreSQL.

    Returns:
        dict: Full candidate profile record or an error dictionary if not found.
    """
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM candidates WHERE id = %s;", (candidate_id,))
        row = cur.fetchone()
    conn.close()

    if not row:
        return {"error": f"Candidate with id={candidate_id} not found."}
    return dict(row)


@mcp.tool()
def update_candidate_stage(
    candidate_id: int,
    new_stage: Literal["Applied", "Shortlisted", "Interview", "Offer", "Rejected"],
    score: int | None = None,
    notes: str | None = None,
) -> dict:
    """
    Update a candidate's hiring stage, optional evaluation score (0-100), and recruiter notes.

    Parameters:
        candidate_id: The ID of the candidate to update.
        new_stage: Valid ATS stage ('Applied', 'Shortlisted', 'Interview', 'Offer', 'Rejected').
        score: Optional integer screening score between 0 and 100.
        notes: Optional recruiter notes to append or overwrite.

    Returns:
        dict: Updated candidate summary including updated_fields or error details.
    """
    if score is not None and not (0 <= score <= 100):
        return {"error": "Score must be an integer between 0 and 100."}

    updates = ["stage = %s", "updated_at = CURRENT_TIMESTAMP"]
    params = [new_stage]

    if score is not None:
        updates.append("score = %s")
        params.append(score)

    if notes is not None:
        updates.append("notes = %s")
        params.append(notes)

    params.append(candidate_id)
    query = f"UPDATE candidates SET {', '.join(updates)} WHERE id = %s RETURNING id, name, stage, score, notes;"

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, tuple(params))
        updated = cur.fetchone()
        conn.commit()
    conn.close()

    if not updated:
        return {"error": f"Candidate with id={candidate_id} not found."}

    return {
        "status": "success",
        "candidate": dict(updated),
        "message": f"Candidate #{candidate_id} stage updated to '{new_stage}'."
    }


@mcp.tool()
def add_candidate(
    name: str,
    email: str,
    role: str,
    experience_years: float,
    skills: list[str],
    stage: Literal["Applied", "Shortlisted", "Interview", "Offer", "Rejected"] = "Applied",
    score: int = 50,
    expected_ctc_lpa: float | None = None,
    notes: str = "",
) -> dict:
    """
    Insert a new candidate directly into the ATS database.

    Parameters:
        name: Full legal name of the candidate.
        email: Contact email address (must be unique).
        role: Primary target job role (e.g. 'Senior Full Stack Engineer').
        experience_years: Total years of professional software experience.
        skills: List of technical skills, languages, and tools.
        stage: Initial hiring stage. Defaults to 'Applied'.
        score: Initial screening score (0 to 100). Defaults to 50.
        expected_ctc_lpa: Expected annual compensation in Lakhs Per Annum (INR).
        notes: Recruiter or referral notes.

    Returns:
        dict: Confirmation with the newly generated candidate ID.
    """
    if not (0 <= score <= 100):
        return {"error": "Score must be between 0 and 100."}

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            cur.execute(
                """
                INSERT INTO candidates (
                    name, email, role, experience_years, skills,
                    stage, score, expected_ctc_lpa, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, email, stage, score;
                """,
                (name, email, role, experience_years, skills, stage, score, expected_ctc_lpa, notes)
            )
            created = cur.fetchone()
            conn.commit()
        except psycopg2.IntegrityError as e:
            conn.rollback()
            conn.close()
            return {"error": f"Candidate insertion failed (duplicate email or constraint violation): {e}"}
    conn.close()

    return {
        "status": "success",
        "candidate": dict(created),
        "message": f"Candidate '{name}' successfully added with id={created['id']}."
    }


if __name__ == "__main__":
    # Start the candidate-tracker FastMCP server over stdio transport
    mcp.run(transport="stdio")
