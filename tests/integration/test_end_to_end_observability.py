"""End-to-end verification that a single request correlates across logs, metrics, and traces."""

import io
import json
import logging
import pytest
from aletheia.observability.logging import JSONFormatter
from aletheia.observability.tracing import get_memory_exporter


@pytest.mark.integration
def test_end_to_end_request_produces_correlated_telemetry(checkout_client):
    """Verify that a request produces correlated logs, metrics, and OpenTelemetry trace spans."""
    # 1. Capture structured log records via an in-memory log stream
    log_stream = io.StringIO()
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setFormatter(JSONFormatter(service_name="checkout-api"))
    stream_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.addHandler(stream_handler)

    # 2. Reset memory span exporter
    memory_exporter = get_memory_exporter()
    if memory_exporter:
        memory_exporter.clear()

    # 3. Issue request with specific correlation ID
    client_corr_id = "corr-verify-e2e-12345"
    response = checkout_client.get(
        "/api/products",
        headers={"X-Correlation-ID": client_corr_id},
    )

    root_logger.removeHandler(stream_handler)

    # 4. Verify HTTP Response Headers
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == client_corr_id
    trace_id_header = response.headers["X-Trace-ID"]
    span_id_header = response.headers["X-Span-ID"]
    assert len(trace_id_header) == 32
    assert len(span_id_header) == 16
    assert "X-Response-Time-Ms" in response.headers

    # 5. Verify Structured JSON Log Output
    log_output = log_stream.getvalue().strip()
    assert len(log_output) > 0

    log_entries = [json.loads(line) for line in log_output.splitlines() if line.startswith("{")]
    correlated_logs = [entry for entry in log_entries if entry.get("correlation_id") == client_corr_id]
    assert len(correlated_logs) >= 1

    req_log = correlated_logs[0]
    assert req_log["correlation_id"] == client_corr_id
    assert req_log["trace_id"] == trace_id_header
    assert req_log["span_id"] == span_id_header
    assert req_log["service"] == "checkout-api"
    assert req_log["http_method"] == "GET"
    assert req_log["http_path"] == "/api/products"
    assert req_log["http_status"] == 200
    assert "duration_ms" in req_log

    # 6. Verify OpenTelemetry Distributed Trace Spans
    if memory_exporter:
        spans = memory_exporter.get_finished_spans()
        matching_spans = [s for s in spans if s.attributes.get("correlation_id") == client_corr_id]
        assert len(matching_spans) >= 1

        span = matching_spans[0]
        assert f"{span.context.trace_id:032x}" == trace_id_header
        assert f"{span.context.span_id:016x}" == span_id_header
        assert span.attributes["http.method"] == "GET"
        assert span.attributes["http.target"] == "/api/products"
        assert span.attributes["http.status_code"] == 200

    # 7. Verify Prometheus Metrics Increment
    metrics_response = checkout_client.get("/metrics")
    assert metrics_response.status_code == 200
    metrics_text = metrics_response.text
    assert 'http_requests_total{endpoint="/api/products",method="GET",service="checkout-api",status="200"}' in metrics_text
