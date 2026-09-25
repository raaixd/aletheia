"""Structured LLM and Agent execution traces, token/cost accounting, and telemetry."""

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("aletheia.reliability.traces")


class LLMCallTrace(BaseModel):
    """Structured record of an individual LLM or agent execution step."""
    model_config = ConfigDict(extra="ignore")

    trace_id: str
    session_id: Optional[str] = None
    incident_id: Optional[str] = None
    agent_name: str  # e.g. "Investigator", "Analyst", "Verifier", "SingleLLMBaseline"
    model: str = "mock-eval-model"
    model_version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    status: str = "success"  # "success", "retried", "rate_limited", "timeout", "error"
    retries_attempted: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMOpsMetricsSummary(BaseModel):
    """Aggregated operational metrics for LLM calls and multi-agent runs."""
    model_config = ConfigDict(extra="ignore")

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    retried_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost_usd: float = 0.0
    mean_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    calls_by_agent: Dict[str, int] = Field(default_factory=dict)
    calls_by_model: Dict[str, int] = Field(default_factory=dict)
    errors_by_type: Dict[str, int] = Field(default_factory=dict)


class TraceRecorder:
    """Thread-safe collector for structured LLM execution traces with file persistence."""

    def __init__(self, persistence_path: Optional[str] = None):
        self._lock = threading.Lock()
        self._traces: List[LLMCallTrace] = []
        if persistence_path:
            self.persistence_path = Path(persistence_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.persistence_path = base_dir / "eval_results" / "traces" / "llm_traces.jsonl"
        self._ensure_dir()

    def _ensure_dir(self):
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(f"Could not create traces directory: {exc}")

    def record_trace(self, trace: LLMCallTrace) -> None:
        """Record an execution trace in memory and append to jsonl file."""
        with self._lock:
            self._traces.append(trace)
            try:
                with open(self.persistence_path, "a", encoding="utf-8") as f:
                    f.write(trace.model_dump_json() + "\n")
            except Exception as exc:
                logger.warning(f"Failed to persist trace {trace.trace_id}: {exc}")

    def get_traces(
        self,
        incident_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[LLMCallTrace]:
        """Query traces with optional filtering."""
        with self._lock:
            filtered = self._traces[:]

        if incident_id:
            filtered = [t for t in filtered if t.incident_id == incident_id]
        if agent_name:
            filtered = [t for t in filtered if t.agent_name.lower() == agent_name.lower()]
        if status:
            filtered = [t for t in filtered if t.status.lower() == status.lower()]

        # Return latest traces first
        return sorted(filtered, key=lambda t: t.timestamp, reverse=True)[:limit]

    def get_metrics_summary(self) -> LLMOpsMetricsSummary:
        """Compute aggregate summary metrics across all recorded traces."""
        with self._lock:
            traces = self._traces[:]

        if not traces:
            return LLMOpsMetricsSummary()

        total = len(traces)
        success = sum(1 for t in traces if t.status in ("success", "retried"))
        retried = sum(1 for t in traces if t.retries_attempted > 0)
        failed = sum(1 for t in traces if t.status in ("error", "timeout", "rate_limited"))

        prompt_toks = sum(t.prompt_tokens for t in traces)
        comp_toks = sum(t.completion_tokens for t in traces)
        tot_toks = sum(t.total_tokens for t in traces)
        tot_cost = sum(t.estimated_cost_usd for t in traces)

        latencies = sorted(t.latency_ms for t in traces)
        mean_lat = sum(latencies) / total
        p95_idx = int(0.95 * total)
        p95_lat = latencies[min(p95_idx, total - 1)]

        by_agent: Dict[str, int] = {}
        by_model: Dict[str, int] = {}
        err_types: Dict[str, int] = {}

        for t in traces:
            by_agent[t.agent_name] = by_agent.get(t.agent_name, 0) + 1
            by_model[t.model] = by_model.get(t.model, 0) + 1
            if t.error_message:
                err_key = t.error_message.split(":")[0][:50]
                err_types[err_key] = err_types.get(err_key, 0) + 1

        return LLMOpsMetricsSummary(
            total_calls=total,
            successful_calls=success,
            failed_calls=failed,
            retried_calls=retried,
            total_prompt_tokens=prompt_toks,
            total_completion_tokens=comp_toks,
            total_tokens=tot_toks,
            total_estimated_cost_usd=round(tot_cost, 6),
            mean_latency_ms=round(mean_lat, 2),
            p95_latency_ms=round(p95_lat, 2),
            calls_by_agent=by_agent,
            calls_by_model=by_model,
            errors_by_type=err_types,
        )

    def clear(self) -> None:
        """Clear recorded traces (useful for tests)."""
        with self._lock:
            self._traces.clear()
            if self.persistence_path.exists():
                try:
                    self.persistence_path.unlink()
                except Exception:
                    pass


# Singleton instance
_global_trace_recorder: Optional[TraceRecorder] = None


def get_trace_recorder() -> TraceRecorder:
    """Get or create singleton TraceRecorder."""
    global _global_trace_recorder
    if _global_trace_recorder is None:
        _global_trace_recorder = TraceRecorder()
    return _global_trace_recorder
