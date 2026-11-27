/**
 * ATS Candidate Pipeline Component
 * =================================
 * Visualizes the complete candidate hiring funnel.
 * Features:
 *   - 5 interactive stage aggregation cards (Applied, Shortlisted, Interview, Offer, Rejected).
 *   - Average screening score per stage.
 *   - Sortable candidate table (by name, role, experience, score, stage).
 *   - Inline stage dropdown selector to move candidates across stages in real-time.
 *   - One-click modal resume inspection.
 */

import React, { useState, useEffect } from "react";
import {
  Users, TrendingUp, Eye, ChevronDown, ArrowUpDown,
  UserPlus, FileCheck, MessageSquare, Award, XCircle,
  RefreshCw, Loader2
} from "lucide-react";
import { fetchCandidates, fetchPipelineSummary, updateCandidateStage, fetchCandidateResume } from "../api";
import ResumeModal from "./ResumeModal";

const STAGES = ["Applied", "Shortlisted", "Interview", "Offer", "Rejected"];

const STAGE_CONFIG = {
  Applied:     { color: "#6366f1", bg: "rgba(99,102,241,0.12)",  icon: UserPlus },
  Shortlisted: { color: "#f59e0b", bg: "rgba(245,158,11,0.12)", icon: FileCheck },
  Interview:   { color: "#3b82f6", bg: "rgba(59,130,246,0.12)",  icon: MessageSquare },
  Offer:       { color: "#10b981", bg: "rgba(16,185,129,0.12)",  icon: Award },
  Rejected:    { color: "#ef4444", bg: "rgba(239,68,68,0.12)",   icon: XCircle },
};

