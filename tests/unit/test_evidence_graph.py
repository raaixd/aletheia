"""Unit tests for EvidenceGraph query engine, path finding, and Mermaid visualization."""

from datetime import datetime, timezone
import pytest

from aletheia.graph.graph import EvidenceGraph
from aletheia.graph.schema import GraphNode, GraphEdge, RelationshipType


@pytest.fixture
def sample_graph():
    """Create a sample 4-node directed graph."""
    graph = EvidenceGraph()
    n1 = GraphNode(node_id="A", label="Deploy", category="ENTITY")
    n2 = GraphNode(node_id="B", label="Commit", category="ENTITY")
    n3 = GraphNode(node_id="C", label="Query Change", category="EVENT")
    n4 = GraphNode(node_id="D", label="Latency Rise", category="EVENT")

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.add_node(n4)

    graph.add_edge(GraphEdge(edge_id="e1", source_id="A", target_id="B", type=RelationshipType.INTRODUCED))
    graph.add_edge(GraphEdge(edge_id="e2", source_id="B", target_id="C", type=RelationshipType.MODIFIED))
    graph.add_edge(GraphEdge(edge_id="e3", source_id="C", target_id="D", type=RelationshipType.INCREASED))

    return graph


@pytest.mark.unit
def test_graph_node_and_edge_queries(sample_graph):
    """Verify outgoing, incoming, and neighbor queries."""
    outgoing = sample_graph.get_outgoing_edges("A")
    assert len(outgoing) == 1
    assert outgoing[0].target_id == "B"

    incoming = sample_graph.get_incoming_edges("B")
    assert len(incoming) == 1
    assert incoming[0].source_id == "A"

    neighbors = sample_graph.get_neighbors("A")
    assert len(neighbors) == 1
    assert neighbors[0].node_id == "B"


@pytest.mark.unit
def test_graph_find_paths(sample_graph):
    """Verify directed causal path finding from source to destination."""
    paths = sample_graph.find_paths("A", "D")
    assert len(paths) == 1
    path = paths[0]
    assert [e.edge_id for e in path] == ["e1", "e2", "e3"]
    assert [e.type for e in path] == [
        RelationshipType.INTRODUCED,
        RelationshipType.MODIFIED,
        RelationshipType.INCREASED,
    ]


@pytest.mark.unit
def test_graph_mermaid_export(sample_graph):
    """Verify Mermaid export generates valid diagram syntax."""
    mermaid = sample_graph.to_mermaid()
    assert mermaid.startswith("graph TD")
    assert 'A["Deploy"]' in mermaid
    assert 'A -->|"INTRODUCED"| B' in mermaid
    assert 'B -->|"MODIFIED"| C' in mermaid
    assert 'C -->|"INCREASED"| D' in mermaid


@pytest.mark.unit
def test_graph_summary(sample_graph):
    """Verify summary breakdown reflects node and edge counts."""
    summary = sample_graph.summary()
    assert summary["node_count"] == 4
    assert summary["edge_count"] == 3
    assert summary["relationship_breakdown"]["INTRODUCED"] == 1
    assert summary["relationship_breakdown"]["MODIFIED"] == 1
    assert summary["relationship_breakdown"]["INCREASED"] == 1
