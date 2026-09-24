"""Evaluation harness executing and scoring diagnostic systems against ground truth."""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from aletheia.evaluation.loader import load_ground_truth, load_incident_telemetry
from aletheia.evaluation.metrics import (
    calculate_overall_score,
    score_affected_service,
    score_evidence_citations,
    score_introduced_by,
    score_root_cause,
)
from aletheia.evaluation.models import DiagnosticSystem, EvaluationReport

logger = logging.getLogger("aletheia.eval.harness")


class EvaluationHarness:
    """Rigorous evaluation harness measuring diagnostic accuracy and evidence discipline."""

    def __init__(self, output_dir: Optional[Path] = None):
        self._reports: Dict[str, EvaluationReport] = {}
        self.output_dir = output_dir or (Path(__file__).resolve().parent.parent.parent.parent / "eval_results")

    def evaluate(
        self,
        system: DiagnosticSystem,
        incident_id: str = "INC-001",
    ) -> EvaluationReport:
        """Run an end-to-end evaluation of a diagnostic system on an incident.

        Strict Isolation Guarantee:
        Ground truth is loaded exclusively within this harness to compute post-diagnosis metrics.
        The diagnostic system receives only observable evidence items and timeline.
        """
        # 1. Load Ground Truth for scoring
        ground_truth = load_ground_truth(incident_id)

        # 2. Load Observable Evidence (untainted by ground truth)
        alert_desc, evidence_items, timeline = load_incident_telemetry(incident_id)

        # 3. Execute Diagnostic System
        logger.info(f"Starting evaluation of system '{system.name}' on incident '{incident_id}'...")
        start_time = time.perf_counter()
        diagnosis = system.diagnose(
            incident_id=incident_id,
            alert_description=alert_desc,
            evidence_items=evidence_items,
            timeline=timeline,
        )
        wall_time = time.perf_counter() - start_time

        # 4. Score Metrics Against Ground Truth
        rc_score = score_root_cause(diagnosis, ground_truth)
        intro_score = score_introduced_by(diagnosis, ground_truth)
        svc_score = score_affected_service(diagnosis, ground_truth)
        recall_score, prec_score, hall_score = score_evidence_citations(
            diagnosis, ground_truth, evidence_items
        )

        overall_score = calculate_overall_score(
            root_cause_score=rc_score,
            introduced_by_score=intro_score,
            service_score=svc_score,
            evidence_recall_score=recall_score,
            evidence_precision_score=prec_score,
            hallucination_score=hall_score,
        )

        # 5. Extract Execution Resources
        usage = diagnosis.usage_metadata or {}
        token_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        cost = usage.get("estimated_cost_usd", 0.0)
        measured_latency = usage.get("latency_seconds", round(wall_time, 4))

        # 6. Generate Report
        report_id = f"EVAL-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        summary = (
            f"Evaluated '{system.name}' on {incident_id}: Overall Score: {overall_score:.1%} | "
            f"Root Cause: {rc_score.score:.1%} | Attribution: {intro_score.score:.1%} | "
            f"Evidence Recall: {recall_score.score:.1%} | Hallucinations: {hall_score.details.get('count', 0)}"
        )

        report = EvaluationReport(
            report_id=report_id,
            incident_id=incident_id,
            system_name=system.name,
            timestamp=datetime.now(timezone.utc),
            root_cause_score=rc_score,
            introduced_by_score=intro_score,
            service_score=svc_score,
            evidence_recall_score=recall_score,
            evidence_precision_score=prec_score,
            hallucination_score=hall_score,
            overall_score=overall_score,
            latency_seconds=measured_latency,
            token_usage=token_usage,
            estimated_cost_usd=cost,
            diagnosis=diagnosis,
            summary=summary,
        )

        self._reports[report_id] = report
        return report

    def get_report(self, report_id: str) -> Optional[EvaluationReport]:
        """Fetch report by ID."""
        return self._reports.get(report_id)

    def list_reports(self) -> List[EvaluationReport]:
        """List all generated reports in reverse chronological order."""
        return sorted(self._reports.values(), key=lambda r: r.timestamp, reverse=True)

    def save_report(self, report: EvaluationReport) -> Path:
        """Persist report JSON to results directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.output_dir / f"{report.report_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        return file_path


# Global in-memory harness instance
_GLOBAL_HARNESS: Optional[EvaluationHarness] = None


def get_evaluation_harness() -> EvaluationHarness:
    """Return singleton evaluation harness instance."""
    global _GLOBAL_HARNESS
    if _GLOBAL_HARNESS is None:
        _GLOBAL_HARNESS = EvaluationHarness()
    return _GLOBAL_HARNESS
