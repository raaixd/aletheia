"""Adapter converting Prometheus metrics into EvidenceItems."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance


class MetricAdapter:
    """Evaluates Prometheus metrics and converts significant measurements into EvidenceItems."""

    def __init__(self, default_service: str = "checkout-api"):
        self.default_service = default_service

    def create_metric_evidence(
        self,
        metric_name: str,
        value: float,
        timestamp: datetime,
        service: str = "checkout-api",
        endpoint: str = "/api/orders",
        unit: str = "seconds",
        item_index: int = 1,
        source_uri: str = "http://localhost:8001/metrics",
    ) -> EvidenceItem:
        """Create a structured EvidenceItem from a metric measurement."""
        evidence_id = f"EV-METRIC-{item_index:04d}"
        entity_ids = [
            f"svc:{service}",
            f"metric:{service}:{metric_name}",
            f"ep:{service}:GET:{endpoint}",
        ]

        provenance = EvidenceProvenance(
            source_type=EvidenceSourceType.PROMETHEUS,
            source_uri=source_uri,
            extracted_at=datetime.now(timezone.utc),
            extraction_method="MetricAdapter.create_metric_evidence",
            raw_reference={
                "metric_name": metric_name,
                "value": value,
                "endpoint": endpoint,
            },
        )

        content = f"Metric '{metric_name}' on {endpoint} measured {value:.3f} {unit}"
        if value > 0.5:
            content += " [ELEVATED LATENCY DETECTED]"

        return EvidenceItem(
            evidence_id=evidence_id,
            timestamp=timestamp,
            source=EvidenceSourceType.PROMETHEUS,
            type=EvidenceType.METRIC,
            service=service,
            entity_ids=entity_ids,
            content=content,
            data={
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "endpoint": endpoint,
            },
            provenance=provenance,
            confidence=1.0,
        )