export default function PipelineTab() {
  const [candidates, setCandidates] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterStage, setFilterStage] = useState("All");
  const [sortField, setSortField] = useState("score");
  const [sortDir, setSortDir] = useState("desc");
  const [resumeData, setResumeData] = useState(null);
  const [updating, setUpdating] = useState(null); // Candidate ID currently being updated

  const loadData = async () => {
    setLoading(true);
    try {
      const [cands, pipe] = await Promise.all([
        fetchCandidates(),
        fetchPipelineSummary()
      ]);
      setCandidates(cands);
      setSummary(pipe);
    } catch (err) {
      console.error("Failed to load pipeline data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleStageChange = async (candidateId, newStage) => {
    setUpdating(candidateId);
    try {
      await updateCandidateStage(candidateId, newStage);
      await loadData();
    } catch (err) {
      alert("Failed to update stage: " + err.message);
    } finally {
      setUpdating(null);
    }
  };

  const openResume = async (name) => {
    try {
      const data = await fetchCandidateResume(name);
      setResumeData(data);
    } catch {
      alert("Could not load resume for " + name);
    }
  };

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  // Filter & sort candidates
  const displayed = candidates
    .filter(c => filterStage === "All" || c.stage === filterStage)
    .sort((a, b) => {
      let aVal = a[sortField], bVal = b[sortField];
      if (typeof aVal === "string") aVal = aVal.toLowerCase();
      if (typeof bVal === "string") bVal = bVal.toLowerCase();
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });

  const getStageCount = (stage) => {
    if (!summary?.stages) return 0;
    const s = summary.stages.find(x => x.stage === stage);
    return s ? s.count : 0;
  };

  const getStageAvg = (stage) => {
    if (!summary?.stages) return "–";
    const s = summary.stages.find(x => x.stage === stage);
    return s?.avg_score != null ? s.avg_score : "–";
  };

  if (loading) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "calc(100vh - 80px)",
        gap: "10px",
        color: "#9ca3af",
        fontSize: "15px"
      }}>
        <Loader2 size={20} style={{ animation: "spin 1s linear infinite" }} />
        Loading pipeline data from Neon Cloud...
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: "1200px",
      margin: "0 auto",
      padding: "24px 20px",
      display: "flex",
      flexDirection: "column",
      gap: "24px"
    }}>
      {/* Stage Summary Cards */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))",
        gap: "14px"
      }}>
        {STAGES.map(stage => {
          const cfg = STAGE_CONFIG[stage];
          const Icon = cfg.icon;
          return (
            <div
              key={stage}
              onClick={() => setFilterStage(filterStage === stage ? "All" : stage)}
              style={{
                backgroundColor: filterStage === stage ? cfg.bg : "#111827",
                border: `1px solid ${filterStage === stage ? cfg.color : "#1f2937"}`,
                borderRadius: "12px",
                padding: "16px",
                cursor: "pointer",
                transition: "all 0.2s"
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  backgroundColor: cfg.bg,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  <Icon size={16} color={cfg.color} />
                </div>
                <span style={{ fontSize: "24px", fontWeight: 800, color: cfg.color }}>
                  {getStageCount(stage)}
                </span>
              </div>
              <div style={{ marginTop: "8px", fontSize: "13px", fontWeight: 600, color: "#e5e7eb" }}>
                {stage}
              </div>
              <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>
                Avg score: {getStageAvg(stage)}
              </div>
            </div>
          );
        })}
      </div>

      {/* Controls Bar */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Users size={18} color="#818cf8" />
          <span style={{ fontSize: "15px", fontWeight: 600, color: "#e5e7eb" }}>
            {displayed.length} Candidate{displayed.length !== 1 ? "s" : ""}
            {filterStage !== "All" && ` in ${filterStage}`}
          </span>
          {filterStage !== "All" && (
            <button
              onClick={() => setFilterStage("All")}
              style={{
                padding: "3px 10px",
                borderRadius: "12px",
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                color: "#9ca3af",
                fontSize: "11px"
              }}
            >
              Show All
            </button>
          )}
        </div>
        <button
          onClick={loadData}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 14px",
            borderRadius: "8px",
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            color: "#9ca3af",
            fontSize: "12px",
            fontWeight: 500
          }}
        >
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Candidates Table */}
      <div style={{
        backgroundColor: "#111827",
        border: "1px solid #1f2937",
        borderRadius: "14px",
        overflow: "hidden"
      }}>
        <table style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "13px"
        }}>
          <thead>
            <tr style={{ backgroundColor: "#1f2937" }}>
              {[
                { key: "name", label: "Candidate" },
                { key: "role", label: "Role" },
                { key: "experience_years", label: "Experience" },
                { key: "score", label: "Score" },
                { key: "stage", label: "Stage" },
                { key: "actions", label: "Actions" }
              ].map(col => (
                <th
                  key={col.key}
                  onClick={() => col.key !== "actions" && toggleSort(col.key)}
                  style={{
                    padding: "12px 16px",
                    textAlign: "left",
                    color: "#9ca3af",
                    fontWeight: 600,
                    fontSize: "12px",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    cursor: col.key !== "actions" ? "pointer" : "default",
                    userSelect: "none",
                    whiteSpace: "nowrap"
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    {col.label}
                    {col.key !== "actions" && (
                      <ArrowUpDown size={12} color={sortField === col.key ? "#818cf8" : "#4b5563"} />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayed.map((c) => {
              const cfg = STAGE_CONFIG[c.stage] || STAGE_CONFIG.Applied;
              return (
                <tr
                  key={c.id}
                  style={{
                    borderBottom: "1px solid #1f2937",
                    transition: "background-color 0.15s"
                  }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = "#1e293b"}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = "transparent"}
                >
                  {/* Name + Email */}
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ fontWeight: 600, color: "#f9fafb" }}>{c.name}</div>
                    <div style={{ fontSize: "11px", color: "#6b7280" }}>{c.email}</div>
                  </td>

                  {/* Role */}
                  <td style={{ padding: "14px 16px", color: "#cbd5e1" }}>
                    {c.role}
                  </td>

                  {/* Experience */}
                  <td style={{ padding: "14px 16px", color: "#9ca3af" }}>
                    {c.experience_years} yrs
                  </td>

                  {/* Score */}
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      padding: "3px 10px",
                      borderRadius: "12px",
                      backgroundColor: c.score >= 80 ? "rgba(16,185,129,0.12)" :
                                       c.score >= 60 ? "rgba(245,158,11,0.12)" :
                                       "rgba(239,68,68,0.12)",
                      color: c.score >= 80 ? "#10b981" :
                             c.score >= 60 ? "#f59e0b" :
                             "#ef4444",
                      fontWeight: 700,
                      fontSize: "13px"
                    }}>
                      <TrendingUp size={12} /> {c.score}
                    </div>
                  </td>

                  {/* Stage Dropdown */}
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ position: "relative", display: "inline-block" }}>
                      <select
                        value={c.stage}
                        onChange={(e) => handleStageChange(c.id, e.target.value)}
                        disabled={updating === c.id}
                        style={{
                          appearance: "none",
                          backgroundColor: cfg.bg,
                          border: `1px solid ${cfg.color}40`,
                          borderRadius: "8px",
                          padding: "5px 28px 5px 10px",
                          color: cfg.color,
                          fontWeight: 600,
                          fontSize: "12px",
                          cursor: "pointer",
                          outline: "none"
                        }}
                      >
                        {STAGES.map(s => (
                          <option key={s} value={s} style={{ backgroundColor: "#111827", color: "#e5e7eb" }}>
                            {s}
                          </option>
                        ))}
                      </select>
                      <ChevronDown
                        size={12}
                        color={cfg.color}
                        style={{ position: "absolute", right: "8px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}
                      />
                    </div>
                  </td>

                  {/* Actions */}
                  <td style={{ padding: "14px 16px" }}>
                    <button
                      onClick={() => openResume(c.name)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "5px",
                        padding: "5px 12px",
                        borderRadius: "6px",
                        backgroundColor: "#1e293b",
                        border: "1px solid #334155",
                        color: "#818cf8",
                        fontSize: "11px",
                        fontWeight: 600
                      }}
                    >
                      <Eye size={12} /> Resume
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {displayed.length === 0 && (
          <div style={{
            padding: "40px",
            textAlign: "center",
            color: "#6b7280",
            fontSize: "14px"
          }}>
            No candidates found{filterStage !== "All" ? ` in ${filterStage} stage` : ""}.
          </div>
        )}
      </div>

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
