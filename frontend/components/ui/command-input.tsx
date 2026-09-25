"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowRight, Search, Activity, CornerDownLeft, Sparkles } from "lucide-react";
import { BorderBeam } from "./border-beam";
import { IncidentMetadata } from "@/app/types";

interface CommandInputProps {
  incidents: IncidentMetadata[];
  selectedIncidentId: string;
  onSelectAndDiagnose: (incidentId: string) => void;
  isLoading?: boolean;
}

export function CommandInput({
  incidents,
  selectedIncidentId,
  onSelectAndDiagnose,
  isLoading = false,
}: CommandInputProps) {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = incidents.filter(
    (inc) =>
      query === "" ||
      inc.incident_id.toLowerCase().includes(query.toLowerCase()) ||
      inc.name.toLowerCase().includes(query.toLowerCase()) ||
      inc.affected_service.toLowerCase().includes(query.toLowerCase())
  );

  const handleSubmit = (incId?: string) => {
    const targetId = incId || filtered[0]?.incident_id || selectedIncidentId;
    if (targetId) {
      onSelectAndDiagnose(targetId);
      setIsOpen(false);
    }
  };

  return (
    <div ref={containerRef} style={{ position: "relative", width: "100%", maxWidth: "680px" }}>
      {/* Outer Shell with BorderBeam */}
      <div
        style={{
          position: "relative",
          backgroundColor: isFocused ? "#0d1017" : "rgba(13, 16, 23, 0.75)",
          border: isFocused ? "1px solid rgba(255, 255, 255, 0.18)" : "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "8px",
          boxShadow: isFocused
            ? "0 12px 32px -8px rgba(0, 0, 0, 0.6), 0 0 1px 1px rgba(59, 130, 246, 0.2)"
            : "0 4px 20px -4px rgba(0, 0, 0, 0.4)",
          transition: "all 0.2s ease",
          padding: "10px 14px",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        <BorderBeam
          isActive={isFocused || isLoading}
          duration={isLoading ? 3 : 8}
          borderWidth={1.5}
          colorFrom="#3b82f6"
          colorTo="#10b981"
        />

        {/* Input Row */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Search size={15} style={{ color: isFocused ? "#3b82f6" : "#71717a", flexShrink: 0, transition: "color 0.15s ease" }} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Investigate an incident... (e.g. INC-001, checkout-api, database)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => {
              setIsFocused(true);
              setIsOpen(true);
            }}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleSubmit();
              }
            }}
            style={{
              flex: 1,
              background: "none",
              border: "none",
              outline: "none",
              color: "#ffffff",
              fontSize: "0.875rem",
              fontFamily: "var(--font-sans)",
            }}
          />

          <button
            type="button"
            onClick={() => handleSubmit()}
            disabled={isLoading}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "5px 10px",
              backgroundColor: isFocused ? "#2563eb" : "rgba(255, 255, 255, 0.08)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: "4px",
              color: "#ffffff",
              fontSize: "0.75rem",
              fontWeight: 500,
              fontFamily: "var(--font-mono)",
              cursor: isLoading ? "not-allowed" : "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              if (!isLoading) e.currentTarget.style.backgroundColor = "#3b82f6";
            }}
            onMouseLeave={(e) => {
              if (!isLoading) e.currentTarget.style.backgroundColor = isFocused ? "#2563eb" : "rgba(255, 255, 255, 0.08)";
            }}
          >
            <span>{isLoading ? "Analyzing..." : "Investigate"}</span>
            <CornerDownLeft size={11} style={{ opacity: 0.75 }} />
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", overflowX: "auto", paddingBottom: "2px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "#71717a", textTransform: "uppercase", letterSpacing: "0.05em", flexShrink: 0 }}>
            Scenarios:
          </span>
          {incidents.slice(0, 4).map((inc) => (
            <button
              key={inc.incident_id}
              type="button"
              onClick={() => handleSubmit(inc.incident_id)}
              style={{
                background: "none",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "3px",
                padding: "2px 7px",
                fontFamily: "var(--font-mono)",
                fontSize: "0.6875rem",
                color: inc.incident_id === selectedIncidentId ? "#93c5fd" : "#889096",
                backgroundColor: inc.incident_id === selectedIncidentId ? "rgba(37, 99, 235, 0.12)" : "rgba(255, 255, 255, 0.02)",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#ffffff";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = inc.incident_id === selectedIncidentId ? "#93c5fd" : "#889096";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              }}
            >
              {inc.incident_id}
            </button>
          ))}
        </div>
      </div>

      {/* Dropdown Suggestions */}
      {isOpen && query.trim() !== "" && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            right: 0,
            zIndex: 60,
            backgroundColor: "#0d1017",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            borderRadius: "6px",
            boxShadow: "0 16px 36px -6px rgba(0, 0, 0, 0.7)",
            maxHeight: "260px",
            overflowY: "auto",
            padding: "4px",
          }}
        >
          {filtered.length === 0 ? (
            <div style={{ padding: "12px", textAlign: "center", color: "#71717a", fontSize: "0.75rem" }}>
              No incidents match &ldquo;{query}&rdquo;
            </div>
          ) : (
            filtered.slice(0, 6).map((inc) => (
              <div
                key={inc.incident_id}
                onClick={() => handleSubmit(inc.incident_id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 10px",
                  borderRadius: "4px",
                  cursor: "pointer",
                  transition: "background-color 0.1s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", fontWeight: 600, color: "#93c5fd" }}>
                    {inc.incident_id}
                  </span>
                  <span style={{ fontSize: "0.8125rem", color: "#f4f4f6" }}>{inc.name}</span>
                </div>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "#71717a" }}>
                  {inc.affected_service}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
