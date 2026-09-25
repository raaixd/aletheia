"""Data models for Aletheia incident diagnostic outputs, evaluation metrics, and reports."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, ConfigDict, Field

from aletheia.evidence.events import Timeline
from aletheia.evidence.schema import EvidenceItem


class DiagnosisResult(BaseModel):
    """Structured diagnosis output produced by any diagnostic system (LLM baseline or agent swarm)."""
    model_config = ConfigDict(extra="ignore")

    incident_id: str = Field(..., description="ID of the investigated incident")
    root_cause: str = Field(..., description="Summary or hypothesis of the root cause")
    root_cause_category: Optional[str] = Field(
        None,
        description="Standardized category, e.g. slow_database_query, memory_leak, etc.",
    )
    suspected_component: Optional[str] = Field(
        None,
        description="Specific subsystem, component, or database table at fault",
    )
    introduced_by: Optional[str] = Field(
        None,
        description="Commit SHA or deployment version that introduced the incident",
    )
    affected_service: Optional[str] = Field(
        None,
        description="Primary affected service name",
    )
    explanation: str = Field(
        default="",
        description="Detailed step-by-step reasoning supporting the conclusion",
    )
    cited_evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of exact Evidence IDs cited from the provided context",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="System confidence score between 0.0 and 1.0",
    )
    recommended_fix: str = Field(
        default="",
        description="Recommended remediation, mitigation, or rollback step",
    )
    raw_response: Optional[str] = Field(
        None,
        description="Raw completion text from the underlying model",
    )
    usage_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Token counts, latency, and model metadata",
    )


class MetricScore(BaseModel):
    """Evaluation score for a specific metric dimension."""
    metric_name: str
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score [0.0 - 1.0]")
    passed: bool = Field(..., description="Whether the metric threshold was achieved")
    details: Dict[str, Any] = Field(default_factory=dict)
    explanation: str = Field(default="")


class EvaluationReport(BaseModel):
    """Comprehensive evaluation report measuring a diagnostic system against ground truth."""
    model_config = ConfigDict(extra="ignore")

    report_id: str
    incident_id: str
    system_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Metric Scores
    root_cause_score: MetricScore
    introduced_by_score: MetricScore
    service_score: MetricScore
    evidence_recall_score: MetricScore
    evidence_precision_score: MetricScore
    hallucination_score: MetricScore

    # Composite & Resources
    overall_score: float = Field(..., ge=0.0, le=1.0)
    latency_seconds: float = Field(..., ge=0.0)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    estimated_cost_usd: float = Field(default=0.0)

    # Diagnosis payload
    diagnosis: DiagnosisResult
    summary: str = ""

    def format_ascii(self) -> str:
        """Render a clean ASCII scorecard for CLI inspection."""
        lines = [
            "=" * 72,
            f"ALETHEIA EVALUATION REPORT: {self.report_id}",
            "=" * 72,
            f"Incident ID   : {self.incident_id}",
            f"System Evaluated: {self.system_name}",
            f"Evaluated At  : {self.timestamp.isoformat()}",
            f"Overall Score : {self.overall_score:.1%} ({'PASS' if self.overall_score >= 0.70 else 'FAIL'})",
            "-" * 72,
            f"{'METRIC':<28} | {'SCORE':<7} | {'STATUS':<6} | {'DETAILS'}",
            "-" * 72,
            f"{'Root Cause Accuracy':<28} | {self.root_cause_score.score:<7.1%} | {'PASS' if self.root_cause_score.passed else 'FAIL':<6} | {self.root_cause_score.explanation}",
            f"{'Introduced By (Attribution)':<28} | {self.introduced_by_score.score:<7.1%} | {'PASS' if self.introduced_by_score.passed else 'FAIL':<6} | {self.introduced_by_score.explanation}",
            f"{'Affected Service/Component':<28} | {self.service_score.score:<7.1%} | {'PASS' if self.service_score.passed else 'FAIL':<6} | {self.service_score.explanation}",
            f"{'Evidence Citation Recall':<28} | {self.evidence_recall_score.score:<7.1%} | {'PASS' if self.evidence_recall_score.passed else 'FAIL':<6} | {self.evidence_recall_score.explanation}",
            f"{'Evidence Citation Precision':<28} | {self.evidence_precision_score.score:<7.1%} | {'PASS' if self.evidence_precision_score.passed else 'FAIL':<6} | {self.evidence_precision_score.explanation}",
            f"{'Hallucination Penalty':<28} | {self.hallucination_score.score:<7.1%} | {'PASS' if self.hallucination_score.passed else 'FAIL':<6} | {self.hallucination_score.explanation}",
            "-" * 72,
            "RESOURCE METRICS:",
            f"  - Latency       : {self.latency_seconds:.3f}s",
            f"  - Input Tokens  : {self.token_usage.get('prompt_tokens', 0)}",
            f"  - Output Tokens : {self.token_usage.get('completion_tokens', 0)}",
            f"  - Total Tokens  : {self.token_usage.get('total_tokens', 0)}",
            f"  - Estimated Cost: ${self.estimated_cost_usd:.6f}",
            "=" * 72,
        ]
        return "\n".join(lines)


@runtime_checkable
class DiagnosticSystem(Protocol):
    """Interface required for any diagnostic system evaluated by the harness."""
    name: str

    def diagnose(
        self,
        incident_id: str,
        alert_description: str,
        evidence_items: List[EvidenceItem],
        timeline: Timeline,
    ) -> DiagnosisResult:
        """Analyze evidence and return a structured diagnosis."""
        ...


class SystemBenchmarkSummary(BaseModel):
    """Aggregate benchmark metrics for a single diagnostic system across multiple incidents."""
    model_config = ConfigDict(extra="ignore")

    system_name: str
    total_incidents: int = 0
    passed_evaluations: int = 0
    failed_evaluations: int = 0
    overall_failure_rate: float = 0.0

    mean_overall_score: float = 0.0
    mean_root_cause_accuracy: float = 0.0
    top_3_hypothesis_accuracy: float = 0.0
    mean_evidence_recall: float = 0.0
    mean_evidence_precision: float = 0.0

    hallucination_rate: float = 0.0  # % of runs citing >= 1 hallucinated ID
    false_positive_rate: float = 0.0  # % of runs with wrong root cause
    verification_success_rate: float = 0.0  # % of verified diagnoses
    tool_api_failure_rate: float = 0.0

    mean_latency_seconds: float = 0.0
    total_tokens: int = 0
    total_estimated_cost_usd: float = 0.0


class ComparativeBenchmarkReport(BaseModel):
    """Comparative benchmark results across Baseline A, Baseline B, and Aletheia 3-Agent system."""
    model_config = ConfigDict(extra="ignore")

    benchmark_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    incidents_evaluated: List[str]
    system_summaries: Dict[str, SystemBenchmarkSummary]
    individual_reports: Dict[str, List[EvaluationReport]] = Field(default_factory=dict)
    comparative_summary: str = ""

    def format_markdown_table(self) -> str:
        """Render a comparative markdown table for documentation and reports."""
        lines = [
            "| Metric | Baseline A (Single-LLM) | Baseline B (2-Agent) | Aletheia (3-Agent) |",
            "|---|---|---|---|",
        ]
        systems = list(self.system_summaries.keys())
        s1 = self.system_summaries.get(systems[0]) if len(systems) > 0 else None
        s2 = self.system_summaries.get(systems[1]) if len(systems) > 1 else None
        s3 = self.system_summaries.get(systems[2]) if len(systems) > 2 else None

        def fmt_row(label: str, getter):
            v1 = getter(s1) if s1 else "N/A"
            v2 = getter(s2) if s2 else "N/A"
            v3 = getter(s3) if s3 else "N/A"
            return f"| **{label}** | {v1} | {v2} | {v3} |"

        lines.append(fmt_row("Root-Cause Accuracy", lambda s: f"{s.mean_root_cause_accuracy:.1%}"))
        lines.append(fmt_row("Top-3 Hypothesis Accuracy", lambda s: f"{s.top_3_hypothesis_accuracy:.1%}"))
        lines.append(fmt_row("Evidence Recall", lambda s: f"{s.mean_evidence_recall:.1%}"))
        lines.append(fmt_row("Evidence Precision", lambda s: f"{s.mean_evidence_precision:.1%}"))
        lines.append(fmt_row("Hallucination Rate", lambda s: f"{s.hallucination_rate:.1%}"))
        lines.append(fmt_row("False-Positive Rate", lambda s: f"{s.false_positive_rate:.1%}"))
        lines.append(fmt_row("Verification Success", lambda s: f"{s.verification_success_rate:.1%}"))
        lines.append(fmt_row("Overall Composite Score", lambda s: f"{s.mean_overall_score:.1%}"))
        lines.append(fmt_row("Mean Latency", lambda s: f"{s.mean_latency_seconds:.3f}s"))
        lines.append(fmt_row("Total Estimated Cost", lambda s: f"${s.total_estimated_cost_usd:.4f}"))
        lines.append(fmt_row("Overall Failure Rate", lambda s: f"{s.overall_failure_rate:.1%}"))

        return "\n".join(lines)
