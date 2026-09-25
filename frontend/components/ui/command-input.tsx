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
          backgroundColor: isFocused ? "#151513" : "rgba(20, 20, 18, 0.85)",
          border: isFocused ? "1px solid #3d3a33" : "1px solid #292823",
          borderRadius: "8px",
          boxShadow: isFocused
            ? "0 12px 32px -8px rgba(0, 0, 0, 0.7), 0 0 1px 1px rgba(143, 165, 138, 0.15)"
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
          colorFrom="#8fa58a"
          colorTo="#b7b2a9"
        />

        {/* Input Row */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Search size={15} style={{ color: isFocused ? "#8fa58a" : "#858178", flexShrink: 0, transition: "color 0.15s ease" }} />
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
              color: "#e7e3dc",
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
              padding: "5px 11px",
              backgroundColor: isFocused ? "#242722" : "rgba(231, 227, 220, 0.06)",
              border: isFocused ? "1px solid rgba(143, 165, 138, 0.35)" : "1px solid #2e2c26",
              borderRadius: "4px",
              color: isFocused ? "#e7e3dc" : "#b7b2a9",
              fontSize: "0.75rem",
              fontWeight: 500,
              fontFamily: "var(--font-mono)",
              cursor: isLoading ? "not-allowed" : "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.backgroundColor = "#2a2e28";
                e.currentTarget.style.color = "#e7e3dc";
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                e.currentTarget.style.backgroundColor = isFocused ? "#242722" : "rgba(231, 227, 220, 0.06)";
                e.currentTarget.style.color = isFocused ? "#e7e3dc" : "#b7b2a9";
              }
            }}
          >
            <span>{isLoading ? "Analyzing..." : "Investigate"}</span>
            <CornerDownLeft size={11} style={{ opacity: 0.75 }} />
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", overflowX: "auto", paddingBottom: "2px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "#858178", textTransform: "uppercase", letterSpacing: "0.05em", flexShrink: 0 }}>
            Scenarios:
          </span>
          {incidents.slice(0, 4).map((inc) => (
            <button
              key={inc.incident_id}
              type="button"
              onClick={() => handleSubmit(inc.incident_id)}
              style={{
                background: "none",
                border: inc.incident_id === selectedIncidentId ? "1px solid rgba(143, 165, 138, 0.35)" : "1px solid #292823",
                borderRadius: "3px",
                padding: "2px 7px",
                fontFamily: "var(--font-mono)",
                fontSize: "0.6875rem",
                color: inc.incident_id === selectedIncidentId ? "#e7e3dc" : "#858178",
                backgroundColor: inc.incident_id === selectedIncidentId ? "rgba(143, 165, 138, 0.12)" : "rgba(231, 227, 220, 0.02)",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#e7e3dc";
                e.currentTarget.style.borderColor = "rgba(231, 227, 220, 0.18)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = inc.incident_id === selectedIncidentId ? "#e7e3dc" : "#858178";
                e.currentTarget.style.borderColor = inc.incident_id === selectedIncidentId ? "rgba(143, 165, 138, 0.35)" : "#292823";
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
            backgroundColor: "#161614",
            border: "1px solid #2e2c26",
            borderRadius: "6px",
            boxShadow: "0 16px 36px -6px rgba(0, 0, 0, 0.75)",
            maxHeight: "260px",
            overflowY: "auto",
            padding: "4px",
          }}
        >
          {filtered.length === 0 ? (
            <div style={{ padding: "12px", textAlign: "center", color: "#858178", fontSize: "0.75rem" }}>
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
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(231, 227, 220, 0.04)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", fontWeight: 500, color: "#e7e3dc" }}>
                    {inc.incident_id}
                  </span>
                  <span style={{ fontSize: "0.8125rem", color: "#b7b2a9" }}>{inc.name}</span>
                </div>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "#858178" }}>
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
