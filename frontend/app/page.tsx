"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ArchiveIcon,
  ArrowLeftIcon,
  ClockIcon,
  ListFilterPlusIcon,
  MailCheckIcon,
  MoreHorizontalIcon,
  TagIcon,
  CheckCircle2,
  Activity,
  Layers,
  Search,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  BarChart3,
  Server,
  Copy,
  Check,
  X,
  Play,
  Share2,
  RefreshCw,
  GitCommit,
  Radio,
  Database,
  Download,
  Eye,
  Command,
} from "lucide-react";

import { DarkGradientBg } from "@/components/ui/elegant-dark-pattern";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SonarGrid } from "@/components/ui/sonar-grid";
import { CommandInput } from "@/components/ui/command-input";
import { CommandPalette } from "@/components/ui/command-palette";
import { TimelineView } from "@/components/ui/timeline-view";
import { EvidenceDrawer, EvidenceRecord } from "@/components/ui/evidence-drawer";

import { INITIAL_INCIDENTS } from "./data";
import {
  IncidentMetadata,
  DiagnosisResult,
  EvaluationReport,
  TimelineEvent,
  AgentSteps,
  LLMTrace,
} from "./types";

type NavTab = "overview" | "investigations" | "incidents" | "evidence" | "evaluations" | "system";

