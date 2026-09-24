"""Unit tests for structured JSON logging, tracing, and metrics."""

import json
import logging
import pytest
from opentelemetry import trace
from aletheia.observability.logging import (
    JSONFormatter,
    get_correlation_id,
    set_correlation_id,
    correlation_id_ctx,
)
from aletheia.observability.tracing import (
    setup_tracing,
    get_tracer,
    get_current_trace_and_span_ids,
    get_memory_exporter,
)
from aletheia.observability.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ACTIVE_REQUESTS,
    metrics_router,
)


@pytest.mark.unit
def test_json_formatter_outputs_valid_json():
    """Verify JSONFormatter outputs valid JSON with expected core fields."""
    formatter = JSONFormatter(service_name="test-service")
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=25,
        msg="Test log message for observability",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["message"] == "Test log message for observability"
    assert data["level"] == "INFO"
    assert data["service"] == "test-service"
    assert "timestamp" in data
    assert data["logger"] == "test.logger"


@pytest.mark.unit
def test_json_formatter_captures_correlation_id():
    """Verify JSONFormatter extracts active correlation ID from context."""
    formatter = JSONFormatter(service_name="test-service")
    set_correlation_id("corr-xyz-789")

    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=45,
        msg="Correlated message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data.get("correlation_id") == "corr-xyz-789"
    set_correlation_id(None)


@pytest.mark.unit
def test_opentelemetry_tracing_and_span_ids():
    """Verify OpenTelemetry tracer creates spans and generates trace/span hex IDs."""
    setup_tracing(service_name="test-service", enable_in_memory=True)
    tracer = get_tracer("test-tracer")

    with tracer.start_as_current_span("test-operation") as span:
        trace_id, span_id = get_current_trace_and_span_ids()
        assert trace_id is not None
        assert len(trace_id) == 32  # 32 hex chars for 128-bit trace ID
        assert span_id is not None
        assert len(span_id) == 16   # 16 hex chars for 64-bit span ID

        # Formatter should capture active span IDs in logs
        formatter = JSONFormatter(service_name="test-service")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=75,
            msg="Span correlated message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)
        assert data.get("trace_id") == trace_id
        assert data.get("span_id") == span_id


@pytest.mark.unit
def test_prometheus_metrics_increment():
    """Verify Prometheus counter and gauge operations."""
    service = "test-service"
    ACTIVE_REQUESTS.labels(service=service).inc()
    REQUEST_COUNT.labels(service=service, method="GET", endpoint="/test", status="200").inc()
    REQUEST_LATENCY.labels(service=service, method="GET", endpoint="/test").observe(0.042)

    from prometheus_client import generate_latest, REGISTRY
    metrics_output = generate_latest(REGISTRY).decode("utf-8")

    assert "http_requests_total" in metrics_output
    assert 'service="test-service"' in metrics_output
    assert 'endpoint="/test"' in metrics_output
    assert "http_request_duration_seconds" in metrics_output
