"use client";

import React from "react";
import { TimelineEvent } from "@/app/types";

interface TimelineViewProps {
  events: TimelineEvent[];
  onSelectEvidence?: (evidenceId: string) => void;
  selectedEvidenceId?: string | null;
}

export function TimelineView({
  events,
  onSelectEvidence,
  selectedEvidenceId,
}: TimelineViewProps) {
  if (!events || events.length === 0) {
    return (
      <div style={{ padding: "24px 0", color: "#71717a", fontSize: "0.8125rem" }}>
        No timeline events reconstructed for this incident.
      </div>
    );
  }

  // Get color and badge label for event type
  const getTypeMeta = (type: string) => {
    switch (type.toLowerCase()) {
      case "deployment":
        return { color: "#8fa58a", dotBg: "#7d9478", label: "DEPLOYMENT" };
      case "commit":
        return { color: "#b7b2a9", dotBg: "#858178", label: "COMMIT" };
      case "span":
        return { color: "#c4685d", dotBg: "#ba5c51", label: "TRACE SPAN" };
      case "metric":
        return { color: "#c29b38", dotBg: "#bfa15f", label: "METRIC SPIKE" };
      default:
        return { color: "#858178", dotBg: "#57544d", label: "SYSTEM EVENT" };
    }
  };

  return (
    <div style={{ position: "relative", paddingLeft: "16px", margin: "16px 0 28px 0" }}>
      {/* Continuous Vertical Guide Line */}
      <div
        style={{
          position: "absolute",
          left: "148px",
          top: "14px",
          bottom: "14px",
          width: "1px",
          backgroundColor: "rgba(231, 227, 220, 0.08)",
        }}
      />

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {events.map((evt, idx) => {
          const meta = getTypeMeta(evt.type);
          const hasEvidence = evt.evidence_ids && evt.evidence_ids.length > 0;
          const isEvidenceSelected =
            hasEvidence && evt.evidence_ids.some((id) => id === selectedEvidenceId);

          return (
            <div
              key={evt.event_id || idx}
              style={{
                display: "grid",
                gridTemplateColumns: "120px 24px 1fr",
                alignItems: "flex-start",
                gap: "12px",
                position: "relative",
              }}
            >
              {/* Left Column: Timestamp */}
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.75rem",
                  color: "#858178",
                  textAlign: "right",
                  paddingTop: "2px",
                }}
              >
                {evt.timestamp}
              </div>

              {/* Middle: Dot on vertical guide line */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  paddingTop: "6px",
                  zIndex: 2,
                }}
              >
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: meta.color,
                    border: "2px solid #0f0f0e",
                  }}
                />
              </div>

              {/* Right Column: Event Content */}
              <div
                style={{
                  paddingBottom: "8px",
                  transition: "background-color 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "3px" }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.625rem",
                      fontWeight: 600,
                      color: meta.color,
                      backgroundColor: `${meta.color}15`,
                      border: `1px solid ${meta.color}33`,
                      padding: "1px 6px",
                      borderRadius: "3px",
                      letterSpacing: "0.04em",
                    }}
                  >
                    {meta.label}
                  </span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "#858178" }}>
                    {evt.service}
                  </span>
                </div>

                <div
                  style={{
                    fontSize: "0.875rem",
                    color: isEvidenceSelected ? "#e7e3dc" : "#d6d1c7",
                    fontWeight: 500,
                    lineHeight: 1.5,
                    marginBottom: "4px",
                  }}
                >
                  {evt.summary}
                </div>

                {/* Cited Evidence Badges */}
                {hasEvidence && (
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
                    {evt.evidence_ids.map((evId) => (
                      <button
                        key={evId}
                        type="button"
                        onClick={() => onSelectEvidence?.(evId)}
                        className="ev-ref"
                        style={{
                          borderColor: selectedEvidenceId === evId ? "rgba(143, 165, 138, 0.45)" : undefined,
                          backgroundColor: selectedEvidenceId === evId ? "rgba(143, 165, 138, 0.12)" : undefined,
                          color: selectedEvidenceId === evId ? "#e7e3dc" : undefined,
                        }}
                      >
                        {evId}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
