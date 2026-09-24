"""Integration tests verifying deterministic evidence graph reconstruction for INC-001."""

from datetime import datetime, timezone
import pytest

from aletheia.evidence.sources.local import LocalEvidenceSource
from aletheia.graph.builder import EvidenceGraphBuilder
from aletheia.graph.schema import RelationshipType


@pytest.mark.integration
def test_inc_001_deterministic_evidence_graph_reconstruction():
    """Verify that INC-001 telemetry reconstructs the exact causal graph and timeline."""
    source = LocalEvidenceSource()
    base_time = datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc)

    # 1. Ingest observable telemetry
    source.ingest_deployment("checkout-api", "v4.2.1", "abc12348f9", datetime(2026, 9, 25, 2, 2, 0, tzinfo=timezone.utc))
    source.ingest_commit(
        "checkout-api",
        "abc12348f9",
        "alex.dev@example.com",
        "refactor(checkout): update order history lookup without index",
        datetime(2026, 9, 25, 2, 1, 0, tzinfo=timezone.utc),
        changed_files=["simulator/services/checkout_api/routes.py"],
    )
    source.ingest_metric("http_request_duration_seconds", 0.005, datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc))
    source.ingest_metric("http_request_duration_seconds", 1.520, datetime(2026, 9, 25, 2, 5, 0, tzinfo=timezone.utc))
    source.ingest_log_entry({
        "timestamp": "2026-09-25T02:04:00+00:00",
        "level": "WARNING",
        "service": "checkout-api",
        "message": "Database query execution delayed by 1500.0ms due to unindexed sort regression (INC-001)",
        "duration_ms": 1500.0,
    })
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

    evidence_items = []
    evidence_items.extend(source.get_deployments())
    evidence_items.extend(source.get_code_changes())
    evidence_items.extend(source.get_traces())
    evidence_items.extend(source.get_metrics())
    evidence_items.extend(source.get_logs())

    # 2. Build deterministic EvidenceGraph and Timeline
    builder = EvidenceGraphBuilder.build_for_inc_001(evidence_items=evidence_items, start_time=base_time)
    graph = builder.graph
    timeline = builder.timeline

    # 3. Verify Timeline chronological sequence
    events = timeline.get_events()
    assert len(events) == 5
    assert events[0].event_id == "EVT-001"  # Normal traffic (02:00)
    assert events[1].event_id == "EVT-002"  # Deployment (02:02)
    assert events[2].event_id == "EVT-003"  # Query Changed (02:03)
    assert events[3].event_id == "EVT-004"  # DB Latency Rise (02:04)
    assert events[4].event_id == "EVT-005"  # API Latency Rise (02:05)

    # 4. Verify Causal Chain: Deployment -> Commit -> Query -> DB Latency -> API Latency
    paths = graph.find_paths("deploy:checkout-api:v4.2.1", "evt:EVT-005")
    assert len(paths) >= 1, "Must discover at least one direct causal path from Deployment to API Latency Spike"

    causal_path = paths[0]
    expected_rel_types = [
        RelationshipType.INTRODUCED,
        RelationshipType.MODIFIED,
        RelationshipType.INCREASED,
        RelationshipType.CONTRIBUTED_TO,
    ]
    assert [e.type for e in causal_path] == expected_rel_types

    # 5. Verify Evidence Provenance is attached to edges
    for edge in causal_path:
        assert len(edge.evidence_ids) > 0, f"Edge {edge.edge_id} ({edge.type}) must have backing evidence provenance IDs"

    # 6. Verify PRECEDES temporal sequence edges
    precedes_edges = graph.get_edges_by_type(RelationshipType.PRECEDES)
    assert len(precedes_edges) == 4  # links 5 consecutive events

    # 7. Verify Mermaid diagram is valid and captures root nodes
    mermaid_str = graph.to_mermaid()
    assert "deploy_checkout_api_v4_2_1" in mermaid_str
    assert "evt_EVT_005" in mermaid_str
    assert "INTRODUCED" in mermaid_str


@pytest.mark.integration
def test_investigation_api_endpoints(aletheia_client):
    """Verify REST API endpoints on Aletheia API return timeline, graph, and causal paths."""
    # 1. Test /timeline
    timeline_res = aletheia_client.get("/api/v1/investigation/timeline")
    assert timeline_res.status_code == 200
    timeline_data = timeline_res.json()
    assert timeline_data["total_events"] == 5
    assert "=== INCIDENT TIMELINE ===" in timeline_data["ascii_timeline"]

    # 2. Test /graph
    graph_res = aletheia_client.get("/api/v1/investigation/graph")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["summary"]["node_count"] > 0
    assert graph_data["summary"]["edge_count"] > 0
    assert "graph TD" in graph_data["mermaid"]

    # 3. Test /paths
    paths_res = aletheia_client.get(
        "/api/v1/investigation/paths",
        params={"source": "deploy:checkout-api:v4.2.1", "target": "evt:EVT-005"},
    )
    assert paths_res.status_code == 200
    paths_data = paths_res.json()
    assert paths_data["path_count"] >= 1
    first_path = paths_data["paths"][0]
    assert any(step["type"] == "INTRODUCED" for step in first_path)
    assert any(step["type"] == "CONTRIBUTED_TO" for step in first_path)
