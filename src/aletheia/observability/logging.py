"""Structured JSON logging with correlation IDs and trace context."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable for request correlation ID
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Retrieve current correlation ID from context."""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set correlation ID in context."""
    correlation_id_ctx.set(correlation_id)


class JSONFormatter(logging.Formatter):
    """Custom formatter producing structured JSON log records."""

    def __init__(self, service_name: str = "aletheia-service"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        # Build base payload
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", self.service_name),
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include correlation ID from context or record attribute
        correlation_id = getattr(record, "correlation_id", None) or get_correlation_id()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id

        # Attach OpenTelemetry trace and span ID if available
        from aletheia.observability.tracing import get_current_trace_and_span_ids
        trace_id, span_id = get_current_trace_and_span_ids()
        if trace_id:
            log_entry["trace_id"] = trace_id
        if span_id:
            log_entry["span_id"] = span_id

        # Capture performance duration if attached to record
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Include HTTP context if present
        if hasattr(record, "http_method"):
            log_entry["http_method"] = record.http_method
        if hasattr(record, "http_path"):
            log_entry["http_path"] = record.http_path
        if hasattr(record, "http_status"):
            log_entry["http_status"] = record.http_status

        # Capture exception details
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include any extra custom metadata passed via extra={}
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "service", "correlation_id", "duration_ms",
            "http_method", "http_path", "http_status", "message",
        }
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_")
        }
        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str)


def setup_logging(service_name: str, log_level: str = "INFO") -> None:
    """Configure root logger to output structured JSON to stdout."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(JSONFormatter(service_name=service_name))
    root_logger.addHandler(handler)

    # Suppress overly noisy external loggers if needed
    logging.getLogger("uvicorn.access").handlers = []
