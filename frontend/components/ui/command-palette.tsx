"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Search,
  Activity,
  ArrowRight,
  X,
  Layers,
  BarChart3,
  Server,
  Play,
  Download,
  ShieldCheck,
  Tag,
} from "lucide-react";
import { IncidentMetadata } from "@/app/types";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  incidents: IncidentMetadata[];
  onSelectIncident: (incidentId: string) => void;
  onNavigateTab: (tab: string) => void;
  onRunDiagnosis: (incidentId: string) => void;
  onExportReport: () => void;
}

export function CommandPalette({
  isOpen,
  onClose,
  incidents,
  onSelectIncident,
  onNavigateTab,
  onRunDiagnosis,
  onExportReport,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Global keyboard shortcut: Cmd+K / Ctrl+K & Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Trigger open via parent
        }
      } else if (e.key === "Escape" && isOpen) {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Filter items
  const q = query.trim().toLowerCase();

  const filteredIncidents = incidents.filter(
    (inc) =>
      q === "" ||
      inc.incident_id.toLowerCase().includes(q) ||
      inc.name.toLowerCase().includes(q) ||
      inc.affected_service.toLowerCase().includes(q)
  );

  const navigationItems = [
    { id: "overview", label: "Overview", desc: "Live state, recent incidents, system status", icon: Activity },
    { id: "investigations", label: "Investigations", desc: "Active & completed investigation workspaces", icon: Play },
    { id: "incidents", label: "Incidents Catalog", desc: "Browse all 21 reproducible benchmark scenarios", icon: Tag },
    { id: "evidence", label: "Evidence Explorer", desc: "Causal DAG graph, spans, metrics & commits", icon: Layers },
    { id: "evaluations", label: "Evaluations Lab", desc: "Scientific benchmark & architecture accuracy", icon: BarChart3 },
    { id: "system", label: "System Health", desc: "LLMOps metrics, latency percentiles & traces", icon: Server },
  ].filter((item) => q === "" || item.label.toLowerCase().includes(q) || item.desc.toLowerCase().includes(q));

  const actionItems = [
    {
      id: "run-inc-001",
      label: "Run Diagnosis on INC-001",
      desc: "Trigger full multi-agent investigation pipeline",
      action: () => {
        onSelectIncident("INC-001");
        onRunDiagnosis("INC-001");
        onClose();
      },
      icon: Play,
    },
    {
      id: "export-report",
      label: "Export Investigation Report",
      desc: "Download JSON diagnostic artifact",
      action: () => {
        onExportReport();
        onClose();
      },
      icon: Download,
    },
  ].filter((item) => q === "" || item.label.toLowerCase().includes(q));

  // Flattened items for keyboard navigation
  type FlatItem =
    | { type: "incident"; item: IncidentMetadata }
    | { type: "nav"; item: (typeof navigationItems)[0] }
    | { type: "action"; item: (typeof actionItems)[0] };

  const allItems: FlatItem[] = [
    ...actionItems.map((item) => ({ type: "action" as const, item })),
    ...navigationItems.map((item) => ({ type: "nav" as const, item })),
    ...filteredIncidents.slice(0, 10).map((item) => ({ type: "incident" as const, item })),
  ];

  const handleSelect = (flatItem: FlatItem) => {
    if (flatItem.type === "action") {
      flatItem.item.action();
    } else if (flatItem.type === "nav") {
      onNavigateTab(flatItem.item.id);
      onClose();
    } else if (flatItem.type === "incident") {
      onSelectIncident(flatItem.item.incident_id);
      onNavigateTab("investigations");
      onClose();
    }
  };

  const handleKeyDownInput = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1 < allItems.length ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 >= 0 ? prev - 1 : allItems.length - 1));
    } else if (e.key === "Enter" && allItems[selectedIndex]) {
      e.preventDefault();
      handleSelect(allItems[selectedIndex]);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "14vh",
        backgroundColor: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "640px",
          backgroundColor: "#151513",
          border: "1px solid #2e2c26",
          borderRadius: "8px",
          boxShadow: "0 24px 60px -12px rgba(0, 0, 0, 0.8), 0 0 1px 1px rgba(231, 227, 220, 0.05)",
          overflow: "hidden",
          color: "#e7e3dc",
          display: "flex",
          flexDirection: "column",
          maxHeight: "70vh",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "14px 16px",
            borderBottom: "1px solid #292823",
            backgroundColor: "rgba(231, 227, 220, 0.015)",
          }}
        >
          <Search size={16} style={{ color: "#858178", flexShrink: 0 }} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search incidents..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDownInput}
            style={{
              flex: 1,
              background: "none",
              border: "none",
              outline: "none",
              color: "#e7e3dc",
              fontSize: "0.9375rem",
              fontFamily: "var(--font-sans)",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.6875rem",
              color: "#858178",
              backgroundColor: "rgba(231, 227, 220, 0.04)",
              padding: "2px 6px",
              borderRadius: "3px",
              border: "1px solid #292823",
            }}
          >
            ESC
          </span>
        </div>

        {/* Results List */}
        <div
          ref={listRef}
          style={{
            overflowY: "auto",
            padding: "8px",
            display: "flex",
            flexDirection: "column",
            gap: "2px",
          }}
        >
          {allItems.length === 0 ? (
            <div
              style={{
                padding: "32px 16px",
                textAlign: "center",
                color: "#858178",
                fontSize: "0.8125rem",
              }}
            >
              No commands or incidents matching &ldquo;{query}&rdquo;
            </div>
          ) : (
            <>
              {/* Actions Section */}
              {actionItems.length > 0 && (
                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.625rem",
                      fontWeight: 600,
                      color: "#858178",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      padding: "6px 8px 4px 8px",
                    }}
                  >
                    Quick Actions
                  </div>
                  {actionItems.map((act) => {
                    const idx = allItems.findIndex((it) => it.type === "action" && it.item.id === act.id);
                    const isSelected = idx === selectedIndex;
                    const IconComponent = act.icon;
                    return (
                      <div
                        key={act.id}
                        onClick={() => handleSelect({ type: "action", item: act })}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "8px 10px",
                          borderRadius: "4px",
                          backgroundColor: isSelected ? "rgba(231, 227, 220, 0.05)" : "transparent",
                          cursor: "pointer",
                          transition: "background-color 0.1s ease",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <IconComponent size={14} style={{ color: isSelected ? "#8fa58a" : "#858178" }} />
                          <div>
                            <div style={{ fontSize: "0.8125rem", fontWeight: 500, color: "#e7e3dc" }}>
                              {act.label}
                            </div>
                            <div style={{ fontSize: "0.6875rem", color: "#858178" }}>{act.desc}</div>
                          </div>
                        </div>
                        <ArrowRight size={12} style={{ color: isSelected ? "#e7e3dc" : "#57544d" }} />
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Navigation Section */}
              {navigationItems.length > 0 && (
                <div style={{ marginTop: "4px" }}>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.625rem",
                      fontWeight: 600,
                      color: "#858178",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      padding: "6px 8px 4px 8px",
                    }}
                  >
                    Navigation
                  </div>
                  {navigationItems.map((nav) => {
                    const idx = allItems.findIndex((it) => it.type === "nav" && it.item.id === nav.id);
                    const isSelected = idx === selectedIndex;
                    const IconComponent = nav.icon;
                    return (
                      <div
                        key={nav.id}
                        onClick={() => handleSelect({ type: "nav", item: nav })}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "8px 10px",
                          borderRadius: "4px",
                          backgroundColor: isSelected ? "rgba(231, 227, 220, 0.05)" : "transparent",
                          cursor: "pointer",
                          transition: "background-color 0.1s ease",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <IconComponent size={14} style={{ color: isSelected ? "#8fa58a" : "#858178" }} />
                          <div>
                            <div style={{ fontSize: "0.8125rem", fontWeight: 500, color: "#e7e3dc" }}>
                              {nav.label}
                            </div>
                            <div style={{ fontSize: "0.6875rem", color: "#858178" }}>{nav.desc}</div>
                          </div>
                        </div>
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.625rem",
                            color: "#858178",
                          }}
                        >
                          Jump
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Incidents Section */}
              {filteredIncidents.length > 0 && (
                <div style={{ marginTop: "4px" }}>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.625rem",
                      fontWeight: 600,
                      color: "#858178",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      padding: "6px 8px 4px 8px",
                    }}
                  >
                    Incidents ({filteredIncidents.length})
                  </div>
                  {filteredIncidents.slice(0, 8).map((inc) => {
                    const idx = allItems.findIndex(
                      (it) => it.type === "incident" && it.item.incident_id === inc.incident_id
                    );
                    const isSelected = idx === selectedIndex;
                    return (
                      <div
                        key={inc.incident_id}
                        onClick={() => handleSelect({ type: "incident", item: inc })}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "8px 10px",
                          borderRadius: "4px",
                          backgroundColor: isSelected ? "rgba(231, 227, 220, 0.05)" : "transparent",
                          cursor: "pointer",
                          transition: "background-color 0.1s ease",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", overflow: "hidden" }}>
                          <span
                            style={{
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.75rem",
                              fontWeight: 500,
                              color: "#e7e3dc",
                              flexShrink: 0,
                            }}
                          >
                            {inc.incident_id}
                          </span>
                          <div style={{ overflow: "hidden" }}>
                            <div
                              style={{
                                fontSize: "0.8125rem",
                                color: "#e7e3dc",
                                whiteSpace: "nowrap",
                                textOverflow: "ellipsis",
                                overflow: "hidden",
                              }}
                            >
                              {inc.name}
                            </div>
                            <div
                              style={{
                                fontFamily: "var(--font-mono)",
                                fontSize: "0.6875rem",
                                color: "#858178",
                              }}
                            >
                              {inc.affected_service}
                            </div>
                          </div>
                        </div>
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.625rem",
                            padding: "2px 6px",
                            borderRadius: "3px",
                            backgroundColor:
                              inc.severity === "CRITICAL"
                                ? "rgba(196, 104, 93, 0.12)"
                                : "rgba(194, 155, 56, 0.12)",
                            color: inc.severity === "CRITICAL" ? "#c4685d" : "#c29b38",
                            flexShrink: 0,
                          }}
                        >
                          {inc.severity}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer shortcuts */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "8px 16px",
            borderTop: "1px solid #292823",
            fontSize: "0.6875rem",
            color: "#858178",
            fontFamily: "var(--font-mono)",
            backgroundColor: "#111110",
          }}
        >
          <div style={{ display: "flex", gap: "12px" }}>
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Close</span>
          </div>
          <div>Aletheia Investigation Instrument</div>
        </div>
      </div>
    </div>
  );
}
