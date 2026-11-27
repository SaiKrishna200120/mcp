/**
 * Candidate Resume Modal Component
 * =================================
 * Renders a backdrop-blurred modal displaying the complete Markdown resume
 * for a candidate retrieved from the secure resume vault.
 *
 * Props:
 *   - resumeData: Object containing { candidate_name: string, content: string }
 *   - onClose: Callback function triggered when closing the modal
 */

import React from "react";
import { X, FileText } from "lucide-react";

export default function ResumeModal({ resumeData, onClose }) {
  if (!resumeData) return null;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(3, 7, 18, 0.75)",
      backdropFilter: "blur(4px)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 100,
      padding: "20px"
    }}>
      <div style={{
        backgroundColor: "#111827",
        border: "1px solid #1f2937",
        borderRadius: "16px",
        width: "100%",
        maxWidth: "750px",
        maxHeight: "85vh",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
        overflow: "hidden"
      }}>
        {/* Modal Header */}
        <div style={{
          padding: "16px 24px",
          borderBottom: "1px solid #1f2937",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: "#1f2937"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <FileText size={20} color="#818cf8" />
            <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#f9fafb" }}>
              {resumeData.candidate_name}'s Verified Resume
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: "6px",
              borderRadius: "8px",
              color: "#9ca3af",
              backgroundColor: "rgba(255, 255, 255, 0.05)"
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Content */}
        <div style={{
          padding: "24px",
          overflowY: "auto",
          fontSize: "14px",
          color: "#e5e7eb",
          lineHeight: "1.7",
          fontFamily: "inherit",
          whiteSpace: "pre-wrap"
        }}>
          {resumeData.content}
        </div>

        {/* Modal Footer */}
        <div style={{
          padding: "12px 24px",
          borderTop: "1px solid #1f2937",
          display: "flex",
          justifyContent: "flex-end",
          backgroundColor: "#111827"
        }}>
          <button
            onClick={onClose}
            style={{
              padding: "8px 18px",
              borderRadius: "8px",
              backgroundColor: "#374151",
              color: "#f3f4f6",
              fontSize: "13px",
              fontWeight: 600
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
