"""
CV Ingestion Pipeline
=====================
Parses incoming Markdown CV files into semantic sections, computes embeddings
via the Qwen embedding pipeline, inserts candidate metadata into Neon PostgreSQL,
and stores the source Markdown file in the secure `./resumes/` vault.

Workflow:
    1. Parse Markdown headers into semantic sections (Summary, Skills, Experience, etc.).
    2. Upsert candidate profile in `candidates` table.
    3. Generate 1536-dim normalized vector embeddings for each section.
    4. Store section embeddings in `cv_embeddings` with pgvector.
    5. Save sanitized `.md` file to `./resumes/<safe_name>.md`.
"""

import os
import re
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from embeddings import get_embedding

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
RESUMES_DIR = Path(__file__).parent / "resumes"
if not RESUMES_DIR.exists():
    RESUMES_DIR = Path(__file__).parent.parent / "resumes"
RESUMES_DIR.mkdir(parents=True, exist_ok=True)


def parse_cv_sections(cv_text: str) -> dict[str, str]:
    """
    Parses common Markdown CV headings into structured semantic sections.

    Recognizes standard section headings:
        - Summary / Professional Summary / Profile
        - Skills / Core Competencies / Technical Skills
        - Experience / Work Experience / Employment History
        - Projects / Featured Projects
        - Education / Academic Background

    Parameters:
        cv_text: Full Markdown string of the candidate's CV.

    Returns:
        dict[str, str]: Dictionary mapping section names to their text contents.
    """
    sections = {}
    current_section = "General"
    lines = cv_text.splitlines()
    buffer = []

    for line in lines:
        if line.startswith("# "):
            continue
        elif line.startswith("### ") or line.startswith("## "):
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
                buffer = []
            heading = line.lstrip("#").strip()
            # Normalize heading name
            heading_lower = heading.lower()
            if "summary" in heading_lower or "profile" in heading_lower:
                current_section = "Summary"
            elif "skill" in heading_lower or "competenc" in heading_lower:
                current_section = "Skills"
            elif "experience" in heading_lower or "work" in heading_lower:
                current_section = "Experience"
            elif "project" in heading_lower:
                current_section = "Projects"
            elif "education" in heading_lower or "academic" in heading_lower:
                current_section = "Education"
            else:
                current_section = heading
        else:
            buffer.append(line)

    if buffer:
        sections[current_section] = "\n".join(buffer).strip()

    # Guarantee core sections exist for searchability
    if "Summary" not in sections:
        sections["Summary"] = cv_text[:300].strip()
    if "Skills" not in sections:
        sections["Skills"] = "General Technical Skills"

    return sections


def ingest_new_cv(
    name: str,
    email: str,
    role: str,
    experience_years: float,
    skills: list[str],
    cv_markdown: str,
    expected_ctc_lpa: float = None,
    stage: str = "Applied",
    score: int = 50,
    notes: str = "Candidate added via CV Ingestion pipeline."
) -> dict:
    """
    End-to-End Ingestion Pipeline:
        1. Inserts or updates the candidate in Neon 'candidates' table.
        2. Parses the CV into semantic sections and embeds each using the Qwen embedding pipeline.
        3. Saves embeddings into the Neon 'cv_embeddings' pgvector table.
        4. Writes the Markdown file to ./resumes/<safe_name>.md.

    Parameters:
        name: Full candidate name.
        email: Candidate email (must be unique).
        role: Target job title.
        experience_years: Years of relevant software experience.
        skills: List of technical skills.
        cv_markdown: Raw Markdown resume content.
        expected_ctc_lpa: Expected annual CTC in LPA (optional).
        stage: Initial hiring stage ('Applied' by default).
        score: Initial screening score 0-100 (50 by default).
        notes: Recruiter notes.

    Returns:
        dict: Ingestion summary with candidate_id, filename, sections_embedded, and file_path.
    """
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    # 1. Insert or update candidate in ATS table
    cursor.execute(
        """
        INSERT INTO candidates (
            name, email, role, experience_years, skills,
            stage, score, expected_ctc_lpa, notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            name = EXCLUDED.name,
            role = EXCLUDED.role,
            experience_years = EXCLUDED.experience_years,
            skills = EXCLUDED.skills,
            expected_ctc_lpa = EXCLUDED.expected_ctc_lpa,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id;
        """,
        (name, email, role, experience_years, skills, stage, score, expected_ctc_lpa, notes)
    )
    candidate_id = cursor.fetchone()[0]

    # 2. Parse & embed CV sections
    sections = parse_cv_sections(cv_markdown)
    cursor.execute("DELETE FROM cv_embeddings WHERE candidate_id = %s;", (candidate_id,))

    saved_chunks = 0
    for section_name, content in sections.items():
        if not content.strip():
            continue
        text_to_embed = f"{name} - {role} - {section_name}: {content}"
        vec = get_embedding(text_to_embed)
        emb_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

        cursor.execute(
            """
            INSERT INTO cv_embeddings (candidate_id, section_name, content, embedding)
            VALUES (%s, %s, %s, %s::vector);
            """,
            (candidate_id, section_name, content, emb_str)
        )
        saved_chunks += 1

    # 3. Save Markdown file to ./resumes/
    safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower()) + ".md"
    file_path = RESUMES_DIR / safe_filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(cv_markdown.strip() + "\n")

    cursor.close()
    conn.close()

    return {
        "status": "success",
        "candidate_id": candidate_id,
        "name": name,
        "filename": safe_filename,
        "sections_embedded": saved_chunks,
        "file_path": str(file_path)
    }


if __name__ == "__main__":
    # Test execution for standalone verification
    test_cv = """# Sample Developer
**Role**: Cloud Infrastructure Engineer  
**Email**: sample.dev@example.com | **Location**: Hyderabad, India  

### Professional Summary
Experienced cloud infrastructure engineer with 4 years managing AWS architectures and Terraform templates.

### Core Skills
- AWS, Terraform, Docker, Kubernetes, Python

### Work Experience
**Cloud Engineer** — NetSolutions (2022 – Present)
- Automated EC2 deployments and RDS backups using Terraform.
"""
    result = ingest_new_cv(
        name="Sample Developer",
        email="sample.dev@example.com",
        role="Cloud Infrastructure Engineer",
        experience_years=4.0,
        skills=["AWS", "Terraform", "Docker", "Kubernetes", "Python"],
        cv_markdown=test_cv
    )
    print("Ingestion Test Result:", result)
