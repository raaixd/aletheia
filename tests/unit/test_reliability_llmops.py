"""Unit and integration tests for Phase 8 Reliability and LLMOps subsystems."""

import time
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from aletheia.api.app import app
from aletheia.evaluation.llm.client import LLMAPIError, LLMTimeoutError
from aletheia.evaluation.models import DiagnosisResult, EvaluationReport, MetricScore
from aletheia.reliability.resilience import execute_with_retry, is_retryable_error, retry_with_backoff
from aletheia.reliability.store import EvaluationStore
from aletheia.reliability.traces import LLMCallTrace, TraceRecorder


def test_trace_recorder_records_and_aggregates(tmp_path):
    recorder = TraceRecorder(persistence_path=str(tmp_path / "traces.jsonl"))

    trace1 = LLMCallTrace(
        trace_id="t1",
        incident_id="INC-001",
        agent_name="Analyst",
        model="gpt-4o-mini",
        latency_ms=120.0,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        estimated_cost_usd=0.0001,
        status="success",
    )
    trace2 = LLMCallTrace(
        trace_id="t2",
        incident_id="INC-001",
        agent_name="Verifier",
        model="gpt-4o-mini",
        latency_ms=200.0,
        prompt_tokens=150,
        completion_tokens=60,
        total_tokens=210,
        estimated_cost_usd=0.00015,
        status="retried",
        retries_attempted=1,
    )

    recorder.record_trace(trace1)
    recorder.record_trace(trace2)

    traces = recorder.get_traces(incident_id="INC-001")
    assert len(traces) == 2

    metrics = recorder.get_metrics_summary()
    assert metrics.total_calls == 2
    assert metrics.successful_calls == 2
    assert metrics.retried_calls == 1
    assert metrics.total_tokens == 360
    assert metrics.calls_by_agent.get("Analyst") == 1
    assert metrics.calls_by_agent.get("Verifier") == 1
    assert metrics.mean_latency_ms == 160.0


def test_retry_with_backoff_transient_rate_limit_and_timeout():
    attempts = {"count": 0}

    def flaky_service():
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise LLMTimeoutError("LLM API request timed out after 30s")
        elif attempts["count"] == 2:
            raise LLMAPIError("LLM API HTTP error 429: Rate limit exceeded")
        return "success_after_retry"

    retries_recorded = []

    def hook(attempt, exc, backoff):
        retries_recorded.append((attempt, type(exc)))

    result = execute_with_retry(
        flaky_service,
        max_retries=3,
        initial_backoff=0.01,
        backoff_factor=1.5,
        retry_hook=hook,
    )

    assert result == "success_after_retry"
    assert attempts["count"] == 3
    assert len(retries_recorded) == 2
    assert retries_recorded[0][0] == 1
    assert retries_recorded[1][0] == 2


def test_retry_with_backoff_fatal_non_retryable_fails_immediately():
    attempts = {"count": 0}

    def fatal_service():
        attempts["count"] += 1
        raise ValueError("Invalid configuration - do not retry")

    with pytest.raises(ValueError, match="Invalid configuration"):
        execute_with_retry(
            fatal_service,
            max_retries=3,
            initial_backoff=0.01,
        )

    # Must fail immediately on attempt 1 without retry
    assert attempts["count"] == 1


def test_evaluation_store_save_get_and_compare(tmp_path):
    store = EvaluationStore(base_dir=str(tmp_path))

    dummy_diag = DiagnosisResult(
        incident_id="INC-001",
        root_cause="Database regression",
        cited_evidence_ids=["EV-001"],
    )

    report_a = EvaluationReport(
        report_id="EVAL-A",
        incident_id="INC-001",
        system_name="Baseline-A",
        timestamp=datetime.now(timezone.utc),
        root_cause_score=MetricScore(metric_name="rc", score=0.5, passed=False),
        introduced_by_score=MetricScore(metric_name="intro", score=0.0, passed=False),
        service_score=MetricScore(metric_name="svc", score=1.0, passed=True),
        evidence_recall_score=MetricScore(metric_name="rec", score=0.5, passed=False),
        evidence_precision_score=MetricScore(metric_name="prec", score=0.6, passed=False),
        hallucination_score=MetricScore(metric_name="hall", score=0.5, passed=False),
        overall_score=0.45,
        latency_seconds=1.2,
        diagnosis=dummy_diag,
    )

    report_b = EvaluationReport(
        report_id="EVAL-B",
        incident_id="INC-001",
        system_name="Aletheia-3Agent",
        timestamp=datetime.now(timezone.utc),
        root_cause_score=MetricScore(metric_name="rc", score=1.0, passed=True),
        introduced_by_score=MetricScore(metric_name="intro", score=1.0, passed=True),
        service_score=MetricScore(metric_name="svc", score=1.0, passed=True),
        evidence_recall_score=MetricScore(metric_name="rec", score=1.0, passed=True),
        evidence_precision_score=MetricScore(metric_name="prec", score=1.0, passed=True),
        hallucination_score=MetricScore(metric_name="hall", score=1.0, passed=True),
        overall_score=1.0,
        latency_seconds=0.8,
        diagnosis=dummy_diag,
    )

    store.save_run(report_a)
    store.save_run(report_b)

    loaded_a = store.get_run("EVAL-A")
    assert loaded_a is not None
    assert loaded_a.system_name == "Baseline-A"

    runs = store.list_runs(incident_id="INC-001")
    assert len(runs) == 2

    # Compare run A and run B
    diff = store.compare_runs(report_a, report_b)
    assert diff.overall_score_delta == 0.55
    assert diff.root_cause_accuracy_delta == 0.5
    assert diff.hallucination_rate_delta == -0.5  # Hallucination decreased
    assert diff.latency_delta_seconds == -0.4  # Latency improved


def test_llmops_api_endpoints():
    client = TestClient(app)

    # 1. Traces endpoint
    resp = client.get("/api/v1/llmops/traces")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # 2. Metrics endpoint
    resp = client.get("/api/v1/llmops/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_calls" in data
    assert "mean_latency_ms" in data

    # 3. Runs endpoint
    resp = client.get("/api/v1/llmops/runs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # 4. Benchmarks endpoint
    resp = client.get("/api/v1/llmops/benchmarks")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # 5. Nonexistent run 404
    resp = client.get("/api/v1/llmops/runs/NONEXISTENT-RUN")
    assert resp.status_code == 404

    # 6. Nonexistent benchmark 404
    resp = client.get("/api/v1/llmops/benchmarks/NONEXISTENT-BENCH")
    assert resp.status_code == 404
