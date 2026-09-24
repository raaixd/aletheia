"""CLI tool to inspect the deterministic Evidence Graph and Timeline."""

import argparse
import json
import sys
from datetime import datetime, timezone

from aletheia.evidence.sources.local import LocalEvidenceSource
from aletheia.graph.builder import EvidenceGraphBuilder


def build_sample_inc001_builder() -> EvidenceGraphBuilder:
    """Instantiate a local evidence source and build graph for INC-001."""
    source = LocalEvidenceSource()
    base_time = datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc)

    # Ingest representative telemetry
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

    return EvidenceGraphBuilder.build_for_inc_001(evidence_items=evidence_items, start_time=base_time)


def main():
    parser = argparse.ArgumentParser(description="Aletheia Evidence Graph & Timeline Inspector")
    parser.add_argument("--inspect-inc001", action="store_true", help="Build and inspect INC-001 evidence graph")
    parser.add_argument("--timeline", action="store_true", help="Print ASCII timeline")
    parser.add_argument("--mermaid", action="store_true", help="Output GitHub Mermaid diagram")
    parser.add_argument("--paths", action="store_true", help="Print causal paths from deployment to API latency spike")
    parser.add_argument("--json", action="store_true", help="Output graph structure as JSON")

    args = parser.parse_args()

    builder = build_sample_inc001_builder()
    graph = builder.graph
    timeline = builder.timeline

    print("\n" + "=" * 60)
    print("ALETHEIA EVIDENCE GRAPH & TIMELINE INSPECTOR")
    print("=" * 60)

    summary = graph.summary()
    print(f"\nGraph Summary: {summary['node_count']} nodes, {summary['edge_count']} edges")
    print("Relationships:")
    for rel, count in summary["relationship_breakdown"].items():
        print(f"  - {rel}: {count}")

    if args.timeline or not (args.mermaid or args.paths or args.json):
        print("\n" + timeline.format_ascii())

    if args.paths:
        print("\n=== CAUSAL PATHS (deploy:checkout-api:v4.2.1 -> evt:EVT-005) ===")
        paths = graph.find_paths("deploy:checkout-api:v4.2.1", "evt:EVT-005")
        if not paths:
            print("No directed paths found.")
        for idx, path in enumerate(paths, start=1):
            chain = []
            for edge in path:
                chain.append(f"({edge.source_id}) --[{edge.type.value}]-->")
            chain.append(f"({path[-1].target_id})")
            print(f"Path {idx}: {' '.join(chain)}")

    if args.mermaid:
        print("\n=== MERMAID DIAGRAM ===")
        print(graph.to_mermaid())

    if args.json:
        print("\n=== GRAPH JSON ===")
        print(json.dumps(graph.model_dump(), default=str, indent=2))


if __name__ == "__main__":
    main()
