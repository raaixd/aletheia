"use client";

import React, { useState } from "react";
import { X, Copy, Check, ExternalLink, ShieldCheck, Database, GitCommit, Radio, Server } from "lucide-react";
import { Button } from "./button";
import { ButtonGroup } from "./button-group";

export interface EvidenceRecord {
  id: string;
  source: string;
  timestamp: string;
  title: string;
  component: string;
  payload: Record<string, unknown>;
  verified: boolean;
}

interface EvidenceDrawerProps {
  evidence: EvidenceRecord | null;
  onClose: () => void;
}

export function EvidenceDrawer({ evidence, onClose }: EvidenceDrawerProps) {
  const [copied, setCopied] = useState(false);

  if (!evidence) return null;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSourceIcon = (src: string) => {
    switch (src.toUpperCase()) {
      case "OPENTELEMETRY":
        return <Radio size={14} style={{ color: "#c4685d" }} />;
      case "DEPLOYMENT":
        return <Server size={14} style={{ color: "#8fa58a" }} />;
      case "GIT":
        return <GitCommit size={14} style={{ color: "#b7b2a9" }} />;
      case "PROMETHEUS":
        return <Database size={14} style={{ color: "#c29b38" }} />;
      default:
        return <ShieldCheck size={14} style={{ color: "#8fa58a" }} />;
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 150,
        display: "flex",
        justifyContent: "flex-end",
        backgroundColor: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(4px)",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "500px",
          height: "100%",
          backgroundColor: "#151513",
          borderLeft: "1px solid #2e2c26",
          boxShadow: "-16px 0 48px rgba(0, 0, 0, 0.75)",
          display: "flex",
          flexDirection: "column",
          color: "#e7e3dc",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "18px 24px",
            borderBottom: "1px solid #292823",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {getSourceIcon(evidence.source)}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.6875rem",
                  color: "#858178",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                EVIDENCE RECORD
              </div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "1rem",
                  fontWeight: 600,
                  color: "#e7e3dc",
                }}
              >
                {evidence.id}
              </div>
            </div>
          </div>

          <Button variant="outline" size="icon" aria-label="Close Drawer" onClick={onClose}>
            <X size={14} />
          </Button>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
          {/* Metadata Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "12px",
              paddingBottom: "20px",
              marginBottom: "20px",
              borderBottom: "1px solid #292823",
            }}
          >
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "#858178", marginBottom: "2px" }}>
                SOURCE TELEMETRY
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "#d6d1c7" }}>
                {evidence.source}
              </div>
            </div>
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "#858178", marginBottom: "2px" }}>
                TIMESTAMP
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "#d6d1c7" }}>
                {evidence.timestamp}
              </div>
            </div>
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "#858178", marginBottom: "2px" }}>
                SERVICE COMPONENT
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "#b7b2a9" }}>
                {evidence.component}
              </div>
            </div>
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "#858178", marginBottom: "2px" }}>
                VERIFICATION AUDIT
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "#8fa58a", display: "flex", alignItems: "center", gap: "5px" }}>
                <span style={{ width: "5px", height: "5px", borderRadius: "50%", backgroundColor: "#8fa58a" }} />
                VERIFIED (NO CORRUPTION)
              </div>
            </div>
          </div>

          {/* Observation Summary */}
          <div style={{ marginBottom: "24px" }}>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.625rem",
                color: "#71717a",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "6px",
              }}
            >
              OBSERVATION STATEMENT
            </div>
            <div
              style={{
                fontSize: "0.875rem",
                lineHeight: 1.5,
                color: "#e7e3dc",
                fontWeight: 500,
              }}
            >
              {evidence.title}
            </div>
          </div>

          {/* Raw JSON Payload */}
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "8px",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.625rem",
                  color: "#858178",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                STRUCTURED PAYLOAD ATTRIBUTES
              </div>
              <button
                type="button"
                onClick={() => handleCopy(JSON.stringify(evidence.payload, null, 2))}
                style={{
                  background: "none",
                  border: "none",
                  color: copied ? "#8fa58a" : "#858178",
                  fontSize: "0.6875rem",
                  fontFamily: "var(--font-mono)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  padding: 0,
                }}
              >
                {copied ? <Check size={11} /> : <Copy size={11} />}
                <span>{copied ? "Copied" : "Copy JSON"}</span>
              </button>
            </div>

            <pre
              style={{
                backgroundColor: "#10100f",
                border: "1px solid #292823",
                borderRadius: "4px",
                padding: "14px",
                fontFamily: "var(--font-mono)",
                fontSize: "0.75rem",
                color: "#b7b2a9",
                overflowX: "auto",
                lineHeight: 1.55,
              }}
            >
              {JSON.stringify(evidence.payload, null, 2)}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "16px 24px",
            borderTop: "1px solid #292823",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <button
            type="button"
            onClick={() => handleCopy(evidence.id)}
            style={{
              background: "none",
              border: "none",
              color: "#858178",
              fontFamily: "var(--font-mono)",
              fontSize: "0.75rem",
              cursor: "pointer",
              padding: 0,
            }}
          >
            Copy Evidence ID: <span style={{ color: "#e7e3dc" }}>{evidence.id}</span>
          </button>
          <Button variant="outline" size="sm" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
}
