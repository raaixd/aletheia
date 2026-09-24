"""Integration tests for ObservabilityMiddleware across services."""

import pytest
from aletheia.observability.tracing import get_memory_exporter


@pytest.mark.integration
def test_checkout_api_observability_headers(checkout_client):
    """Verify Checkout API injects correlation ID, response time, and trace IDs into response."""
    response = checkout_client.get("/health")
    assert response.status_code == 200

    # Observability headers must be present
    assert "x-correlation-id" in response.headers
    assert response.headers["x-correlation-id"].startswith("corr-")
    assert "x-response-time-ms" in response.headers
    assert float(response.headers["x-response-time-ms"]) >= 0

    assert "x-trace-id" in response.headers
    assert len(response.headers["x-trace-id"]) == 32
    assert "x-span-id" in response.headers
    assert len(response.headers["x-span-id"]) == 16


@pytest.mark.integration
def test_correlation_id_propagation(checkout_client):
    """Verify caller-provided correlation ID is respected and returned."""
    custom_corr_id = "test-custom-correlation-998877"
    response = checkout_client.get("/health", headers={"X-Correlation-ID": custom_corr_id})

    assert response.status_code == 200
    assert response.headers.get("x-correlation-id") == custom_corr_id


@pytest.mark.integration
def test_checkout_api_prometheus_metrics_endpoint(checkout_client):
    """Verify /metrics endpoint on Checkout API exports Prometheus metrics."""
    # First make a request to ensure counters are populated
    checkout_client.get("/api/products")

    metrics_response = checkout_client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "text/plain" in metrics_response.headers.get("content-type", "")

    body = metrics_response.text
    assert "http_requests_total" in body
    assert 'service="checkout-api"' in body
    assert 'endpoint="/api/products"' in body


@pytest.mark.integration
def test_aletheia_api_observability_headers_and_metrics(aletheia_client):
    """Verify Aletheia API response includes correlation ID, trace IDs, and exports /metrics."""
    res = aletheia_client.get("/health")
    assert res.status_code == 200
    assert "x-correlation-id" in res.headers
    assert "x-trace-id" in res.headers
    assert "x-span-id" in res.headers

    metrics_res = aletheia_client.get("/metrics")
    assert metrics_res.status_code == 200
    assert "http_requests_total" in metrics_res.text
    assert 'service="aletheia-api"' in metrics_res.text


@pytest.mark.integration
def test_opentelemetry_spans_captured_in_memory(checkout_client):
    """Verify OpenTelemetry spans are recorded with expected HTTP attributes."""
    memory_exporter = get_memory_exporter()
    if memory_exporter:
        memory_exporter.clear()

    # Perform order creation request
    products = checkout_client.get("/api/products").json()
    product_id = products[0]["id"]
    checkout_client.post(
        "/api/orders",
        json={"customer_email": "trace.test@example.com", "items": [{"product_id": product_id, "quantity": 1}]},
    )

    if memory_exporter:
        spans = memory_exporter.get_finished_spans()
        assert len(spans) >= 2  # at least the GET /api/products and POST /api/orders spans
        span_names = [s.name for s in spans]
        assert any("POST /api/orders" in name for name in span_names)

        post_span = next(s for s in spans if "POST /api/orders" in s.name)
        assert post_span.attributes["http.method"] == "POST"
        assert post_span.attributes["http.target"] == "/api/orders"
        assert post_span.attributes["http.status_code"] == 201
        assert "correlation_id" in post_span.attributes
