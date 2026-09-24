"""Aletheia Observability Package.

Provides structured JSON logging, correlation IDs, Prometheus metrics,
and OpenTelemetry distributed tracing across all services.
"""

from aletheia.observability.logging import (
    JSONFormatter,
    setup_logging,
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
    metrics_router,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ERROR_COUNT,
    ACTIVE_REQUESTS,
)
from aletheia.observability.middleware import ObservabilityMiddleware

__all__ = [
    "JSONFormatter",
    "setup_logging",
    "get_correlation_id",
    "set_correlation_id",
    "correlation_id_ctx",
    "setup_tracing",
    "get_tracer",
    "get_current_trace_and_span_ids",
    "get_memory_exporter",
    "metrics_router",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "ERROR_COUNT",
    "ACTIVE_REQUESTS",
    "ObservabilityMiddleware",
]
