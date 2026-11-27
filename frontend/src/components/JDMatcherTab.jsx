/**
 * JD Talent Matcher Component
 * ============================
 * Enables recruiters to paste a Job Description (JD) and immediately retrieve
 * ranked candidates scored by vector cosine similarity against chunked CV embeddings.
 * Features:
 *   - Configurable top results selector (3, 5, 6).
 *   - Relevance percentage ring badge with color indicators (Green >=80%, Yellow >=60%, Red <60%).
 *   - Extracted CV evidence quotes showing exactly why the candidate matched the JD.
 *   - Modal resume inspection button.
 */

import React, { useState } from "react";
import { Search, FileText, Star, Briefcase, Clock, IndianRupee, Award, Eye, Loader2 } from "lucide-react";
import { matchJobDescription, fetchCandidateResume } from "../api";
import ResumeModal from "./ResumeModal";

export default function JDMatcherTab() {
  const [jd, setJd] = useState("");
  const [topK, setTopK] = useState(5);
  const [matches, setMatches] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resumeData, setResumeData] = useState(null);

  const handleMatch = async () => {
    if (!jd.trim()) return;
    setLoading(true);
    setError("");
    setMatches(null);
    try {
      const result = await matchJobDescription(jd, topK);
      setMatches(result.matches);
    } catch (err) {
      setError("Failed to match candidates. Ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const openResume = async (candidateName) => {
    try {
      const data = await fetchCandidateResume(candidateName);
      setResumeData(data);
    } catch {
      alert("Could not load resume for " + candidateName);
    }
  };

  const matchColor = (pct) => {
    if (pct >= 80) return "#10b981";
    if (pct >= 60) return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div style={{
      maxWidth: "1100px",
      margin: "0 auto",
      padding: "24px 20px",
      display: "flex",
      flexDirection: "column",
      gap: "24px"
    }}>
      {/* JD Input Section */}
      <div style={{
        backgroundColor: "#111827",
        border: "1px solid #1f2937",
        borderRadius: "14px",
        padding: "24px",
        boxShadow: "0 4px 14px rgba(0,0,0,0.25)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
          <div style={{
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            background: "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}>
            <Search size={18} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f9fafb" }}>
              JD Talent Matcher
            </h2>
            <p style={{ fontSize: "13px", color: "#9ca3af" }}>
              Paste a Job Description — the system uses pgvector cosine similarity to find the best candidates from the resume vault
            </p>
          </div>
        </div>

        <textarea
          value={jd}
          onChange={(e) => setJd(e.target.value)}
          placeholder={"Paste the full Job Description here...\n\nExample: We are looking for a Senior Python Backend Engineer with 5+ years experience in FastAPI, PostgreSQL, Docker, and Kubernetes. Must have led teams of 3+ engineers and deployed microservices at scale."}
          rows={6}
          style={{
            width: "100%",
            backgroundColor: "#0b0f19",
            border: "1px solid #243048",
            borderRadius: "10px",
            padding: "14px",
            color: "#f8fafc",
            fontSize: "14px",
            lineHeight: "1.6",
            resize: "vertical",
            outline: "none"
          }}
        />

        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: "14px",
          flexWrap: "wrap",
          gap: "12px"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <label style={{ fontSize: "13px", color: "#9ca3af" }}>Top results:</label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "6px",
                padding: "4px 10px",
                color: "#e5e7eb",
                fontSize: "13px"
              }}
            >
              {[3, 5, 6].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>

          <button
            onClick={handleMatch}
            disabled={loading || !jd.trim()}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 24px",
              borderRadius: "10px",
              backgroundColor: jd.trim() ? "#4f46e5" : "#334155",
              color: "#ffffff",
              fontWeight: 600,
              fontSize: "14px",
              transition: "all 0.2s"
            }}
          >
            {loading ? (
              <><Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> Matching...</>
            ) : (
              <><Search size={16} /> Find Best Candidates</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: "12px 16px",
          borderRadius: "10px",
          backgroundColor: "rgba(239,68,68,0.1)",
          border: "1px solid rgba(239,68,68,0.3)",
          color: "#fca5a5",
          fontSize: "13px"
        }}>
          {error}
        </div>
      )}

      {/* Results Grid */}
      {matches && (
        <div>
          <h3 style={{ fontSize: "15px", fontWeight: 600, color: "#e5e7eb", marginBottom: "14px" }}>
            🎯 Top {Array.isArray(matches) ? matches.length : 0} Matching Candidates
          </h3>

          {Array.isArray(matches) ? (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: "16px"
            }}>
              {matches.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: "#111827",
                    border: "1px solid #1f2937",
                    borderRadius: "14px",
                    padding: "20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "14px",
                    transition: "border-color 0.2s",
                    position: "relative"
                  }}
                >
                  {/* Rank Badge */}
                  <div style={{
                    position: "absolute",
                    top: "-8px",
                    right: "16px",
                    backgroundColor: idx === 0 ? "#4f46e5" : "#374151",
                    padding: "2px 10px",
                    borderRadius: "12px",
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#ffffff"
                  }}>
                    #{idx + 1}
                  </div>

                  {/* Match Percentage Ring */}
                  <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                    <div style={{
                      width: "56px",
                      height: "56px",
                      borderRadius: "50%",
                      border: `3px solid ${matchColor(m.match_percentage || 0)}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0
                    }}>
                      <span style={{
                        fontSize: "16px",
                        fontWeight: 800,
                        color: matchColor(m.match_percentage || 0)
                      }}>
                        {Math.round(m.match_percentage || 0)}%
                      </span>
                    </div>
                    <div>
                      <div style={{ fontSize: "16px", fontWeight: 700, color: "#f9fafb" }}>
                        {m.candidate_name || m.name || "Unknown"}
                      </div>
                      <div style={{ fontSize: "13px", color: "#9ca3af" }}>
                        {m.role || ""}
                      </div>
                    </div>
                  </div>

                  {/* Candidate Details */}
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "8px",
                    fontSize: "12px"
                  }}>
                    {m.experience_years != null && (
                      <div style={{ display: "flex", alignItems: "center", gap: "5px", color: "#9ca3af" }}>
                        <Clock size={12} /> {m.experience_years} yrs exp
                      </div>
                    )}
                    {m.expected_ctc_lpa != null && (
                      <div style={{ display: "flex", alignItems: "center", gap: "5px", color: "#9ca3af" }}>
                        <IndianRupee size={12} /> ₹{m.expected_ctc_lpa} LPA
                      </div>
                    )}
                    {m.screening_score != null && (
                      <div style={{ display: "flex", alignItems: "center", gap: "5px", color: "#9ca3af" }}>
                        <Award size={12} /> Score: {m.screening_score}
                      </div>
                    )}
                    {m.stage && (
                      <div style={{ display: "flex", alignItems: "center", gap: "5px", color: "#9ca3af" }}>
                        <Briefcase size={12} /> {m.stage}
                      </div>
                    )}
                  </div>

                  {/* Resume Proof Quote */}
                  {m.resume_proof && (
                    <div style={{
                      backgroundColor: "rgba(99, 102, 241, 0.06)",
                      border: "1px solid rgba(99, 102, 241, 0.15)",
                      borderRadius: "8px",
                      padding: "10px 12px",
                      fontSize: "12px",
                      color: "#cbd5e1",
                      lineHeight: "1.5",
                      fontStyle: "italic"
                    }}>
                      <span style={{ color: "#818cf8", fontWeight: 600, fontStyle: "normal" }}>CV Evidence: </span>
                      {m.resume_proof.length > 200 ? m.resume_proof.slice(0, 200) + "…" : m.resume_proof}
                    </div>
                  )}

                  {/* View Resume Button */}
                  <button
                    onClick={() => openResume(m.candidate_name || m.name)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "6px",
                      padding: "8px 14px",
                      borderRadius: "8px",
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      color: "#818cf8",
                      fontSize: "12px",
                      fontWeight: 600,
                      transition: "all 0.15s"
                    }}
                  >
                    <Eye size={14} /> View Full Resume
                  </button>
                </div>
              ))}
            </div>
          ) : (
            /* Fallback for text-based response */
            <div style={{
              backgroundColor: "#111827",
              border: "1px solid #1f2937",
              borderRadius: "12px",
              padding: "20px",
              fontSize: "14px",
              color: "#e5e7eb",
              whiteSpace: "pre-wrap",
              lineHeight: "1.6"
            }}>
              {typeof matches === "string" ? matches : JSON.stringify(matches, null, 2)}
            </div>
          )}
        </div>
      )}

      {/* Resume Modal */}
      {resumeData && (
        <ResumeModal resumeData={resumeData} onClose={() => setResumeData(null)} />
      )}

      {/* CSS Animation */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
