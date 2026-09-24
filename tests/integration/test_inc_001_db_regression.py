"""Integration tests verifying reproducible failure injection for INC-001."""

import pytest
from aletheia.observability.tracing import get_memory_exporter
from simulator.failure_injection.manager import failure_manager


@pytest.fixture(autouse=True)
def clean_failures():
    """Ensure failure manager is reset before and after each test."""
    failure_manager.reset()
    yield
    failure_manager.reset()


@pytest.mark.integration
def test_inc_001_database_query_regression_reproducibility(checkout_client):
    """Verify INC-001 causes measurable, reproducible latency spike and traces."""
    memory_exporter = get_memory_exporter()

    # Step 1: Measure Baseline Performance
    baseline_res = checkout_client.get("/api/orders")
    assert baseline_res.status_code == 200
    baseline_latency_ms = float(baseline_res.headers["X-Response-Time-Ms"])
    assert baseline_latency_ms < 50.0, f"Expected baseline < 50ms, got {baseline_latency_ms}ms"

    # Step 2: Inject Failure INC-001 with 120ms simulated regression for fast, deterministic test
    injected_latency = 120.0
    inject_res = checkout_client.post(
        "/api/simulator/inject",
        json={"incident_id": "INC-001", "parameters": {"latency_ms": injected_latency}},
    )
    assert inject_res.status_code == 200
    assert inject_res.json()["incident_id"] == "INC-001"

    # Verify status endpoint reflects active incident
    status_res = checkout_client.get("/api/simulator/incidents")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["total_active"] == 1
    assert "INC-001" in status_data["active_incidents"]

    if memory_exporter:
        memory_exporter.clear()

    # Step 3: Measure Regressed Performance
    regressed_res = checkout_client.get("/api/orders")
    assert regressed_res.status_code == 200
    regressed_latency_ms = float(regressed_res.headers["X-Response-Time-Ms"])

    # Latency must be noticeably higher than baseline and near injected latency
    assert regressed_latency_ms >= injected_latency * 0.9, (
        f"Expected regressed latency >= {injected_latency * 0.9}ms, got {regressed_latency_ms}ms"
    )

    # Step 4: Verify OpenTelemetry Traces contain the specific regressed database query child span
    if memory_exporter:
        spans = memory_exporter.get_finished_spans()
        db_spans = [s for s in spans if "db.query" in s.name and s.attributes.get("incident.id") == "INC-001"]
        assert len(db_spans) >= 1, "Must contain child span for regressed database query"

        regressed_span = db_spans[0]
        assert regressed_span.attributes.get("db.regression") is True
        assert regressed_span.attributes.get("db.table") == "orders"
        assert regressed_span.attributes.get("db.system") == "postgresql"

    # Step 5: Reset Failure and Verify Immediate Recovery
    reset_res = checkout_client.post("/api/simulator/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["remaining_active"] == 0

    recovered_res = checkout_client.get("/api/orders")
    assert recovered_res.status_code == 200
    recovered_latency_ms = float(recovered_res.headers["X-Response-Time-Ms"])
    assert recovered_latency_ms < 50.0, (
        f"Expected recovered latency < 50ms, got {recovered_latency_ms}ms"
    )
