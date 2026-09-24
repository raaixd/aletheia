# Aletheia Architecture: Phase 2 Observability

## Overview

In Phase 2, full observability was implemented across the simulated production services (`checkout-api`) and the Aletheia platform API (`aletheia-api`). Rather than treating observability as an afterthought or using generic text logs, Aletheia implements a unified, correlated telemetry triad:

1. **Structured JSON Logs**: Machine-readable JSON records emitted to stdout, automatically enriched with correlation IDs, OpenTelemetry trace/span IDs, and HTTP timing metadata.
2. **Context-Aware Correlation IDs**: Unique correlation IDs extracted from `X-Correlation-ID` or generated per-request, preserved across execution contexts using Python `contextvars`.
3. **Prometheus Metrics**: Standard `/metrics` endpoint exporting request counters, latency histograms, error counters, and in-flight request gauges.
4. **OpenTelemetry Distributed Tracing**: Automated span creation for HTTP requests with standards-compliant trace and span ID injection into response headers (`X-Trace-ID`, `X-Span-ID`).

---

## Telemetry Triad Architecture

```
Client Request
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                 ObservabilityMiddleware                     │
│                                                             │
│ 1. Extract or Generate Correlation ID (contextvars)         │
│ 2. Start OpenTelemetry Span (Trace ID, Span ID)             │
│ 3. Increment Active In-Flight Gauge                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Route Handler                          │
│                                                             │
│ - Logs automatically formatted as structured JSON           │
│ - Correlation ID + Trace ID + Span ID auto-injected         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 ObservabilityMiddleware (Exit)              │
│                                                             │
│ 1. Calculate Request Duration (ms)                          │
│ 2. Observe Prometheus Histogram & Increment Counter         │
│ 3. Set Span Status (OK / Error) & Record Attributes         │
│ 4. Emit Structured JSON Completion Log                      │
│ 5. Attach Response Headers:                                 │
│    - X-Correlation-ID                                       │
│    - X-Trace-ID                                             │
│    - X-Span-ID                                              │
│    - X-Response-Time-Ms                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## JSON Log Schema

Every log emitted by the system conforms to the following structured JSON schema:

```json
{
  "timestamp": "2026-09-24T20:33:10.800801+00:00",
  "level": "INFO",
  "service": "checkout-api",
  "logger": "aletheia.observability",
  "message": "GET /api/products completed with 200 in 7.88ms",
  "correlation_id": "corr-be32c80b7913",
  "trace_id": "fcb3dec3df421e4625f8490da2896e9d",
  "span_id": "2dbbf1e78558dcc6",
  "duration_ms": 7.88,
  "http_method": "GET",
  "http_path": "/api/products",
  "http_status": 200
}
```

---

## Prometheus Metrics

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `http_requests_total` | Counter | `service`, `method`, `endpoint`, `status` | Total count of HTTP requests processed |
| `http_request_duration_seconds` | Histogram | `service`, `method`, `endpoint` | Request duration histogram with standard latency buckets |
| `http_errors_total` | Counter | `service`, `endpoint`, `error_type` | Total errors categorized by status code or exception |
| `http_active_requests` | Gauge | `service` | Current count of active in-flight requests |

Metrics are accessible at `GET /metrics` on both `http://localhost:8001/metrics` (checkout-api) and `http://localhost:8000/metrics` (aletheia-api).

---

## OpenTelemetry Tracing

- Spans are generated for each HTTP request with name: `HTTP {method} {path}`
- Standard attributes:
  - `http.method`: HTTP method (GET, POST, etc.)
  - `http.url`: Full request URL
  - `http.target`: URL path
  - `http.status_code`: HTTP status response code
  - `service.name`: Identifies the originating service
  - `correlation_id`: Matches the application correlation ID
- Traces are exported via in-memory exporter during testing and are ready for OTLP collector forwarding.
