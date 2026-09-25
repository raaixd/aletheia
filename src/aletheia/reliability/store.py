"""Evaluation Run Storage and Experiment Comparison for LLMOps."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from aletheia.evaluation.models import ComparativeBenchmarkReport, EvaluationReport

logger = logging.getLogger("aletheia.reliability.store")


class EvaluationComparisonDiff(BaseModel):
    """Structured comparison between two evaluation runs or benchmarks."""
    model_config = ConfigDict(extra="ignore")

    run_a_id: str
    run_b_id: str
    system_a_name: str
    system_b_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    overall_score_delta: float = 0.0
    root_cause_accuracy_delta: float = 0.0
    evidence_recall_delta: float = 0.0
    evidence_precision_delta: float = 0.0
    hallucination_rate_delta: float = 0.0
    latency_delta_seconds: float = 0.0
    cost_delta_usd: float = 0.0

    comparison_summary: str = ""
    detailed_metrics: Dict[str, Any] = Field(default_factory=dict)


class EvaluationStore:
    """Persistent storage and comparison engine for evaluation runs and benchmarks."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            self.base_dir = repo_root / "eval_results"

        self.runs_dir = self.base_dir / "runs"
        self.benchmarks_dir = self.base_dir / "benchmarks"
        self._ensure_dirs()

    def _ensure_dirs(self):
        try:
            self.runs_dir.mkdir(parents=True, exist_ok=True)
            self.benchmarks_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(f"Failed to create evaluation storage directories: {exc}")

    # ==================== Run Storage ====================

    def save_run(self, report: EvaluationReport) -> Path:
        """Persist an individual evaluation report to JSON."""
        file_path = self.runs_dir / f"{report.report_id}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
        except Exception as exc:
            logger.error(f"Failed to save run {report.report_id}: {exc}")
        return file_path

    def get_run(self, report_id: str) -> Optional[EvaluationReport]:
        """Load an evaluation report by ID."""
        file_path = self.runs_dir / f"{report_id}.json"
        if not file_path.exists():
            # Check without extension if user supplied it
            if not report_id.endswith(".json"):
                alt_path = self.runs_dir / f"{report_id}.json"
            else:
                alt_path = self.runs_dir / report_id
            if not alt_path.exists():
                return None
            file_path = alt_path

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return EvaluationReport.model_validate(data)
        except Exception as exc:
            logger.error(f"Failed to load run {report_id}: {exc}")
            return None

    def list_runs(
        self,
        incident_id: Optional[str] = None,
        system_name: Optional[str] = None,
        limit: int = 50,
    ) -> List[EvaluationReport]:
        """List stored evaluation runs with optional filters."""
        reports: List[EvaluationReport] = []
        if not self.runs_dir.exists():
            return reports

        for fpath in sorted(self.runs_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    rep = EvaluationReport.model_validate(json.load(f))
                if incident_id and rep.incident_id != incident_id:
                    continue
                if system_name and system_name.lower() not in rep.system_name.lower():
                    continue
                reports.append(rep)
                if len(reports) >= limit:
                    break
            except Exception:
                continue

        return reports

    # ==================== Benchmark Storage ====================

    def save_benchmark(self, benchmark: ComparativeBenchmarkReport) -> Path:
        """Persist a multi-system comparative benchmark report."""
        file_path = self.benchmarks_dir / f"{benchmark.benchmark_id}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(benchmark.model_dump_json(indent=2))
        except Exception as exc:
            logger.error(f"Failed to save benchmark {benchmark.benchmark_id}: {exc}")
        return file_path

    def get_benchmark(self, benchmark_id: str) -> Optional[ComparativeBenchmarkReport]:
        """Load a benchmark report by ID."""
        file_path = self.benchmarks_dir / f"{benchmark_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ComparativeBenchmarkReport.model_validate(data)
        except Exception as exc:
            logger.error(f"Failed to load benchmark {benchmark_id}: {exc}")
            return None

    def list_benchmarks(self, limit: int = 20) -> List[ComparativeBenchmarkReport]:
        """List stored comparative benchmark reports."""
        benchmarks: List[ComparativeBenchmarkReport] = []
        if not self.benchmarks_dir.exists():
            return benchmarks

        for fpath in sorted(self.benchmarks_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    benchmarks.append(ComparativeBenchmarkReport.model_validate(json.load(f)))
                if len(benchmarks) >= limit:
                    break
            except Exception:
                continue

        return benchmarks

    # ==================== Run & Experiment Comparison ====================

    def compare_runs(self, report_a: EvaluationReport, report_b: EvaluationReport) -> EvaluationComparisonDiff:
        """Compare two evaluation runs and compute performance deltas."""
        score_delta = round(report_b.overall_score - report_a.overall_score, 4)
        rc_delta = round(report_b.root_cause_score.score - report_a.root_cause_score.score, 4)
        rec_delta = round(report_b.evidence_recall_score.score - report_a.evidence_recall_score.score, 4)
        prec_delta = round(report_b.evidence_precision_score.score - report_a.evidence_precision_score.score, 4)

        # Hallucination delta: (1.0 - score) is hallucination rate
        hall_a = 1.0 - report_a.hallucination_score.score
        hall_b = 1.0 - report_b.hallucination_score.score
        hall_delta = round(hall_b - hall_a, 4)

        lat_delta = round(report_b.latency_seconds - report_a.latency_seconds, 4)
        cost_delta = round(report_b.estimated_cost_usd - report_a.estimated_cost_usd, 6)

        summary = (
            f"Compared '{report_b.system_name}' against '{report_a.system_name}' on {report_b.incident_id}: "
            f"Overall Score Δ: {score_delta:+.1%}, Root Cause Δ: {rc_delta:+.1%}, "
            f"Recall Δ: {rec_delta:+.1%}, Hallucination Δ: {hall_delta:+.1%}"
        )

        return EvaluationComparisonDiff(
            run_a_id=report_a.report_id,
            run_b_id=report_b.report_id,
            system_a_name=report_a.system_name,
            system_b_name=report_b.system_name,
            overall_score_delta=score_delta,
            root_cause_accuracy_delta=rc_delta,
            evidence_recall_delta=rec_delta,
            evidence_precision_delta=prec_delta,
            hallucination_rate_delta=hall_delta,
            latency_delta_seconds=lat_delta,
            cost_delta_usd=cost_delta,
            comparison_summary=summary,
            detailed_metrics={
                "system_a": {
                    "overall_score": report_a.overall_score,
                    "root_cause_score": report_a.root_cause_score.score,
                    "latency": report_a.latency_seconds,
                    "tokens": report_a.token_usage,
                },
                "system_b": {
                    "overall_score": report_b.overall_score,
                    "root_cause_score": report_b.root_cause_score.score,
                    "latency": report_b.latency_seconds,
                    "tokens": report_b.token_usage,
                },
            },
        )


_global_eval_store: Optional[EvaluationStore] = None


def get_evaluation_store() -> EvaluationStore:
    """Get or create singleton EvaluationStore."""
    global _global_eval_store
    if _global_eval_store is None:
        _global_eval_store = EvaluationStore()
    return _global_eval_store
