"""Telemetry and ground truth loaders with strict isolation guarantees."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from aletheia.evidence.events import Event, EventType, Timeline
from aletheia.evidence.schema import EvidenceItem
from aletheia.evidence.sources.local import LocalEvidenceSource
from aletheia.models.incident import IncidentGroundTruth


def get_ground_truth_path(incident_id: str) -> Path:
    """Resolve ground truth JSON file path."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    gt_dir = project_root / "incidents" / "ground_truth"

    candidate_names = [
        f"{incident_id.lower().replace('-', '_')}_ground_truth.json",
        f"{incident_id.lower()}_ground_truth.json",
        f"{incident_id}_ground_truth.json",
    ]

    for name in candidate_names:
        p = gt_dir / name
        if p.exists():
            return p

    raise FileNotFoundError(f"No ground truth specification found for incident '{incident_id}' in {gt_dir}")


def load_ground_truth(incident_id: str) -> IncidentGroundTruth:
    """Load isolated ground truth specification.

    CRITICAL RULE:
    This function must ONLY be called by the Evaluation Harness or test assertions.
    Diagnostic agents/baselines must NEVER call this or have access to ground truth.
    """
    path = get_ground_truth_path(incident_id)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return IncidentGroundTruth(**data)


def load_incident_telemetry(incident_id: str) -> Tuple[str, List[EvidenceItem], Timeline]:
    """Load observable telemetry and timeline for an incident without ground truth leakage.

    Returns:
        (alert_description, evidence_items, timeline)
    """
    if incident_id.upper() != "INC-001":
        raise ValueError(f"Telemetry loader currently supports 'INC-001'. Received: '{incident_id}'")

    source = LocalEvidenceSource(default_service="checkout-api")

    # Ingest representative observable telemetry for INC-001
    source.ingest_deployment(
        service="checkout-api",
        version="v4.2.1",
        commit_sha="abc12348f9",
        timestamp=datetime(2026, 9, 25, 2, 2, 0, tzinfo=timezone.utc),
    )
    source.ingest_commit(
        service="checkout-api",
        commit_sha="abc12348f9",
        author="alex.dev@example.com",
        message="refactor(checkout): update order history lookup without index",
        timestamp=datetime(2026, 9, 25, 2, 1, 0, tzinfo=timezone.utc),
        changed_files=["simulator/services/checkout_api/routes.py"],
    )
    # Normal metric sample before incident
    source.ingest_metric(
        metric_name="http_request_duration_seconds",
        value=0.005,
        timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
    )
    # Regressed metric sample
    source.ingest_metric(
        metric_name="http_request_duration_seconds",
        value=1.520,
        timestamp=datetime(2026, 9, 25, 2, 5, 0, tzinfo=timezone.utc),
    )
    # Warning log
    source.ingest_log_entry({
        "timestamp": "2026-09-25T02:04:00+00:00",
        "level": "WARNING",
        "service": "checkout-api",
        "message": "Database query execution delayed by 1500.0ms due to unindexed sort regression (INC-001)",
        "duration_ms": 1500.0,
    })
    # Database trace span
    source._raw_spans.append({
        "name": "db.query: SELECT orders (unindexed)",
        "trace_id": "a" * 32,
        "span_id": "b" * 16,
        "duration_ms": 1500.0,
        "timestamp": datetime(2026, 9, 25, 2, 4, 0, tzinfo=timezone.utc),
        "attributes": {
            "db.system": "postgresql",
            "db.table": "orders",
            "db.regression": True,
            "incident.id": "INC-001",
        },
    })

    evidence_items: List[EvidenceItem] = []
    evidence_items.extend(source.get_deployments())
    evidence_items.extend(source.get_code_changes())
    evidence_items.extend(source.get_traces())
    evidence_items.extend(source.get_metrics())
    evidence_items.extend(source.get_logs())

    # Build chronological timeline
    timeline = Timeline()
    timeline.add_event(Event(
        event_id="EVT-001",
        timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
        type=EventType.NORMAL_TRAFFIC,
        service="checkout-api",
        summary="Normal background traffic across checkout endpoints (<10ms latency)",
        evidence_ids=["EV-METRIC-0001"],
    ))
    timeline.add_event(Event(
        event_id="EVT-002",
        timestamp=datetime(2026, 9, 25, 2, 2, 0, tzinfo=timezone.utc),
        type=EventType.DEPLOYMENT_COMPLETE,
        service="checkout-api",
        summary="Deployment of release v4.2.1 completed on checkout-api",
        evidence_ids=["EV-DEP-0001", "EV-GIT-0001"],
    ))
    timeline.add_event(Event(
        event_id="EVT-003",
        timestamp=datetime(2026, 9, 25, 2, 3, 0, tzinfo=timezone.utc),
        type=EventType.QUERY_CHANGED,
        service="checkout-api",
        summary="Order history SQL query execution plan modified (unindexed sort)",
        evidence_ids=["EV-GIT-0001"],
    ))
    timeline.add_event(Event(
        event_id="EVT-004",
        timestamp=datetime(2026, 9, 25, 2, 4, 0, tzinfo=timezone.utc),
        type=EventType.DB_LATENCY_INCREASE,
        service="checkout-api",
        summary="Database query execution time rose from 3ms to 1500ms on orders query",
        evidence_ids=["EV-SPAN-0001", "EV-LOG-0001"],
    ))
    timeline.add_event(Event(
        event_id="EVT-005",
        timestamp=datetime(2026, 9, 25, 2, 5, 0, tzinfo=timezone.utc),
        type=EventType.API_LATENCY_INCREASE,
        service="checkout-api",
        summary="GET /api/orders average and P99 latency exceeded 1500ms SLA",
        evidence_ids=["EV-METRIC-0002"],
    ))

    alert_desc = (
        "CRITICAL SLA BREACH: checkout-api /api/orders P99 latency exceeded 1500ms threshold (measured: 1520ms). "
        "Alert triggered at 2026-09-25T02:05:00Z."
    )

    return alert_desc, evidence_items, timeline
