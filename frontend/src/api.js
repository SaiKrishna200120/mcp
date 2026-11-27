/**
 * RecruitAI Copilot - Frontend API Client
 * =======================================
 * Handles all asynchronous HTTP communication between the React frontend
 * and the FastAPI backend endpoints.
 *
 * Dev Environment:
 *   Requests use relative path `/api/*` which Vite proxies to `http://localhost:8000/api/*`.
 */

const API_BASE = "/api";

/**
 * Fetches all candidates from the ATS database sorted by screening score.
 * @returns {Promise<Array<Object>>} List of candidate objects.
 */
export async function fetchCandidates() {
  const res = await fetch(`${API_BASE}/candidates`);
  if (!res.ok) throw new Error("Failed to fetch candidates from database.");
  return res.json();
}

/**
 * Fetches live hiring pipeline stage metrics, count aggregations, and average scores.
 * Reads directly from the MCP resource on the backend.
 * @returns {Promise<{summary_text: string, total_candidates: number, stages: Array<Object>}>}
 */
export async function fetchPipelineSummary() {
  const res = await fetch(`${API_BASE}/pipeline/summary`);
  if (!res.ok) throw new Error("Failed to fetch pipeline summary.");
  return res.json();
}

/**
 * Sends a chat message to the ReAct agent host.
 * @param {string} message - User recruiter query.
 * @param {Array<{role: string, content: string}>} history - Multi-turn conversation history.
 * @returns {Promise<{reply: string, tools_used: Array<Object>, turns: number}>}
 */
export async function sendChatMessage(message, history = []) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error("Chat request failed.");
  return res.json();
}

/**
 * Submits a Job Description for pgvector semantic candidate matching.
 * @param {string} job_description - Full JD text.
 * @param {number} top_k - Number of top matches to return (default: 3).
 * @returns {Promise<{matches: Array<Object>}>} Ranked candidate matches with similarity percentages.
 */
export async function matchJobDescription(job_description, top_k = 3) {
  const res = await fetch(`${API_BASE}/match-jd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_description, top_k }),
  });
  if (!res.ok) throw new Error("Job description matching failed.");
  return res.json();
}

/**
 * Updates a candidate's ATS stage and optional screening score.
 * @param {number} candidate_id - Candidate primary key.
 * @param {string} new_stage - New stage ('Applied', 'Shortlisted', 'Interview', 'Offer', 'Rejected').
 * @param {number|null} score - Updated screening score (0-100).
 * @param {string|null} notes - Recruiter evaluation notes.
 * @returns {Promise<Object>} Backend confirmation.
 */
export async function updateCandidateStage(candidate_id, new_stage, score = null, notes = null) {
  const res = await fetch(`${API_BASE}/candidates/stage`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate_id, new_stage, score, notes }),
  });
  if (!res.ok) throw new Error("Failed to update candidate stage.");
  return res.json();
}

/**
 * Retrieves the full verified Markdown resume for a given candidate.
 * @param {string} candidateName - Full name of candidate.
 * @returns {Promise<{candidate_name: string, content: string}>}
 */
export async function fetchCandidateResume(candidateName) {
  const res = await fetch(`${API_BASE}/resumes/${encodeURIComponent(candidateName)}`);
  if (!res.ok) throw new Error("Failed to retrieve candidate resume.");
  return res.json();
}
