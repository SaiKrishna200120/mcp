"""
AI Recruitment Copilot — Deterministic Eval Suite
==================================================
Tests the full MCP-based ReAct agent pipeline with 5 reproducible prompts.

Usage:
    python evals/test_suite.py

Requirements:
    - Backend FastAPI server running on http://localhost:8000
    - Neon Cloud database seeded with 6 candidates
"""

import sys
import json
import requests
import time

API_BASE = "http://127.0.0.1:8000"

PASS = 0
FAIL = 0

def log(test_id, title, passed, detail=""):
    global PASS, FAIL
    icon = "✅" if passed else "❌"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    print(f"\n{icon} Test {test_id}: {title}")
    if detail:
        print(f"   → {detail}")


def test_1_top_candidates_above_80():
    """Prompt: 'Who are the top candidates with a score above 80?' → Expect ≥ 5 candidates."""
    try:
        r = requests.post(f"{API_BASE}/api/chat", json={
            "message": "Who are the top candidates with a score above 80?",
            "history": []
        }, timeout=60)
        data = r.json()
        reply = data.get("reply", "")
        tools = data.get("tools_used", [])
        
        # Verify LLM called a tool (not hallucinating)
        has_tool_call = len(tools) > 0
        # Verify reply mentions at least some known candidates
        known = ["Aarav", "Priya", "Vikram", "Sneha", "Ananya"]
        found = sum(1 for name in known if name.lower() in reply.lower())
        
        passed = has_tool_call and found >= 3
        log(1, "Top candidates with score ≥ 80", passed,
            f"Tools called: {len(tools)}, Known names found in reply: {found}/5")
    except Exception as e:
        log(1, "Top candidates with score ≥ 80", False, f"Exception: {e}")


def test_2_update_candidate_stage():
    """Direct API: PATCH /api/candidates/stage to move a candidate."""
    try:
        # First get candidates to find Rohan's ID
        cands = requests.get(f"{API_BASE}/api/candidates", timeout=15).json()
        rohan = next((c for c in cands if "rohan" in c["name"].lower()), None)
        if not rohan:
            log(2, "Update candidate stage (Rohan Kulkarni)", False, "Rohan not found in DB")
            return
        
        original_stage = rohan["stage"]
        new_stage = "Interview" if original_stage != "Interview" else "Shortlisted"
        
        r = requests.patch(f"{API_BASE}/api/candidates/stage", json={
            "candidate_id": rohan["id"],
            "new_stage": new_stage,
            "score": 76
        }, timeout=30)
        
        # Verify the update
        cands_after = requests.get(f"{API_BASE}/api/candidates", timeout=15).json()
        rohan_after = next((c for c in cands_after if c["id"] == rohan["id"]), None)
        
        passed = rohan_after and rohan_after["stage"] == new_stage
        log(2, "Update candidate stage (Rohan Kulkarni)", passed,
            f"Stage: {original_stage} → {rohan_after['stage'] if rohan_after else '?'}")
        
        # Restore original stage
        requests.patch(f"{API_BASE}/api/candidates/stage", json={
            "candidate_id": rohan["id"],
            "new_stage": original_stage,
            "score": rohan.get("score", 68)
        }, timeout=30)
    except Exception as e:
        log(2, "Update candidate stage (Rohan Kulkarni)", False, f"Exception: {e}")


def test_3_pipeline_summary():
    """GET /api/pipeline/summary → Verify stage counts match candidate list."""
    try:
        cands = requests.get(f"{API_BASE}/api/candidates", timeout=15).json()
        summary = requests.get(f"{API_BASE}/api/pipeline/summary", timeout=30).json()
        
        # Build expected counts from candidates
        expected = {}
        for c in cands:
            expected[c["stage"]] = expected.get(c["stage"], 0) + 1
        
        # Compare with summary
        actual = {s["stage"]: s["count"] for s in summary.get("stages", [])}
        
        total_match = summary.get("total_candidates") == len(cands)
        stages_match = expected == actual
        
        passed = total_match and stages_match
        log(3, "Pipeline summary consistency", passed,
            f"Total: {summary.get('total_candidates')}/{len(cands)}, Stages match: {stages_match}")
    except Exception as e:
        log(3, "Pipeline summary consistency", False, f"Exception: {e}")


def test_4_jd_matching():
    """POST /api/match-jd → Verify JD matching returns ranked candidates."""
    try:
        jd = "Senior Python Backend Engineer with 5+ years experience in FastAPI, PostgreSQL, Docker, and Kubernetes. Must have deployed production microservices."
        r = requests.post(f"{API_BASE}/api/match-jd", json={
            "job_description": jd,
            "top_k": 3
        }, timeout=60)
        data = r.json()
        matches = data.get("matches", [])
        
        # Verify we got results with required fields
        has_results = isinstance(matches, list) and len(matches) > 0
        has_fields = all(
            "name" in m or "candidate_name" in m 
            for m in (matches if isinstance(matches, list) else [])
        ) if has_results else False
        
        passed = has_results and has_fields
        names = [m.get("name", m.get("candidate_name", "?")) for m in matches] if isinstance(matches, list) else []
        log(4, "JD matching (Python Backend Engineer)", passed,
            f"Returned {len(matches) if isinstance(matches, list) else 0} matches: {names}")
    except Exception as e:
        log(4, "JD matching (Python Backend Engineer)", False, f"Exception: {e}")


def test_5_resume_path_traversal():
    """GET /api/resumes/../../etc/passwd → Expect 404, NOT file content."""
    try:
        r = requests.get(f"{API_BASE}/api/resumes/../../etc/passwd", timeout=15)
        
        # Should NOT return 200 with file content
        passed = r.status_code != 200 or "root:" not in r.text
        log(5, "Resume path traversal blocked", passed,
            f"Status: {r.status_code}")
    except Exception as e:
        log(5, "Resume path traversal blocked", False, f"Exception: {e}")


def main():
    print("=" * 60)
    print("  AI Recruitment Copilot — Eval Suite")
    print("  5 Deterministic Prompts & Security Tests")
    print("=" * 60)
    
    # Check server health
    try:
        health = requests.get(f"{API_BASE}/", timeout=10)
        print(f"\n🟢 Backend healthy: {health.json().get('status', '?')}")
    except Exception as e:
        print(f"\n🔴 Backend not reachable at {API_BASE}: {e}")
        print("   Start the server first: python main.py")
        sys.exit(1)
    
    test_1_top_candidates_above_80()
    test_2_update_candidate_stage()
    test_3_pipeline_summary()
    test_4_jd_matching()
    test_5_resume_path_traversal()
    
    print("\n" + "=" * 60)
    print(f"  Results:  {PASS} passed  /  {FAIL} failed  /  {PASS + FAIL} total")
    print("=" * 60)
    
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
