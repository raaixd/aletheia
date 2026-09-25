"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Search, Activity, Sparkles, CheckCircle2 } from "lucide-react";
import { IncidentMetadata } from "@/app/types";

interface IncidentCommandInputProps {
  incidents: IncidentMetadata[];
  selectedIncidentId: string;
  onSelectAndDiagnose: (incidentId: string) => void;
  isLoading?: boolean;
}

export function AnimatedAIChat({
  incidents,
  selectedIncidentId,
  onSelectAndDiagnose,
  isLoading = false,
}: IncidentCommandInputProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
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

  const currentInc = incidents.find((i) => i.incident_id === selectedIncidentId) || incidents[0];

  const handleSelect = (incId: string) => {
    setQuery("");
    setIsOpen(false);
    onSelectAndDiagnose(incId);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (filtered.length > 0) {
      handleSelect(filtered[0].incident_id);
    } else {
      handleSelect(selectedIncidentId);
    }
  };

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        width: "100%",
        maxWidth: "600px",
        margin: "0 auto",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          backgroundColor: "rgba(14, 18, 27, 0.85)",
          backdropFilter: "blur(16px)",
          border: isOpen
            ? "1px solid var(--crimson-blue-accent)"
            : "1px solid var(--border-subtle)",
          borderRadius: "24px",
          padding: "4px 8px 4px 16px",
          boxShadow: isOpen
            ? "0 4px 20px rgba(37, 99, 235, 0.15), 0 0 0 1px var(--crimson-blue-accent)"
            : "0 2px 10px rgba(0, 0, 0, 0.4)",
          transition: "all 0.2s ease",
        }}
      >
        <Search
          size={16}
          style={{
            color: isOpen ? "var(--crimson-blue-accent)" : "var(--text-muted)",
            marginRight: "10px",
            flexShrink: 0,
            transition: "color 0.2s ease",
          }}
        />

        <input
          ref={inputRef}
          type="text"
          value={query}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          placeholder={
            currentInc
              ? `Investigate ${currentInc.incident_id}: ${currentInc.name.slice(0, 36)}...`
              : "Search or enter incident ID (e.g. INC-001)..."
          }
          style={{
            flex: 1,
            backgroundColor: "transparent",
            border: "none",
            outline: "none",
            color: "var(--text-primary)",
            fontSize: "0.875rem",
            fontFamily: "var(--font-sans)",
            padding: "8px 0",
          }}
        />

        <button
          type="submit"
          disabled={isLoading}
          aria-label="Run investigation"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            backgroundColor: "var(--crimson-blue-accent)",
            border: "none",
            color: "#ffffff",
            cursor: isLoading ? "wait" : "pointer",
            flexShrink: 0,
            transition: "all 0.15s ease",
          }}
        >
          {isLoading ? (
            <Activity size={14} className="animate-spin" />
          ) : (
            <ArrowRight size={14} />
          )}
        </button>
      </form>

      {/* Suggestion Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            style={{
              position: "absolute",
              top: "calc(100% + 8px)",
              left: 0,
              right: 0,
              backgroundColor: "rgba(11, 15, 23, 0.96)",
              backdropFilter: "blur(20px)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "12px",
              boxShadow: "0 16px 36px rgba(0, 0, 0, 0.8)",
              overflow: "hidden",
              zIndex: 60,
              maxHeight: "280px",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                padding: "8px 14px",
                fontFamily: "var(--font-mono)",
                fontSize: "0.6875rem",
                color: "var(--text-muted)",
                letterSpacing: "0.06em",
                borderBottom: "1px solid var(--border-hairline)",
                textTransform: "uppercase",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <Sparkles size={11} style={{ color: "var(--crimson-blue-accent)" }} />
              Reproducible Benchmark Incidents ({filtered.length})
            </div>

            {filtered.slice(0, 6).map((inc) => (
              <div
                key={inc.incident_id}
                onClick={() => handleSelect(inc.incident_id)}
                style={{
                  padding: "10px 14px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  cursor: "pointer",
                  borderBottom: "1px solid var(--border-hairline)",
                  transition: "background-color 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "var(--crimson-blue-subtle)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                <div style={{ display: "flex", alignItems: "baseline", gap: "10px" }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color:
                        inc.incident_id === selectedIncidentId
                          ? "var(--crimson-blue-accent)"
                          : "var(--text-secondary)",
                    }}
                  >
                    {inc.incident_id}
                  </span>
                  <span style={{ fontSize: "0.8125rem", color: "#f8fafc" }}>
                    {inc.name}
                  </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span
                    style={{
                      fontSize: "0.6875rem",
                      color: "var(--text-muted)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {inc.affected_service}
                  </span>
                  {inc.incident_id === selectedIncidentId && (
                    <CheckCircle2 size={13} style={{ color: "var(--verified-emerald)" }} />
                  )}
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