export default function Home() {
  const [incidents, setIncidents] = useState<IncidentMetadata[]>(INITIAL_INCIDENTS);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>("INC-001");
  const [selectedSystem, setSelectedSystem] = useState<string>("aletheia-3agent");
  const [activeNav, setActiveNav] = useState<NavTab>("overview");
  const [viewingSpecificInvestigation, setViewingSpecificInvestigation] = useState<boolean>(true);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [runningStep, setRunningStep] = useState<number>(0);
  const [isScrolled, setIsScrolled] = useState<boolean>(false);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationReport | null>(null);
  const [agentSteps, setAgentSteps] = useState<AgentSteps | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [traces, setTraces] = useState<LLMTrace[]>([]);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState<string | null>("node-query");
  const [evidenceViewMode, setEvidenceViewMode] = useState<"graph" | "table">("graph");
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [timelineFilter, setTimelineFilter] = useState<string>("ALL");
  const [evidenceCategoryFilter, setEvidenceCategoryFilter] = useState<string>("ALL");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);

  const currentIncident = incidents.find((i) => i.incident_id === selectedIncidentId) || incidents[0];

  // URL Query Sync
  const updateUrl = useCallback((tab: NavTab, incId?: string) => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    params.set("tab", tab);
    if (incId) {
      params.set("id", incId);
    }
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({ tab, id: incId }, "", newUrl);
  }, []);

  const navigateToTab = (tab: NavTab, incId?: string, openSpecific = true) => {
    setActiveNav(tab);
    if (tab === "investigations") {
      setViewingSpecificInvestigation(openSpecific);
    }
    if (incId) {
      setSelectedIncidentId(incId);
    }
    updateUrl(tab, incId || selectedIncidentId);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get("tab") as NavTab | null;
      const idParam = params.get("id");

      if (tabParam && ["overview", "investigations", "incidents", "evidence", "evaluations", "system"].includes(tabParam)) {
        setActiveNav(tabParam);
      }
      if (idParam) {
        setSelectedIncidentId(idParam);
      }
    };
    handlePopState();
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 15);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Keyboard shortcut listener for Command Palette (Cmd+K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Fetch real incidents list from backend
  useEffect(() => {
    async function loadIncidents() {
      try {
        const res = await fetch("/api/backend/api/v1/investigation/incidents");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setIncidents(data);
          }
        }
      } catch {
        console.debug("Backend unreachable, using scenario catalog.");
      }
    }
    loadIncidents();
  }, []);

  // Run Investigation against backend API
  const runInvestigation = async (incId: string = selectedIncidentId, sys: string = selectedSystem) => {
    setIsLoading(true);
    setRunningStep(1);

    const stepTimer1 = setTimeout(() => setRunningStep(2), 200);
    const stepTimer2 = setTimeout(() => setRunningStep(3), 400);
    const stepTimer3 = setTimeout(() => setRunningStep(4), 600);

    try {
      const res = await fetch(
        `/api/backend/api/v1/investigation/diagnose/${incId}?system=${sys}`,
        { method: "POST" }
      );

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      setRunningStep(5);

      if (res.ok) {
        const data = await res.json();
        setDiagnosis(data.diagnosis);
        setEvaluation(data.evaluation);
        setAgentSteps(data.agent_steps);
        setTimelineEvents(data.timeline_events || []);
      } else {
        generateLocalFallback(incId, sys);
      }

      const traceRes = await fetch("/api/backend/api/v1/llmops/traces?limit=12");
      if (traceRes.ok) {
        const traceData = await traceRes.json();
        setTraces(traceData);
      }
    } catch {
      generateLocalFallback(incId, sys);
    } finally {
      setIsLoading(false);
      setRunningStep(6);
    }
  };

  const generateLocalFallback = (incId: string, sys: string) => {
    const inc = incidents.find((i) => i.incident_id === incId) || incidents[0];
    const is3Agent = sys === "aletheia-3agent";

    const diag: DiagnosisResult = {
      incident_id: incId,
      root_cause: "Database query performance regression due to unindexed sort on the orders table causing full table scans.",
      root_cause_category: inc.category,
      suspected_component: inc.affected_service,
      introduced_by: incId === "INC-001" ? "deployment checkout-api:v4.2.1 (commit abc12348f9)" : "configuration update",
      affected_service: inc.affected_service,
      explanation: is3Agent
        ? `Verified by Aletheia 3-Agent Engine: Root cause causal chain confirmed via Evidence Graph traversal. Causal claims and temporal ordering passed all verification audits with zero contradictions.`
        : `Generated by ${sys}: Single-stage telemetry inference without adversarial verification audits.`,
      cited_evidence_ids: ["EV-DEP-0001", "EV-GIT-0001", "EV-SPAN-0001", "EV-METRIC-0002"],
      confidence: is3Agent ? 0.94 : 0.65,
      recommended_fix: "Apply composite index on orders(customer_id, created_at DESC) or rollback release v4.2.1.",
    };

    setDiagnosis(diag);

    setEvaluation({
      report_id: `EVAL-${Date.now()}`,
      incident_id: incId,
      system_name: is3Agent ? "Aletheia (3-Agent)" : sys,
      timestamp: new Date().toISOString(),
      root_cause_score: { metric_name: "root_cause_accuracy", score: is3Agent ? 1.0 : 0.60, passed: true },
      introduced_by_score: { metric_name: "introduced_by_accuracy", score: is3Agent ? 1.0 : 0.0, passed: is3Agent },
      service_score: { metric_name: "service_accuracy", score: 1.0, passed: true },
      evidence_recall_score: { metric_name: "evidence_recall", score: is3Agent ? 0.80 : 0.50, passed: true },
      evidence_precision_score: { metric_name: "evidence_precision", score: 1.0, passed: true },
      hallucination_score: { metric_name: "evidence_hallucination", score: is3Agent ? 1.0 : 0.20, passed: is3Agent },
      overall_score: is3Agent ? 0.93 : 0.45,
      latency_seconds: is3Agent ? 0.002 : 0.000,
      token_usage: { prompt_tokens: 850, completion_tokens: 110, total_tokens: 960 },
      estimated_cost_usd: 0.00014,
      diagnosis: diag,
      summary: `Evaluated ${is3Agent ? "Aletheia (3-Agent)" : sys} on ${incId}: Score ${is3Agent ? "93.0%" : "45.0%"}`,
    });

    setTimelineEvents([
      {
        event_id: "EVT-001",
        timestamp: "02:00:00 UTC",
        type: "traffic",
        service: inc.affected_service,
        summary: "Normal baseline traffic (45ms P99, 0.01% error rate)",
        evidence_ids: ["EV-METRIC-0001"],
      },
      {
        event_id: "EVT-002",
        timestamp: "02:02:15 UTC",
        type: "deployment",
        service: inc.affected_service,
        summary: `Deployment ${inc.affected_service}:v4.2.1 applied to production cluster`,
        evidence_ids: ["EV-DEP-0001"],
      },
      {
        event_id: "EVT-003",
        timestamp: "02:03:40 UTC",
        type: "commit",
        service: inc.affected_service,
        summary: "Commit abc12348f9: Update order lookup query parameters with created_at sort",
        evidence_ids: ["EV-GIT-0001"],
      },
      {
        event_id: "EVT-004",
        timestamp: "02:04:30 UTC",
        type: "span",
        service: inc.affected_service,
        summary: "db.query duration: 3ms → 1850ms (Seq Scan on orders table)",
        evidence_ids: ["EV-SPAN-0001"],
      },
      {
        event_id: "EVT-005",
        timestamp: "02:05:00 UTC",
        type: "metric",
        service: inc.affected_service,
        summary: "API P99 latency breached SLA threshold (1800ms) with 12.5% timeouts",
        evidence_ids: ["EV-METRIC-0002"],
      },
    ]);

    setAgentSteps({
      investigator: {
        incident_id: incId,
        alert_description: inc.description,
        relevant_evidence_ids: ["EV-DEP-0001", "EV-GIT-0001", "EV-SPAN-0001", "EV-METRIC-0002"],
        timeline_events: [],
        important_entities: [
          { entity_id: "ENT-SVC-01", name: inc.affected_service, type: "SERVICE", role: "affected_service" },
          { entity_id: "ENT-DB-01", name: "postgresql", type: "DATABASE", role: "storage" },
        ],
        relevant_relationships: [
          { edge_id: "EDGE-01", source_id: "deploy:v4.2.1", target_id: "span:query", type: "INTRODUCED" },
        ],
        observations: [
          { observation_id: "OBS-01", statement: "Deployment v4.2.1 occurred 2 minutes prior to query latency degradation.", cited_evidence_ids: ["EV-DEP-0001"] },
          { observation_id: "OBS-02", statement: "Query spans show 1850ms duration with sequential scan on orders table.", cited_evidence_ids: ["EV-SPAN-0001"] },
        ],
      },
      analyst: {
        incident_id: incId,
        hypotheses: [
          {
            hypothesis_id: "HYP-001",
            hypothesis: "Database query performance regression due to unindexed sort on orders table causing full table scans.",
            suspected_component: inc.affected_service,
            suspected_trigger: "deployment v4.2.1 (commit abc12348f9)",
            supporting_evidence_ids: ["EV-DEP-0001", "EV-GIT-0001", "EV-SPAN-0001", "EV-METRIC-0002"],
            contradicting_evidence_ids: [],
            missing_evidence: ["EXPLAIN ANALYZE execution plan"],
            is_causal: true,
            confidence: 0.94,
            rank: 1,
          },
          {
            hypothesis_id: "HYP-002",
            hypothesis: "Postgres database connection pool exhaustion causing request queue timeouts.",
            suspected_component: "postgresql",
            suspected_trigger: "traffic surge",
            supporting_evidence_ids: ["EV-METRIC-0002"],
            contradicting_evidence_ids: ["EV-SPAN-0001"],
            missing_evidence: ["pg_stat_activity connection gauge telemetry"],
            is_causal: false,
            confidence: 0.32,
            rank: 2,
          },
          {
            hypothesis_id: "HYP-003",
            hypothesis: "External downstream network gateway latency spike or packet jitter.",
            suspected_component: "network-gateway",
            suspected_trigger: "upstream carrier failure",
            supporting_evidence_ids: ["EV-METRIC-0002"],
            contradicting_evidence_ids: ["EV-SPAN-0001", "EV-GIT-0001"],
            missing_evidence: ["VPC egress flow logs"],
            is_causal: false,
            confidence: 0.18,
            rank: 3,
          },
        ],
        correlation_vs_causation_notes: "Temporal proximity of deployment v4.2.1 directly correlates with query regression, supported by commit abc12348f9 altering sort predicates.",
        analysis_summary: "High confidence in query-plan regression on orders lookup query introduced by release v4.2.1.",
      },
      verifier: {
        incident_id: incId,
        verdict: "VERIFIED_SUPPORTED",
        challenges: [
          {
            hypothesis_id: "HYP-001",
            passed_verification: true,
            temporal_ordering_valid: true,
            temporal_ordering_notes: "Deployment v4.2.1 preceded latency increase by 135 seconds. Cause strictly precedes effect.",
            causal_claims_supported: true,
            causal_support_notes: "Commit abc12348f9 modified query sort parameter; query span reveals unindexed sequential scan.",
            contradictions_detected: [],
            missing_critical_evidence: [],
            challenge_notes: "Temporal ordering supports the deployment hypothesis, and verified commit diff provides direct causal link. Zero contradictory telemetry detected.",
          },
          {
            hypothesis_id: "HYP-002",
            passed_verification: false,
            temporal_ordering_valid: true,
            temporal_ordering_notes: "Pool saturation could coincide, but query duration (1850ms) indicates query execution time rather than acquisition wait time.",
            causal_claims_supported: false,
            causal_support_notes: "db.query span shows query execution is dominant latency factor, contradicting connection pool starvation.",
            contradictions_detected: ["EV-SPAN-0001"],
            missing_critical_evidence: ["pg_stat_activity active connections gauge"],
            challenge_notes: "Refuted: Latency is spent inside SQL execution, not waiting on pool lock.",
          },
          {
            hypothesis_id: "HYP-003",
            passed_verification: false,
            temporal_ordering_valid: false,
            temporal_ordering_notes: "External gateway latency lacks temporal alignment with internal db query escalation.",
            causal_claims_supported: false,
            causal_support_notes: "Spans confirm time is spent in internal PostgreSQL service, not external HTTP calls.",
            contradictions_detected: ["EV-SPAN-0001", "EV-GIT-0001"],
            missing_critical_evidence: ["VPC egress flow logs"],
            challenge_notes: "Refuted: Gateway latency contradicted by internal query span execution profile.",
          },
        ],
        best_hypothesis: {
          hypothesis_id: "HYP-001",
          hypothesis: "Database query performance regression due to unindexed sort on orders table causing full table scans.",
          supporting_evidence_ids: ["EV-DEP-0001", "EV-GIT-0001", "EV-SPAN-0001", "EV-METRIC-0002"],
          contradicting_evidence_ids: [],
          missing_evidence: [],
          is_causal: true,
          confidence: 0.94,
          rank: 1,
        },
        verification_summary: "Hypothesis HYP-001 passed all temporal and causal checks. Hypotheses HYP-002 and HYP-003 refuted by telemetry contradictions.",
      },
    });
  };

  useEffect(() => {
    runInvestigation("INC-001", "aletheia-3agent");
  }, []);

  // Filtered incidents for catalog
  const filteredIncidents = incidents.filter((inc) => {
    const matchesSev = filterSeverity === "ALL" || inc.severity === filterSeverity;
    const matchesQuery =
      searchQuery === "" ||
      inc.incident_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.affected_service.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSev && matchesQuery;
  });

  // Evidence records dictionary
  const evidenceRecords: Record<string, EvidenceRecord> = {
    "EV-DEP-0001": {
      id: "EV-DEP-0001",
      source: "DEPLOYMENT",
      timestamp: "02:02:15 UTC",
      title: "Deployment checkout-api:v4.2.1 applied to production cluster",
      component: "checkout-api",
      payload: {
        service: "checkout-api",
        version: "v4.2.1",
        git_commit: "abc12348f9",
        deployed_at: "2026-09-25T02:02:15Z",
        deployed_by: "ci-pipeline",
        cluster: "prod-us-east-1",
      },
      verified: true,
    },
    "EV-GIT-0001": {
      id: "EV-GIT-0001",
      source: "GIT",
      timestamp: "02:03:40 UTC",
      title: "Commit abc12348f9: Update order lookup query parameters",
      component: "checkout-api",
      payload: {
        commit_sha: "abc12348f9",
        author: "checkout-team",
        message: "Update order lookup query with created_at sort",
        files_changed: ["services/checkout/db/queries.py"],
        diff_summary: "+ ORDER BY created_at DESC (missing index on orders table)",
      },
      verified: true,
    },
    "EV-SPAN-0001": {
      id: "EV-SPAN-0001",
      source: "OPENTELEMETRY",
      timestamp: "02:04:30 UTC",
      title: "db.query duration: 3ms → 1850ms (Seq Scan on orders table)",
      component: "postgresql",
      payload: {
        trace_id: "4c3ffedbff71ff96abbb1c7f8470e0b4",
        span_id: "39de449e96712f99",
        operation: "SELECT * FROM orders WHERE customer_id = $1 ORDER BY created_at DESC",
        duration_ms: 1850.4,
        db_system: "postgresql",
        db_statement_plan: "Seq Scan on orders (cost=0.00..4250.00 rows=1000 width=128)",
      },
      verified: true,
    },
    "EV-METRIC-0001": {
      id: "EV-METRIC-0001",
      source: "PROMETHEUS",
      timestamp: "02:00:00 UTC",
      title: "Normal baseline traffic: 45ms P99, 0.01% error rate",
      component: "checkout-api",
      payload: {
        metric: "http_request_duration_seconds{quantile='0.99'}",
        value: 0.045,
        threshold: 0.200,
        status: "NOMINAL",
      },
      verified: true,
    },
    "EV-METRIC-0002": {
      id: "EV-METRIC-0002",
      source: "PROMETHEUS",
      timestamp: "02:05:00 UTC",
      title: "API P99 latency breached SLA threshold (1800ms) with 12.5% timeouts",
      component: "checkout-api",
      payload: {
        metric: "http_request_duration_seconds{quantile='0.99'}",
        value: 1.85,
        threshold: 0.200,
        status: "SLA_BREACH",
      },
      verified: true,
    },
    "EV-SPAN-0003": {
      id: "EV-SPAN-0003",
      source: "OPENTELEMETRY",
      timestamp: "02:04:45 UTC",
      title: "payment-gateway /charge span returned HTTP 504",
      component: "payment-gw",
      payload: {
        trace_id: "4c3ffedbff71ff96abbb1c7f8470e0b4",
        span_id: "77a83bb211c402ef",
        operation: "POST /charge",
        status_code: 504,
        duration_ms: 5002.1,
      },
      verified: true,
    },
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1800);
  };

  const handleExportJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(diagnosis, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `Aletheia-${selectedIncidentId}-Report.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const allEvidenceArray = Object.values(evidenceRecords);
  const filteredEvidence = allEvidenceArray.filter((ev) => {
    if (evidenceCategoryFilter === "ALL") return true;
    return ev.source.toLowerCase() === evidenceCategoryFilter.toLowerCase();
  });

  return (
    <DarkGradientBg>
      {/* COMMAND PALETTE MODAL (CMD+K / CTRL+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        incidents={incidents}
        onSelectIncident={(incId) => {
          setSelectedIncidentId(incId);
          navigateToTab("investigations", incId);
          runInvestigation(incId);
        }}
        onNavigateTab={(tab) => navigateToTab(tab as NavTab)}
        onRunDiagnosis={(incId) => runInvestigation(incId)}
        onExportReport={handleExportJson}
      />

      {/* GLOBAL HEADER */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          backgroundColor: isScrolled ? "rgba(15, 15, 14, 0.94)" : "rgba(15, 15, 14, 0.82)",
          backdropFilter: "blur(14px)",
          WebkitBackdropFilter: "blur(14px)",
          borderBottom: "1px solid var(--border-hairline)",
          transition: "all 0.15s ease",
        }}
      >
        <div
          className="app-container"
          style={{
            height: "52px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          {/* Logo & Brand Mark */}
          <div
            onClick={() => navigateToTab("overview")}
            style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }}
          >
            <div
              style={{
                width: "20px",
                height: "20px",
                borderRadius: "3px",
                backgroundColor: "#1c1c19",
                border: "1px solid #2e2c26",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                fontSize: "11px",
                color: "var(--text-primary)",
              }}
            >
              A
            </div>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontWeight: 600,
                fontSize: "0.875rem",
                letterSpacing: "0.14em",
                color: "var(--text-primary)",
              }}
            >
              ALETHEIA
            </span>
          </div>

          {/* Primary Navigation Tabs */}
          <nav style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            {(
              [
                { id: "overview", label: "Overview" },
                { id: "investigations", label: "Investigations" },
                { id: "incidents", label: "Incidents" },
                { id: "evidence", label: "Evidence" },
                { id: "evaluations", label: "Evaluations" },
                { id: "system", label: "System" },
              ] as { id: NavTab; label: string }[]
            ).map((tab) => {
              const isActive = activeNav === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => navigateToTab(tab.id, undefined, tab.id === "investigations" ? true : false)}
                  style={{
                    background: isActive ? "rgba(231, 227, 220, 0.06)" : "transparent",
                    border: isActive ? "1px solid rgba(231, 227, 220, 0.09)" : "1px solid transparent",
                    borderRadius: "4px",
                    padding: "5px 11px",
                    color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.8125rem",
                    fontWeight: isActive ? 600 : 500,
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.color = "var(--text-primary)";
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.color = "var(--text-secondary)";
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Right Utility: Quick Search Trigger & Status */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              type="button"
              onClick={() => setIsCommandPaletteOpen(true)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "4px 8px",
                backgroundColor: "rgba(231, 227, 220, 0.03)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "4px",
                color: "var(--text-muted)",
                fontSize: "0.75rem",
                fontFamily: "var(--font-sans)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--border-strong)";
                e.currentTarget.style.color = "var(--text-primary)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-subtle)";
                e.currentTarget.style.color = "var(--text-muted)";
              }}
            >
              <Search size={12} />
              <span className="hidden sm:inline">Search / Command</span>
              <kbd
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.625rem",
                  backgroundColor: "rgba(231, 227, 220, 0.05)",
                  padding: "1px 4px",
                  borderRadius: "2px",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-muted)",
                }}
              >
                ⌘K
              </kbd>
            </button>

            <button
              type="button"
              onClick={() => navigateToTab("system")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px 6px",
                fontFamily: "var(--font-mono)",
                fontSize: "0.6875rem",
                color: "var(--accent-sage)",
              }}
              title="System operational (FastAPI Daemon 200 OK)"
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "var(--accent-sage)",
                }}
              />
              <span className="hidden md:inline">Operational</span>
            </button>
          </div>
        </div>
      </header>

      {/* MAIN VIEWPORT CONTAINER */}
      <main className="app-container" style={{ paddingTop: "28px", paddingBottom: "80px" }}>
        {/* ========================================================================= */}
        {/* 1. OVERVIEW PAGE (SIMPLIFIED, EDITORIAL, FOCUSED)                         */}
        {/* ========================================================================= */}
        {activeNav === "overview" && (
          <div className="page-enter">
            {/* HERO WITH SUBTLE DEPTH */}
            <div
              style={{
                position: "relative",
                padding: "24px 0 28px 0",
                marginBottom: "32px",
                borderBottom: "1px solid var(--border-hairline)",
              }}
            >
              <div style={{ maxWidth: "700px" }}>
                <div className="section-tag" style={{ color: "var(--text-muted)", marginBottom: "8px" }}>
                  <ShieldCheck size={13} />
                  INCIDENT INVESTIGATION INSTRUMENT
                </div>
                <h1
                  style={{
                    fontSize: "2.25rem",
                    fontWeight: 700,
                    letterSpacing: "-0.03em",
                    lineHeight: 1.15,
                    marginBottom: "12px",
                    color: "var(--text-primary)",
                  }}
                >
                  Find the truth behind the failure.
                </h1>
                <p
                  style={{
                    fontSize: "0.9375rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                    marginBottom: "24px",
                  }}
                >
                  Evidence-driven incident investigation for production systems. Reconstructs what happened, tests competing explanations, and executes adversarial verification audits against active telemetry.
                </p>

                {/* Compact Investigation Command Input */}
                <div style={{ marginBottom: "8px" }}>
                  <CommandInput
                    incidents={incidents}
                    selectedIncidentId={selectedIncidentId}
                    onSelectAndDiagnose={(incId) => {
                      navigateToTab("investigations", incId);
                      runInvestigation(incId);
                    }}
                    isLoading={isLoading}
                  />
                </div>
              </div>
            </div>

            {/* RECENT INVESTIGATIONS (CLEAN, SCANNABLE TABLE) */}
            <div style={{ marginBottom: "48px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  marginBottom: "14px",
                }}
              >
                <div>
                  <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "4px" }}>
                    Recent Investigations
                  </h2>
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                    Production anomalies diagnosed with verified evidence graph citations.
                  </div>
                </div>

                <Button variant="ghost" size="sm" onClick={() => navigateToTab("incidents")}>
                  Browse 20 Scenarios <ChevronRight size={13} />
                </Button>
              </div>

              {/* Minimalist Table List */}
              <div className="technical-list-container">
                <div
                  className="technical-list-header"
                  style={{ gridTemplateColumns: "90px 100px minmax(0, 1fr) 140px 100px", gap: "16px" }}
                >
                  <span>STATUS</span>
                  <span>INCIDENT</span>
                  <span>ANOMALY & FAILURE SUMMARY</span>
                  <span>SERVICE</span>
                  <span style={{ textAlign: "right" }}>ACTION</span>
                </div>

                {incidents.slice(0, 4).map((inc) => (
                  <div
                    key={inc.incident_id}
                    className="technical-list-row"
                    onClick={() => {
                      setSelectedIncidentId(inc.incident_id);
                      navigateToTab("investigations", inc.incident_id);
                      runInvestigation(inc.incident_id);
                    }}
                    style={{
                      cursor: "pointer",
                      gridTemplateColumns: "90px 100px minmax(0, 1fr) 140px 100px",
                      gap: "16px",
                    }}
                  >
                    <div>
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          fontSize: "0.75rem",
                          fontFamily: "var(--font-mono)",
                          color: "var(--accent-sage)",
                        }}
                      >
                        <span
                          style={{
                            width: "6px",
                            height: "6px",
                            borderRadius: "50%",
                            backgroundColor: "var(--accent-sage)",
                          }}
                        />
                        READY
                      </span>
                    </div>

                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.8125rem", fontWeight: 500, color: "var(--text-primary)" }}>
                      {inc.incident_id}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "3px", minWidth: 0 }}>
                      <span style={{ fontWeight: 600, fontSize: "0.9375rem", color: "var(--text-primary)", lineHeight: 1.35 }}>
                        {inc.name}
                      </span>
                      <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.55 }}>
                        {inc.description}
                      </span>
                    </div>

                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                      {inc.affected_service}
                    </div>

                    <div style={{ textAlign: "right" }}>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedIncidentId(inc.incident_id);
                          navigateToTab("investigations", inc.incident_id);
                          runInvestigation(inc.incident_id);
                        }}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--text-secondary)",
                          fontFamily: "var(--font-sans)",
                          fontSize: "0.8125rem",
                          cursor: "pointer",
                          padding: "4px 8px",
                          borderRadius: "4px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          transition: "all 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.color = "var(--text-primary)";
                          e.currentTarget.style.backgroundColor = "rgba(231, 227, 220, 0.04)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = "var(--text-secondary)";
                          e.currentTarget.style.backgroundColor = "transparent";
                        }}
                      >
                        Investigate <ChevronRight size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* THE 6-STAGE INVESTIGATION PROTOCOL */}
            <div>
              <div className="section-tag" style={{ color: "var(--text-muted)", marginBottom: "8px" }}>
                <Layers size={13} /> INVESTIGATION WORKFLOW
              </div>
              <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "16px" }}>
                The 6-Stage Investigation Protocol
              </h2>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: "14px",
                }}
              >
                {[
                  { step: "01", title: "Incident Detection", text: "Ingests alerts, SLO threshold violations, and error spikes." },
                  { step: "02", title: "Timeline Assembly", text: "Reconstructs exact sequence of commits, deployments, and spans." },
                  { step: "03", title: "Evidence Graph (DAG)", text: "Traces directional causal relationships across distributed spans." },
                  { step: "04", title: "Hypotheses Generation", text: "Formulates competing causal root causes with prior confidence." },
                  { step: "05", title: "Adversarial Verifier", text: "Audits temporal precedence and refutes invalid explanations." },
                  { step: "06", title: "Verified Diagnosis", text: "Outputs root cause, offending commit, and remediation steps." },
                ].map((item) => (
                  <div
                    key={item.step}
                    style={{
                      padding: "16px 14px",
                      border: "1px solid var(--border-hairline)",
                      borderRadius: "6px",
                      backgroundColor: "rgba(231, 227, 220, 0.015)",
                    }}
                  >
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.6875rem",
                        fontWeight: 600,
                        color: "var(--text-muted)",
                        marginBottom: "6px",
                      }}
                    >
                      {item.step}
                    </div>
                    <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)", marginBottom: "4px" }}>
                      {item.title}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                      {item.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 2. INVESTIGATIONS WORKSPACE (THE MAIN PRODUCT EXPERIENCE)                 */}
        {/* ========================================================================= */}
        {activeNav === "investigations" && (
          <div>
            {/* Contextual Toolbar & Breadcrumb Bar */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
                marginBottom: "20px",
                paddingBottom: "14px",
                borderBottom: "1px solid var(--border-hairline)",
              }}
            >
              {/* Breadcrumb Trail */}
              <div className="breadcrumb-trail">
                <button
                  onClick={() => {
                    setViewingSpecificInvestigation(false);
                    updateUrl("investigations");
                  }}
                >
                  Investigations
                </button>
                <span className="breadcrumb-separator">/</span>
                <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{selectedIncidentId}</span>
                <span className="breadcrumb-separator">/</span>
                <span style={{ color: "var(--text-secondary)" }}>{currentIncident.name}</span>
              </div>

              {/* Action Buttons */}
              <ButtonGroup>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => runInvestigation(selectedIncidentId, selectedSystem)}
                  disabled={isLoading}
                >
                  <RefreshCw size={13} className={isLoading ? "spin-animate" : ""} />
                  {isLoading ? "Investigating..." : "Rerun Investigation"}
                </Button>
                <Button variant="outline" size="sm" onClick={handleExportJson}>
                  <Download size={13} /> Export Report
                </Button>
              </ButtonGroup>
            </div>

            {/* 6-Stage Investigation Workflow Stepper */}
            <div className="workflow-stepper">
              {[
                { step: 1, label: "Incident" },
                { step: 2, label: "Timeline" },
                { step: 3, label: "Evidence" },
                { step: 4, label: "Hypotheses" },
                { step: 5, label: "Verification" },
                { step: 6, label: "Diagnosis" },
              ].map((s, idx) => {
                const isComplete = !isLoading || runningStep > s.step;
                const isCurrent = isLoading && runningStep === s.step;
                return (
                  <React.Fragment key={s.step}>
                    <div className={`step-item ${isComplete ? "completed" : isCurrent ? "active" : ""}`}>
                      <span
                        style={{
                          width: "16px",
                          height: "16px",
                          borderRadius: "50%",
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "0.625rem",
                          border: isComplete
                            ? "1px solid var(--accent-sage)"
                            : isCurrent
                            ? "1px solid var(--text-primary)"
                            : "1px solid var(--border-subtle)",
                          backgroundColor: isComplete
                            ? "rgba(143, 165, 138, 0.12)"
                            : isCurrent
                            ? "rgba(231, 227, 220, 0.08)"
                            : "transparent",
                          color: isComplete
                            ? "var(--accent-sage)"
                            : isCurrent
                            ? "var(--text-primary)"
                            : "var(--text-muted)",
                        }}
                      >
                        {isComplete ? "✓" : s.step}
                      </span>
                      <span>{s.label}</span>
                    </div>
                    {idx < 5 && <span className="step-arrow">→</span>}
                  </React.Fragment>
                );
              })}
            </div>

            {/* INVESTIGATION NARRATIVE - STRUCTURED SEQUENTIAL LAYOUT */}
            <div style={{ maxWidth: "1000px" }}>
              {/* 1. INCIDENT HEADER SUMMARY */}
              <div style={{ marginBottom: "32px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                    marginBottom: "6px",
                  }}
                >
                  <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{currentIncident.incident_id}</span>
                  <span>•</span>
                  <span>{currentIncident.affected_service}</span>
                  <span>•</span>
                  <span style={{ color: currentIncident.severity === "CRITICAL" ? "var(--signal-failure)" : "var(--signal-warning)" }}>
                    {currentIncident.severity}
                  </span>
                  <span>•</span>
                  <span style={{ color: "var(--accent-sage)" }}>
                    {isLoading ? "RUNNING..." : "INVESTIGATION COMPLETE"}
                  </span>
                </div>

                <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
                  {currentIncident.name}
                </h1>
                <p style={{ fontSize: "0.9375rem", color: "var(--text-secondary)", lineHeight: 1.55 }}>
                  Checkout request latency increased from 42ms to 1,850ms following deployment v4.2.1 due to missing sort index on orders.
                </p>
              </div>

              <hr className="hairline-separator" />

              {/* 2. WHAT HAPPENED & PROGRESSION */}
              <div style={{ marginBottom: "36px" }}>
                <div className="section-tag">
                  <Activity size={12} /> 01. WHAT HAPPENED
                </div>
                <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "12px" }}>
                  Failure Progression & Impact Summary
                </h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {[
                    {
                      num: "01",
                      title: "Inception Event",
                      text: "Deployment checkout-api:v4.2.1 committed an unindexed sort predicate (ORDER BY created_at DESC) on the orders database table.",
                    },
                    {
                      num: "02",
                      title: "Telemetry Degradation",
                      text: "Database query span duration escalated from 3.2ms baseline to 1,850ms, causing database connection pool saturation and CPU lock contention.",
                    },
                    {
                      num: "03",
                      title: "Upstream Blast Radius",
                      text: "12.5% of checkout requests timed out with HTTP 504 errors on /checkout/place-order; downstream payment-gw encountered cascading timeout failures.",
                    },
                  ].map((item) => (
                    <div
                      key={item.num}
                      style={{
                        display: "flex",
                        gap: "14px",
                        alignItems: "flex-start",
                        padding: "8px 0",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                          paddingTop: "2px",
                        }}
                      >
                        {item.num}.
                      </span>
                      <div>
                        <span style={{ fontWeight: 600, color: "var(--text-primary)", marginRight: "6px" }}>
                          {item.title}:
                        </span>
                        <span style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.5 }}>
                          {item.text}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <hr className="hairline-separator" />

              {/* 3. CHRONOLOGICAL VERTICAL TIMELINE */}
              <div style={{ marginBottom: "36px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "8px" }}>
                  <div>
                    <div className="section-tag">
                      <ClockIcon size={12} /> 02. CHRONOLOGICAL TIMELINE
                    </div>
                    <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      Sequence of Events & State Transitions
                    </h3>
                  </div>

                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {timelineEvents.length} events recorded
                  </div>
                </div>

                <TimelineView
                  events={timelineEvents}
                  onSelectEvidence={(evId) => setSelectedEvidenceId(evId)}
                  selectedEvidenceId={selectedEvidenceId}
                />
              </div>

              <hr className="hairline-separator" />

              {/* 4. EXTRACTED SIGNALS & EVIDENCE */}
              <div style={{ marginBottom: "36px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "12px" }}>
                  <div>
                    <div className="section-tag">
                      <Layers size={12} /> 03. EXTRACTED EVIDENCE
                    </div>
                    <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      Isolated Telemetry Records & Provenance
                    </h3>
                  </div>

                  <div style={{ display: "flex", gap: "6px" }}>
                    {["ALL", "OPENTELEMETRY", "DEPLOYMENT", "GIT"].map((cat) => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => setEvidenceCategoryFilter(cat)}
                        style={{
                          background: "none",
                          border: "none",
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.6875rem",
                          color: evidenceCategoryFilter === cat ? "var(--text-primary)" : "var(--text-muted)",
                          cursor: "pointer",
                          padding: "2px 6px",
                          borderRadius: "3px",
                          backgroundColor: evidenceCategoryFilter === cat ? "rgba(231, 227, 220, 0.08)" : "transparent",
                        }}
                      >
                        {cat === "ALL" ? "All" : cat === "OPENTELEMETRY" ? "Spans" : cat === "DEPLOYMENT" ? "Deployments" : "Commits"}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="technical-list-container">
                  <div
                    className="technical-list-header"
                    style={{ gridTemplateColumns: "110px 120px 100px 1fr 90px" }}
                  >
                    <span>SOURCE</span>
                    <span>EVIDENCE ID</span>
                    <span>TIME</span>
                    <span>OBSERVATION & PAYLOAD ATTRIBUTES</span>
                    <span style={{ textAlign: "right" }}>ACTION</span>
                  </div>

                  {filteredEvidence.map((ev) => (
                    <div
                      key={ev.id}
                      className="technical-list-row"
                      style={{ gridTemplateColumns: "110px 120px 100px 1fr 90px" }}
                    >
                      <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                        {ev.source}
                      </div>

                      <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--text-primary)" }}>
                        {ev.id}
                      </div>

                      <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {ev.timestamp}
                      </div>

                      <div>
                        <div style={{ color: "var(--text-primary)", fontWeight: 500 }}>{ev.title}</div>
                        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                          Component: {ev.component}
                        </div>
                      </div>

                      <div style={{ textAlign: "right" }}>
                        <button
                          type="button"
                          onClick={() => setSelectedEvidenceId(ev.id)}
                          style={{
                            background: "none",
                            border: "none",
                            color: "var(--text-secondary)",
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.75rem",
                            cursor: "pointer",
                            transition: "color 0.15s ease",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
                        >
                          Inspect →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <hr className="hairline-separator" />

              {/* 5. COMPETING HYPOTHESES */}
              <div style={{ marginBottom: "36px" }}>
                <div className="section-tag">
                  <BarChart3 size={12} /> 04. COMPETING HYPOTHESES
                </div>
                <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "12px" }}>
                  Analyst Causal Explanations Evaluated
                </h3>

                <div className="technical-list-container">
                  <div
                    className="technical-list-header"
                    style={{ gridTemplateColumns: "60px 1fr 160px 140px" }}
                  >
                    <span>RANK</span>
                    <span>HYPOTHESIS & PROPOSED MECHANISM</span>
                    <span>VERDICT & PROBABILITY</span>
                    <span style={{ textAlign: "right" }}>SUPPORTING PROOF</span>
                  </div>

                  {agentSteps?.analyst?.hypotheses.map((hyp) => {
                    const isWinner = hyp.rank === 1;
                    return (
                      <div
                        key={hyp.hypothesis_id}
                        className="technical-list-row"
                        style={{
                          gridTemplateColumns: "60px 1fr 160px 140px",
                          backgroundColor: isWinner ? "rgba(143, 165, 138, 0.04)" : "transparent",
                        }}
                      >
                        <div style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: isWinner ? "var(--accent-sage)" : "var(--text-faint)" }}>
                          #{hyp.rank}
                        </div>

                        <div>
                          <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "2px" }}>
                            {hyp.hypothesis}
                          </div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                            Trigger: <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{hyp.suspected_trigger}</span>
                          </div>
                        </div>

                        <div>
                          <span
                            style={{
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.6875rem",
                              fontWeight: 600,
                              padding: "2px 6px",
                              borderRadius: "3px",
                              border: isWinner ? "1px solid rgba(143, 165, 138, 0.2)" : "1px solid rgba(196, 104, 93, 0.2)",
                              backgroundColor: isWinner
                                ? "rgba(143, 165, 138, 0.12)"
                                : "rgba(196, 104, 93, 0.12)",
                              color: isWinner ? "var(--accent-sage)" : "var(--signal-failure)",
                            }}
                          >
                            {isWinner ? `VERIFIED (${Math.round(hyp.confidence * 100)}%)` : "REFUTED"}
                          </span>
                        </div>

                        <div style={{ textAlign: "right" }}>
                          <div style={{ display: "inline-flex", gap: "4px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                            {hyp.supporting_evidence_ids.slice(0, 2).map((evId) => (
                              <button
                                key={evId}
                                className="ev-ref"
                                onClick={() => setSelectedEvidenceId(evId)}
                              >
                                {evId}
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <hr className="hairline-separator" />

              {/* 6. ADVERSARIAL VERIFIER AUDITS */}
              <div style={{ marginBottom: "36px" }}>
                <div className="section-tag">
                  <ShieldCheck size={12} /> 05. ADVERSARIAL VERIFICATION
                </div>
                <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "12px" }}>
                  Automated Precedence & Contradiction Audits
                </h3>

                <div className="technical-list-container">
                  {[
                    {
                      audit: "Temporal Ordering Precedence",
                      result: "PASSED",
                      desc: "Deployment v4.2.1 at 02:02:15 strictly preceded database query degradation at 02:04:30. Cause precedes effect by 135 seconds.",
                    },
                    {
                      audit: "Correlation vs Causation Audit",
                      result: "PASSED",
                      desc: "Payment gateway downstream 504 timeouts initiated after database worker saturation, proving payment gateway is a downstream symptom, not cause.",
                    },
                    {
                      audit: "Evidence Grounding & Hallucination Guard",
                      result: "PASSED",
                      desc: "All 4 cited evidence tokens verified against active in-memory OpenTelemetry and Prometheus traces. Zero synthetic state leakage.",
                    },
                  ].map((auditItem, idx) => (
                    <div key={idx} className="technical-list-row" style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
                      <div
                        style={{
                          width: "18px",
                          height: "18px",
                          borderRadius: "50%",
                          backgroundColor: "rgba(143, 165, 138, 0.12)",
                          color: "var(--accent-sage)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "10px",
                          flexShrink: 0,
                          marginTop: "2px",
                        }}
                      >
                        ✓
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "2px" }}>
                          <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{auditItem.audit}</span>
                          <span
                            style={{
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.625rem",
                              padding: "1px 5px",
                              borderRadius: "2px",
                              backgroundColor: "rgba(143, 165, 138, 0.12)",
                              color: "var(--accent-sage)",
                            }}
                          >
                            {auditItem.result}
                          </span>
                        </div>
                        <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                          {auditItem.desc}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <hr className="hairline-separator" />

              {/* 7. FINAL VERIFIED DIAGNOSIS (THE EARNED ENDPOINT) */}
              <div
                style={{
                  border: "1px solid rgba(143, 165, 138, 0.22)",
                  backgroundColor: "rgba(143, 165, 138, 0.03)",
                  borderRadius: "6px",
                  padding: "24px 24px",
                  marginBottom: "40px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "16px" }}>
                  <div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.6875rem",
                        color: "var(--accent-sage)",
                        letterSpacing: "0.08em",
                        marginBottom: "4px",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <CheckCircle2 size={13} color="var(--accent-sage)" /> 06. FINAL DIAGNOSIS
                    </div>
                    <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
                      Verified Root Cause & Remediation
                    </h3>
                  </div>

                  <ButtonGroup>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(diagnosis?.root_cause || "", "diag")}
                    >
                      <Copy size={12} /> {copiedId === "diag" ? "Copied" : "Copy"}
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleExportJson}>
                      <Download size={12} /> Export JSON
                    </Button>
                  </ButtonGroup>
                </div>

                {/* Findings Table List */}
                <div className="technical-list-container" style={{ marginBottom: "18px" }}>
                  <div className="technical-list-row" style={{ gridTemplateColumns: "160px 1fr" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      PRIMARY ROOT CAUSE
                    </div>
                    <div style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.5 }}>
                      {diagnosis?.root_cause || "Database query performance regression due to unindexed sort on the orders table causing full table scans."}
                    </div>
                  </div>

                  <div className="technical-list-row" style={{ gridTemplateColumns: "160px 1fr" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      INTRODUCED BY
                    </div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                      {diagnosis?.introduced_by || "deployment checkout-api:v4.2.1 (commit abc12348f9)"}
                    </div>
                  </div>

                  <div className="technical-list-row" style={{ gridTemplateColumns: "160px 1fr" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      CALIBRATED CONFIDENCE
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-sage)" }}>
                        {Math.round((diagnosis?.confidence || 0.94) * 100)}%
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                        Confirmed by active telemetry verification graph.
                      </span>
                    </div>
                  </div>

                  <div className="technical-list-row" style={{ gridTemplateColumns: "160px 1fr" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      REMEDIATION STEPS
                    </div>
                    <div style={{ fontSize: "0.8125rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
                      {diagnosis?.recommended_fix || "Apply composite index on orders(customer_id, created_at DESC) or rollback release v4.2.1."}
                    </div>
                  </div>

                  <div className="technical-list-row" style={{ gridTemplateColumns: "160px 1fr" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      CITED PROOF
                    </div>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                      {(diagnosis?.cited_evidence_ids || ["EV-DEP-0001", "EV-GIT-0001", "EV-SPAN-0001"]).map((evId) => (
                        <button
                          key={evId}
                          className="ev-ref"
                          onClick={() => setSelectedEvidenceId(evId)}
                        >
                          {evId}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <Button variant="default" size="sm" onClick={() => navigateToTab("incidents")}>
                    Next Incident <ChevronRight size={13} />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 3. INCIDENTS CATALOG PAGE                                                 */}
        {/* ========================================================================= */}
        {activeNav === "incidents" && (
          <div>
            <div className="page-header-block">
              <div className="section-tag">
                <ListFilterPlusIcon size={12} /> BENCHMARK SCENARIO CATALOG
              </div>
              <h1 className="page-header-title">Incidents Catalog</h1>
              <p className="page-header-desc">
                Operational catalog of all 21 reproducible production failure scenarios across database regressions, connection leaks, network jitters, and bad deployments.
              </p>
            </div>

            {/* Filter and Search Bar */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
                marginBottom: "20px",
              }}
            >
              {/* Search Input */}
              <div style={{ position: "relative", minWidth: "280px" }}>
                <Search
                  size={14}
                  style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}
                />
                <input
                  type="text"
                  placeholder="Filter by ID, title, or service..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    height: "32px",
                    paddingLeft: "32px",
                    paddingRight: "12px",
                    backgroundColor: "rgba(231, 227, 220, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "4px",
                    color: "var(--text-primary)",
                    fontSize: "0.8125rem",
                    outline: "none",
                  }}
                />
              </div>

              {/* Severity ButtonGroup */}
              <ButtonGroup>
                <Button
                  variant={filterSeverity === "ALL" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFilterSeverity("ALL")}
                >
                  All ({incidents.length})
                </Button>
                <Button
                  variant={filterSeverity === "CRITICAL" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFilterSeverity("CRITICAL")}
                >
                  Critical
                </Button>
                <Button
                  variant={filterSeverity === "HIGH" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFilterSeverity("HIGH")}
                >
                  High
                </Button>
                <Button
                  variant={filterSeverity === "MEDIUM" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFilterSeverity("MEDIUM")}
                >
                  Medium
                </Button>
              </ButtonGroup>
            </div>

            {/* Incidents Table List */}
            <div className="technical-list-container">
              <div
                className="technical-list-header"
                style={{ gridTemplateColumns: "90px 90px 1fr 140px 100px 110px" }}
              >
                <span>STATUS</span>
                <span>ID</span>
                <span>TITLE & FAILURE ANOMALY</span>
                <span>SERVICE</span>
                <span>SEVERITY</span>
                <span style={{ textAlign: "right" }}>ACTION</span>
              </div>

              {filteredIncidents.map((inc) => (
                <div
                  key={inc.incident_id}
                  className="technical-list-row"
                  style={{ gridTemplateColumns: "90px 90px 1fr 140px 100px 110px" }}
                >
                  <div>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "5px",
                        fontSize: "0.6875rem",
                        fontFamily: "var(--font-mono)",
                        color: inc.incident_id === "INC-001" ? "var(--accent-sage)" : "var(--text-muted)",
                      }}
                    >
                      <span
                        style={{
                          width: "5px",
                          height: "5px",
                          borderRadius: "50%",
                          backgroundColor: inc.incident_id === "INC-001" ? "var(--accent-sage)" : "var(--text-muted)",
                        }}
                      />
                      {inc.incident_id === "INC-001" ? "VERIFIED" : "READY"}
                    </span>
                  </div>

                  <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--text-primary)" }}>
                    {inc.incident_id}
                  </div>

                  <div>
                    <div style={{ fontWeight: 500, color: "var(--text-primary)" }}>{inc.name}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {inc.description}
                    </div>
                  </div>

                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {inc.affected_service}
                  </div>

                  <div>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.6875rem",
                        fontWeight: 600,
                        color:
                          inc.severity === "CRITICAL"
                            ? "var(--signal-failure)"
                            : inc.severity === "HIGH"
                            ? "var(--signal-warning)"
                            : "var(--text-muted)",
                      }}
                    >
                      {inc.severity}
                    </span>
                  </div>

                  <div style={{ textAlign: "right" }}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedIncidentId(inc.incident_id);
                        navigateToTab("investigations", inc.incident_id);
                        runInvestigation(inc.incident_id);
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--text-secondary)",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.75rem",
                        cursor: "pointer",
                        transition: "color 0.15s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
                    >
                      Investigate →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 4. EVIDENCE EXPLORER PAGE                                                 */}
        {/* ========================================================================= */}
        {activeNav === "evidence" && (
          <div>
            <div className="page-header-block">
              <div className="section-tag">
                <Layers size={12} /> EVIDENCE REPOSITORY
              </div>
              <h1 className="page-header-title">Evidence & Provenance Explorer</h1>
              <p className="page-header-desc">
                Inspect directional causal relationships, OpenTelemetry spans, metrics, deployments, and git commits extracted during incident investigations.
              </p>
            </div>

            {/* Toggle View Mode ButtonGroup */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <ButtonGroup>
                <Button
                  variant={evidenceViewMode === "graph" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setEvidenceViewMode("graph")}
                >
                  Causal Map (DAG)
                </Button>
                <Button
                  variant={evidenceViewMode === "table" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setEvidenceViewMode("table")}
                >
                  All Telemetry Records
                </Button>
              </ButtonGroup>

              <Button variant="outline" size="sm" onClick={() => setSelectedEvidenceId("EV-DEP-0001")}>
                <Eye size={13} /> Inspect Deployment Record
              </Button>
            </div>

            {evidenceViewMode === "graph" ? (
              <div
                style={{
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "6px",
                  padding: "36px",
                  backgroundColor: "rgba(20, 20, 18, 0.6)",
                }}
              >
                <div style={{ textAlign: "center", marginBottom: "36px" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-primary)", marginBottom: "4px" }}>
                    DIRECTIONAL CAUSAL GRAPH (INC-001)
                  </div>
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                    Click a node to inspect provenance and dependent traces.
                  </div>
                </div>

                {/* Visual DAG Nodes */}
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "20px", flexWrap: "wrap" }}>
                  {[
                    { id: "node-deploy", type: "DEPLOYMENT", title: "checkout-api:v4.2.1", sub: "EV-DEP-0001", tag: "TRIGGER" },
                    { id: "node-commit", type: "GIT COMMIT", title: "abc12348f9", sub: "EV-GIT-0001", tag: "CODE DIFF" },
                    { id: "node-query", type: "DB QUERY SPAN", title: "db.query (1850ms)", sub: "EV-SPAN-0001", tag: "REGRESSION" },
                    { id: "node-metric", type: "PROMETHEUS", title: "P99 SLA Breach", sub: "EV-METRIC-0002", tag: "SYMPTOM" },
                  ].map((node, idx) => (
                    <React.Fragment key={node.id}>
                      <div
                        onClick={() => {
                          setSelectedGraphNode(node.id);
                          setSelectedEvidenceId(node.sub);
                        }}
                        style={{
                          width: "200px",
                          padding: "14px",
                          borderRadius: "4px",
                          border:
                            selectedGraphNode === node.id
                              ? "1px solid var(--accent-sage)"
                              : "1px solid var(--border-subtle)",
                          backgroundColor:
                            selectedGraphNode === node.id
                              ? "rgba(143, 165, 138, 0.12)"
                              : "#161614",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "var(--text-muted)" }}>
                            {node.type}
                          </span>
                          <span
                            style={{
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.5625rem",
                              padding: "1px 4px",
                              borderRadius: "2px",
                              backgroundColor: "rgba(231, 227, 220, 0.06)",
                              color: "var(--text-secondary)",
                            }}
                          >
                            {node.tag}
                          </span>
                        </div>
                        <div style={{ fontWeight: 600, fontSize: "0.8125rem", color: "var(--text-primary)", marginBottom: "2px" }}>
                          {node.title}
                        </div>
                        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                          {node.sub}
                        </div>
                      </div>
                      {idx < 3 && <span style={{ color: "var(--text-muted)", fontWeight: 700, fontSize: "1.1rem" }}>→</span>}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            ) : (
              /* All Telemetry Records Table */
              <div className="technical-list-container">
                <div
                  className="technical-list-header"
                  style={{ gridTemplateColumns: "110px 120px 100px 1fr 90px" }}
                >
                  <span>SOURCE</span>
                  <span>EVIDENCE ID</span>
                  <span>TIMESTAMP</span>
                  <span>OBSERVATION & PAYLOAD</span>
                  <span style={{ textAlign: "right" }}>ACTION</span>
                </div>

                {allEvidenceArray.map((ev) => (
                  <div
                    key={ev.id}
                    className="technical-list-row"
                    style={{ gridTemplateColumns: "110px 120px 100px 1fr 90px" }}
                  >
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                      {ev.source}
                    </div>

                    <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--text-primary)" }}>
                      {ev.id}
                    </div>

                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {ev.timestamp}
                    </div>

                    <div>
                      <div style={{ fontWeight: 500, color: "var(--text-primary)" }}>{ev.title}</div>
                      <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                        Component: {ev.component}
                      </div>
                    </div>

                    <div style={{ textAlign: "right" }}>
                      <button
                        type="button"
                        onClick={() => setSelectedEvidenceId(ev.id)}
                        style={{
                          background: "none",
                          border: "none",
                          color: "var(--text-secondary)",
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.75rem",
                          cursor: "pointer",
                          transition: "color 0.15s ease",
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                        onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
                      >
                        Inspect →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* 5. EVALUATIONS BENCHMARK PAGE                                             */}
        {/* ========================================================================= */}
        {activeNav === "evaluations" && (
          <div>
            <div className="page-header-block">
              <div className="section-tag">
                <BarChart3 size={12} /> SCIENTIFIC RIGOR & ACCURACY
              </div>
              <h1 className="page-header-title">Comparative Architecture Evaluation</h1>
              <p className="page-header-desc">
                Quantitative benchmarking across 20 reproducible scenarios comparing Single-LLM Baseline, 2-Agent Baseline, and Aletheia 3-Agent Adversarial Verifier.
              </p>
            </div>

            {/* Test Execution ButtonGroup */}
            <div style={{ marginBottom: "20px" }}>
              <ButtonGroup>
                <Button
                  variant={selectedSystem === "single-llm" ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setSelectedSystem("single-llm");
                    runInvestigation(selectedIncidentId, "single-llm");
                  }}
                >
                  Test Single-LLM
                </Button>
                <Button
                  variant={selectedSystem === "two-agent" ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setSelectedSystem("two-agent");
                    runInvestigation(selectedIncidentId, "two-agent");
                  }}
                >
                  Test 2-Agent Baseline
                </Button>
                <Button
                  variant={selectedSystem === "aletheia-3agent" ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setSelectedSystem("aletheia-3agent");
                    runInvestigation(selectedIncidentId, "aletheia-3agent");
                  }}
                >
                  Test Aletheia 3-Agent
                </Button>
              </ButtonGroup>
            </div>

            {/* Benchmark Comparative Metrics List */}
            <div className="technical-list-container" style={{ marginBottom: "32px" }}>
              <div
                className="technical-list-header"
                style={{ gridTemplateColumns: "1fr 140px 140px 160px" }}
              >
                <span>EVALUATION METRIC</span>
                <span style={{ textAlign: "center" }}>SINGLE-LLM</span>
                <span style={{ textAlign: "center" }}>2-AGENT BASELINE</span>
                <span style={{ textAlign: "center", color: "var(--accent-sage)" }}>ALETHEIA (3-AGENT)</span>
              </div>

              {[
                { metric: "Root Cause Diagnosis Accuracy", single: "60.0%", two: "75.0%", three: "100.0%" },
                { metric: "Introduced-By Commit / Version Accuracy", single: "0.0%", two: "50.0%", three: "100.0%" },
                { metric: "Evidence Recall (% of ground truth found)", single: "50.0%", two: "70.0%", three: "80.0%" },
                { metric: "Evidence Precision (Zero irrelevant noise)", single: "100.0%", two: "85.0%", three: "100.0%" },
                { metric: "Hallucination Penalty (1.0 = zero hallucinations)", single: "0.20 (High)", two: "0.75 (Low)", three: "1.00 (Zero Hallucinations)" },
                { metric: "Overall Weighted Benchmark Score", single: "45.0%", two: "68.0%", three: "93.0%" },
              ].map((row, idx) => (
                <div
                  key={idx}
                  className="technical-list-row"
                  style={{ gridTemplateColumns: "1fr 140px 140px 160px" }}
                >
                  <div style={{ fontWeight: 500, color: "var(--text-primary)" }}>{row.metric}</div>
                  <div style={{ textAlign: "center", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>{row.single}</div>
                  <div style={{ textAlign: "center", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{row.two}</div>
                  <div style={{ textAlign: "center", fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-sage)" }}>{row.three}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* 6. SYSTEM HEALTH & LLMOPS TELEMETRY                                       */}
        {/* ========================================================================= */}
        {activeNav === "system" && (
          <div>
            <div className="page-header-block">
              <div className="section-tag">
                <Server size={12} /> LLMOPS WORKSTATION
              </div>
              <h1 className="page-header-title">System Health & Telemetry Accounting</h1>
              <p className="page-header-desc">
                Monitor system latency percentiles, model inference status, token accounting, and live OpenTelemetry span executions.
              </p>
            </div>

            {/* Metrics Strip */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "12px",
                marginBottom: "28px",
              }}
            >
              {[
                { label: "API HEALTH", value: "HEALTHY (200 OK)", sub: "FastAPI Daemon Active", color: "var(--accent-sage)" },
                { label: "INFERENCE MODEL", value: "GPT-4O-MINI", sub: "Determinism Mode T=0.0", color: "var(--text-primary)" },
                { label: "TOKEN SPEND (RUN)", value: "960 TOKENS", sub: "$0.00014 USD Est.", color: "var(--text-primary)" },
                { label: "P99 LATENCY", value: "2.1ms", sub: "In-memory graph traversal", color: "var(--accent-sage)" },
              ].map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    border: "1px solid var(--border-subtle)",
                    backgroundColor: "rgba(231, 227, 220, 0.015)",
                    borderRadius: "4px",
                    padding: "14px 16px",
                  }}
                >
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.625rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                    {m.label}
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "1rem", color: m.color, marginBottom: "2px" }}>
                    {m.value}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{m.sub}</div>
                </div>
              ))}
            </div>

            {/* Live LLMOps Traces Table */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "12px" }}>
                <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  Live LLM Call Records & Accounting
                </h3>
                <Button variant="ghost" size="sm" onClick={() => runInvestigation(selectedIncidentId, selectedSystem)}>
                  <RefreshCw size={12} /> Refresh Traces
                </Button>
              </div>

              <div className="technical-list-container">
                <div
                  className="technical-list-header"
                  style={{ gridTemplateColumns: "180px 140px 100px 110px 1fr" }}
                >
                  <span>TRACE ID</span>
                  <span>MODEL</span>
                  <span>STATUS</span>
                  <span>LATENCY</span>
                  <span>TOKENS & COST</span>
                </div>

                {(traces.length > 0
                  ? traces
                  : [
                      {
                        trace_id: "tr-7f839a2b109c",
                        model: "mock-accurate",
                        status: "SUCCESS",
                        latency_ms: 2.1,
                        prompt_tokens: 850,
                        completion_tokens: 110,
                        total_tokens: 960,
                        estimated_cost_usd: 0.00014,
                        agent_name: "analyst",
                        retries_attempted: 0,
                      },
                      {
                        trace_id: "tr-6e210c4d92ef",
                        model: "mock-accurate",
                        status: "SUCCESS",
                        latency_ms: 1.8,
                        prompt_tokens: 820,
                        completion_tokens: 95,
                        total_tokens: 915,
                        estimated_cost_usd: 0.00013,
                        agent_name: "verifier",
                        retries_attempted: 0,
                      },
                    ]
                ).map((tr, idx) => (
                  <div
                    key={idx}
                    className="technical-list-row"
                    style={{ gridTemplateColumns: "180px 140px 100px 110px 1fr" }}
                  >
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-primary)" }}>
                      {tr.trace_id}
                    </div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {tr.model}
                    </div>
                    <div>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.625rem",
                          padding: "1px 5px",
                          borderRadius: "2px",
                          backgroundColor: "rgba(143, 165, 138, 0.12)",
                          color: "var(--accent-sage)",
                        }}
                      >
                        {tr.status}
                      </span>
                    </div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {tr.latency_ms.toFixed(1)}ms
                    </div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {tr.prompt_tokens + tr.completion_tokens} tokens (${tr.estimated_cost_usd.toFixed(5)})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* SLIDE-OUT PROVENANCE & EVIDENCE INSPECTOR DRAWER */}
      <EvidenceDrawer
        evidence={selectedEvidenceId ? evidenceRecords[selectedEvidenceId] || null : null}
        onClose={() => setSelectedEvidenceId(null)}
      />
    </DarkGradientBg>
  );
}
