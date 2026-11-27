/**
 * Navigation Bar Component
 * ========================
 * Top header displaying project brand, active navigation tabs,
 * and live system telemetry badges (Neon Cloud & Dual MCP status).
 */

import React from "react";
import { Bot, FileSearch, Users, Database, Cpu } from "lucide-react";

export default function Navbar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: "chat", label: "AI Copilot Chat", icon: Bot },
    { id: "matcher", label: "JD Talent Matcher", icon: FileSearch },
    { id: "pipeline", label: "ATS Candidate Pipeline", icon: Users },
  ];

  return (
    <header style={{
      backgroundColor: "#111827",
      borderBottom: "1px solid #1f2937",
      padding: "14px 24px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      flexWrap: "wrap",
      gap: "16px"
    }}>
      {/* Brand & Project Identity */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          width: "40px",
          height: "40px",
          borderRadius: "10px",
          background: "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 4px 12px rgba(99, 102, 241, 0.35)"
        }}>
          <Bot size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: "17px", letterSpacing: "-0.02em", color: "#f9fafb" }}>
            RecruitAI Copilot
          </div>
          <div style={{ fontSize: "12px", color: "#9ca3af", display: "flex", alignItems: "center", gap: "6px" }}>
            <span>Dual MCP</span> • <span>Neon pgvector</span> • <span>Qwen Embeddings</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{
        display: "flex",
        alignItems: "center",
        backgroundColor: "#030712",
        padding: "4px",
        borderRadius: "10px",
        border: "1px solid #1f2937"
      }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                borderRadius: "8px",
                fontSize: "13px",
                fontWeight: 600,
                color: isActive ? "#ffffff" : "#9ca3af",
                backgroundColor: isActive ? "#374151" : "transparent",
                transition: "all 0.2s ease"
              }}
            >
              <Icon size={16} color={isActive ? "#818cf8" : "#9ca3af"} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Architecture System Telemetry Badges */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "4px 10px",
          borderRadius: "20px",
          backgroundColor: "rgba(16, 185, 129, 0.12)",
          border: "1px solid rgba(16, 185, 129, 0.3)",
          color: "#34d399",
          fontSize: "12px",
          fontWeight: 500
        }}>
          <Database size={13} />
          <span>Neon Cloud: Live</span>
        </div>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "4px 10px",
          borderRadius: "20px",
          backgroundColor: "rgba(99, 102, 241, 0.12)",
          border: "1px solid rgba(99, 102, 241, 0.3)",
          color: "#818cf8",
          fontSize: "12px",
          fontWeight: 500
        }}>
          <Cpu size={13} />
          <span>MCP: 2 Servers</span>
        </div>
      </div>
    </header>
  );
}
