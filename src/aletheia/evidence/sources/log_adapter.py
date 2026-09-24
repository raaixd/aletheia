"""Adapter converting structured JSON logs into EvidenceItems."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance


class LogAdapter:
    """Parses structured JSON application logs into standardized EvidenceItems."""

    def __init__(self, default_service: str = "checkout-api"):
        self.default_service = default_service

    def parse_log_entry(
        self,
        raw_log: Dict[str, Any],
        source_uri: str = "stdout",
        item_index: int = 1,
    ) -> EvidenceItem:
        """Transform a single JSON log record into an EvidenceItem."""
        # Parse timestamp
        ts_str = raw_log.get("timestamp")
        if ts_str:
            try:
                timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        service = raw_log.get("service", self.default_service)
        level = raw_log.get("level", "INFO")
        message = raw_log.get("message", "")
        correlation_id = raw_log.get("correlation_id")
        trace_id = raw_log.get("trace_id")
        span_id = raw_log.get("span_id")
        duration_ms = raw_log.get("duration_ms")
        extra = raw_log.get("extra", {})

        entity_ids = [f"svc:{service}"]
        if correlation_id:
            entity_ids.append(f"corr:{correlation_id}")
        if trace_id:
            entity_ids.append(f"trace:{trace_id}")
        if raw_log.get("http_path"):
            method = raw_log.get("http_method", "GET")
            path = raw_log.get("http_path")
            entity_ids.append(f"ep:{service}:{method}:{path}")

        evidence_id = f"EV-LOG-{item_index:04d}"
        provenance = EvidenceProvenance(
            source_type=EvidenceSourceType.APPLICATION_LOG,
            source_uri=source_uri,
            extracted_at=datetime.now(timezone.utc),
            extraction_method="LogAdapter.parse_log_entry",
            raw_reference={
                "logger": raw_log.get("logger"),
                "level": level,
                "correlation_id": correlation_id,
            },
        )

        return EvidenceItem(
            evidence_id=evidence_id,
            timestamp=timestamp,
            source=EvidenceSourceType.APPLICATION_LOG,
            type=EvidenceType.LOG,
            service=service,
            entity_ids=entity_ids,
            content=f"[{level}] {service}: {message}",
            data={
                "level": level,
                "message": message,
                "duration_ms": duration_ms,
                "correlation_id": correlation_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "extra": extra,
            },
            provenance=provenance,
            confidence=1.0,
        )

    def parse_log_lines(self, lines: List[str], source_uri: str = "stdout") -> List[EvidenceItem]:
        """Parse multiple log strings into EvidenceItems."""
        items = []
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str or not line_str.startswith("{"):
                continue
            try:
                data = json.loads(line_str)
                items.append(self.parse_log_entry(data, source_uri=source_uri, item_index=idx))
            except json.JSONDecodeError:
                continue
        return items
