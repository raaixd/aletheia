# ADR 0002: Observability Architecture (Correlated Telemetry Triad)

## Context

Incident investigation requires strict provenance, temporal accuracy, and causality. When investigating why an incident occurred, Aletheia cannot rely on disconnected text logs or unmeasured delays. Every log line must correlate to a trace span, and every metric anomaly must link to the relevant requests.

## Decisions

1. **Structured JSON Logging**:
   - Replaced default text logging with a custom `JSONFormatter` writing to stdout.
   - Automatically enriches log lines with `correlation_id`, `trace_id`, `span_id`, and `duration_ms`.
   - Adheres to Twelve-Factor App principles by writing to standard streams.

2. **Context-Aware Correlation IDs**:
   - Implemented using Python's asynchronous `contextvars` module (`correlation_id_ctx`).
   - Ensures deep function calls and database queries log with the active correlation ID without explicitly threading parameters through every function signature.

3. **Prometheus Metrics**:
   - Instrument standard HTTP metrics (`http_requests_total`, `http_request_duration_seconds`, `http_errors_total`, `http_active_requests`) using official `prometheus-client`.
   - Exposed on `/metrics` endpoint for Prometheus scraping.

4. **OpenTelemetry Distributed Tracing**:
   - Used official OpenTelemetry SDK (`opentelemetry-api`, `opentelemetry-sdk`).
   - Added `InMemorySpanExporter` support to ensure automated test suites can programmatically verify spans without running a separate OpenTelemetry collector or Jaeger container.
   - Injected `X-Correlation-ID`, `X-Trace-ID`, and `X-Span-ID` into HTTP response headers for end-to-end tracing.

## Consequences

- Full traceability across logs, metrics, and traces for every single HTTP request.
- Sub-second automated verification in CI/CD without external tracing infrastructure.
- Direct foundation for Phase 3 (Failure Injection) and Phase 4 (Evidence Model & Graph).
