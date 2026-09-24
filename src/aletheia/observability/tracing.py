"""OpenTelemetry distributed tracing setup and utilities."""

import os
from typing import Optional, Tuple
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.util._once import Once

_in_memory_exporter: Optional[InMemorySpanExporter] = None
_tracer_provider: Optional[TracerProvider] = None


def reset_tracer_provider() -> None:
    """Reset global OpenTelemetry tracer provider (useful for test isolation)."""
    global _in_memory_exporter, _tracer_provider
    if _in_memory_exporter:
        _in_memory_exporter.clear()
    _in_memory_exporter = None
    _tracer_provider = None
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE = Once()


def setup_tracing(
    service_name: str,
    enable_in_memory: bool = False,
    enable_console: bool = False,
    force_reset: bool = False,
) -> TracerProvider:
    """Initialize OpenTelemetry TracerProvider and configure exporters."""
    global _in_memory_exporter, _tracer_provider

    if force_reset:
        reset_tracer_provider()

    current_provider = trace.get_tracer_provider()
    # Check if a real SDK TracerProvider is already configured
    if isinstance(current_provider, TracerProvider) and not force_reset:
        _tracer_provider = current_provider
        if enable_in_memory and _in_memory_exporter is None:
            _in_memory_exporter = InMemorySpanExporter()
            _tracer_provider.add_span_processor(SimpleSpanProcessor(_in_memory_exporter))
        return _tracer_provider

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # In-memory exporter allows automated test verification and inspection
    if enable_in_memory or os.getenv("OTEL_IN_MEMORY", "").lower() in ("true", "1"):
        _in_memory_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(_in_memory_exporter))

    if enable_console or os.getenv("OTEL_CONSOLE_EXPORT", "").lower() in ("true", "1"):
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    try:
        trace.set_tracer_provider(provider)
    except Exception:
        trace._TRACER_PROVIDER = provider
        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER_SET_ONCE.do_once(lambda: None)

    _tracer_provider = provider
    return provider


def get_tracer(name: str = "aletheia") -> trace.Tracer:
    """Get or create an OpenTelemetry tracer."""
    return trace.get_tracer(name)


def get_memory_exporter() -> Optional[InMemorySpanExporter]:
    """Retrieve the in-memory exporter if active (useful for testing)."""
    return _in_memory_exporter


def get_current_trace_and_span_ids() -> Tuple[Optional[str], Optional[str]]:
    """Extract the current active OpenTelemetry trace ID and span ID as hex strings."""
    current_span = trace.get_current_span()
    if not current_span:
        return None, None

    ctx = current_span.get_span_context()
    if not ctx or not ctx.is_valid:
        return None, None

    trace_id_hex = f"{ctx.trace_id:032x}"
    span_id_hex = f"{ctx.span_id:016x}"
    return trace_id_hex, span_id_hex
