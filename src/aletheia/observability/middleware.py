"""Observability middleware for FastAPI integrating logging, metrics, and tracing."""

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry.trace import Status, StatusCode

from aletheia.observability.logging import correlation_id_ctx, set_correlation_id
from aletheia.observability.metrics import (
    ACTIVE_REQUESTS,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ERROR_COUNT,
)
from aletheia.observability.tracing import get_tracer, get_current_trace_and_span_ids

logger = logging.getLogger("aletheia.observability")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware capturing request correlation, OpenTelemetry spans, and Prometheus metrics."""

    def __init__(self, app, service_name: str = "aletheia-service"):
        super().__init__(app)
        self.service_name = service_name
        self.tracer = get_tracer(service_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ignore metrics scraping from trace pollution if needed, but keep metrics intact
        path = request.url.path
        method = request.method

        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or f"corr-{uuid.uuid4().hex[:12]}"
        )
        token = correlation_id_ctx.set(correlation_id)

        # Track active in-flight requests
        ACTIVE_REQUESTS.labels(service=self.service_name).inc()
        start_time = time.perf_counter()
        status_code = 500
        span_name = f"HTTP {method} {path}"

        with self.tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.target", path)
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("correlation_id", correlation_id)

            trace_id_hex, span_id_hex = get_current_trace_and_span_ids()

            try:
                response = await call_next(request)
                status_code = response.status_code
                span.set_attribute("http.status_code", status_code)

                if status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, description=f"HTTP {status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))

            except Exception as exc:
                status_code = 500
                span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                span.record_exception(exc)
                ERROR_COUNT.labels(
                    service=self.service_name,
                    endpoint=path,
                    error_type=exc.__class__.__name__,
                ).inc()
                raise
            finally:
                duration_seconds = time.perf_counter() - start_time
                duration_ms = round(duration_seconds * 1000, 2)

                # Record Prometheus metrics
                REQUEST_COUNT.labels(
                    service=self.service_name,
                    method=method,
                    endpoint=path,
                    status=str(status_code),
                ).inc()

                REQUEST_LATENCY.labels(
                    service=self.service_name,
                    method=method,
                    endpoint=path,
                ).observe(duration_seconds)

                if status_code >= 400 and status_code != 500:
                    ERROR_COUNT.labels(
                        service=self.service_name,
                        endpoint=path,
                        error_type=f"HTTP_{status_code}",
                    ).inc()

                ACTIVE_REQUESTS.labels(service=self.service_name).dec()

                # Log structured completion event
                log_extra = {
                    "service": self.service_name,
                    "correlation_id": correlation_id,
                    "duration_ms": duration_ms,
                    "http_method": method,
                    "http_path": path,
                    "http_status": status_code,
                }
                log_level = logging.WARNING if status_code >= 400 else logging.INFO
                logger.log(
                    log_level,
                    f"{method} {path} completed with {status_code} in {duration_ms}ms",
                    extra=log_extra,
                )

                # Clean up context
                correlation_id_ctx.reset(token)

        # Attach observability headers to response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        if trace_id_hex:
            response.headers["X-Trace-ID"] = trace_id_hex
        if span_id_hex:
            response.headers["X-Span-ID"] = span_id_hex

        return response
