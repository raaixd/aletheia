"""Prometheus metrics instrumentation and export endpoints."""

from fastapi import APIRouter, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)

# Standard Prometheus metrics for HTTP services
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total count of HTTP requests processed",
    ["service", "method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Histogram of HTTP request latency in seconds",
    ["service", "method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total count of HTTP errors encountered",
    ["service", "endpoint", "error_type"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of currently active HTTP requests",
    ["service"],
)

metrics_router = APIRouter(tags=["Observability"])


@metrics_router.get("/metrics")
def get_metrics() -> Response:
    """Prometheus metrics endpoint returning plain text metrics."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
