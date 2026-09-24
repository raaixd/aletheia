"""Adapter converting OpenTelemetry spans into EvidenceItems."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance


class TraceAdapter:
    """Transforms OpenTelemetry spans into standardized EvidenceItems."""

    def __init__(self, default_service: str = "checkout-api"):
        self.default_service = default_service

    def parse_span(self, span: Any, source_uri: str = "otel/memory_exporter", item_index: int = 1) -> EvidenceItem:
        """Parse an OpenTelemetry ReadableSpan or span dictionary into an EvidenceItem."""
        # Handle ReadableSpan object from opentelemetry SDK
        if hasattr(span, "name") and hasattr(span, "context"):
            name = span.name
            trace_id = f"{span.context.trace_id:032x}"
            span_id = f"{span.context.span_id:016x}"
            parent_id = f"{span.parent.span_id:016x}" if span.parent else None
            attributes = dict(span.attributes or {})
            start_ns = span.start_time
            end_ns = span.end_time or start_ns
            duration_ms = round((end_ns - start_ns) / 1_000_000, 2)
            timestamp = datetime.fromtimestamp(start_ns / 1_000_000_000, tz=timezone.utc)
            service = attributes.get("service.name", self.default_service)
            status_code = str(span.status.status_code)
        else:
            # Handle dictionary
            name = span.get("name", "span")
            trace_id = span.get("trace_id", "0" * 32)
            span_id = span.get("span_id", "0" * 16)
            parent_id = span.get("parent_id")
            attributes = span.get("attributes", {})
            duration_ms = span.get("duration_ms", 0.0)
            timestamp = span.get("timestamp", datetime.now(timezone.utc))
            service = span.get("service", attributes.get("service.name", self.default_service))
            status_code = span.get("status_code", "OK")

        entity_ids = [f"svc:{service}", f"trace:{trace_id}"]
        if "http.target" in attributes:
            method = attributes.get("http.method", "GET")
            target = attributes.get("http.target")
            entity_ids.append(f"ep:{service}:{method}:{target}")
        if "db.system" in attributes or "db.table" in attributes:
            db_name = attributes.get("db.name", "postgres")
            entity_ids.append(f"db:{db_name}")

        correlation_id = attributes.get("correlation_id")
        if correlation_id:
            entity_ids.append(f"corr:{correlation_id}")

        evidence_id = f"EV-SPAN-{item_index:04d}"
        provenance = EvidenceProvenance(
            source_type=EvidenceSourceType.OPENTELEMETRY,
            source_uri=source_uri,
            extracted_at=datetime.now(timezone.utc),
            extraction_method="TraceAdapter.parse_span",
            raw_reference={
                "trace_id": trace_id,
                "span_id": span_id,
                "span_name": name,
            },
        )

        content = f"Span '{name}' ({duration_ms}ms, trace={trace_id[:8]})"
        if attributes.get("db.regression"):
            content += " [DATABASE REGRESSION DETECTED]"

        return EvidenceItem(
            evidence_id=evidence_id,
            timestamp=timestamp,
            source=EvidenceSourceType.OPENTELEMETRY,
            type=EvidenceType.SPAN,
            service=service,
            entity_ids=entity_ids,
            content=content,
            data={
                "name": name,
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_id": parent_id,
                "duration_ms": duration_ms,
                "attributes": attributes,
                "status_code": status_code,
            },
            provenance=provenance,
            confidence=1.0,
        )

    def parse_spans(self, spans: List[Any], source_uri: str = "otel/memory_exporter") -> List[EvidenceItem]:
        """Convert a list of spans into EvidenceItems."""
        return [self.parse_span(span, source_uri=source_uri, item_index=idx) for idx, span in enumerate(spans, start=1)]
