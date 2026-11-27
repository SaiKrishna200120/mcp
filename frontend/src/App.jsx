/**
 * RecruitAI Copilot - Main Application Root
 * =========================================
 * Provides top-level tab navigation across three core recruiter workflows:
 *   1. AI Copilot Chat: Multi-turn ReAct agent with MCP tool execution trace.
 *   2. JD Talent Matcher: Semantic pgvector search matching JDs against CV embeddings.
 *   3. ATS Candidate Pipeline: Live candidate tracker table with stage progression.
 */

import { useState } from "react";
import Navbar from "./components/Navbar";
import ChatTab from "./components/ChatTab";
import JDMatcherTab from "./components/JDMatcherTab";
import PipelineTab from "./components/PipelineTab";
import "./index.css";

export default function App() {
  // Active navigation tab state ('chat' | 'matcher' | 'pipeline')
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#0b0f19" }}>
      {/* Global Application Header & Telemetry */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Primary Tab Viewport */}
      <main>
        {activeTab === "chat" && <ChatTab />}
        {activeTab === "matcher" && <JDMatcherTab />}
        {activeTab === "pipeline" && <PipelineTab />}
      </main>
    </div>
  );
}
