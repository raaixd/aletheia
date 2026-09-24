"""Evidence graph data structure and query engine."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

from aletheia.graph.schema import GraphNode, GraphEdge, RelationshipType


class EvidenceGraph(BaseModel):
    """Directed graph representing entities, events, relationships, and evidence provenance."""
    model_config = ConfigDict(extra="ignore")

    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: List[GraphEdge] = Field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        """Add or update a node in the graph."""
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        """Add a directed edge between existing nodes."""
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node '{edge.source_id}' does not exist in graph")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node '{edge.target_id}' does not exist in graph")
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieve node by ID."""
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges originating from node_id."""
        return [e for e in self.edges if e.source_id == node_id]

    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges targeting node_id."""
        return [e for e in self.edges if e.target_id == node_id]

    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        """Get all adjacent downstream nodes."""
        targets = {e.target_id for e in self.get_outgoing_edges(node_id)}
        return [self.nodes[tid] for tid in targets if tid in self.nodes]

    def get_edges_by_type(self, rel_type: RelationshipType) -> List[GraphEdge]:
        """Filter edges by specific relationship type."""
        return [e for e in self.edges if e.type == rel_type]

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> List[List[GraphEdge]]:
        """Find all directed causal paths from source_id to target_id."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        results: List[List[GraphEdge]] = []

        def dfs(current_id: str, current_path: List[GraphEdge], visited: Set[str]):
            if current_id == target_id:
                results.append(list(current_path))
                return
            if len(current_path) >= max_depth:
                return

            for edge in self.get_outgoing_edges(current_id):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    current_path.append(edge)
                    dfs(edge.target_id, current_path, visited)
                    current_path.pop()
                    visited.remove(edge.target_id)

        dfs(source_id, [], {source_id})
        return results

    def get_temporal_subgraph(self, start: datetime, end: datetime) -> "EvidenceGraph":
        """Extract subgraph of nodes and edges within a specific time window."""
        subgraph = EvidenceGraph()
        valid_node_ids = set()

        for nid, node in self.nodes.items():
            if node.timestamp and start <= node.timestamp <= end:
                subgraph.add_node(node)
                valid_node_ids.add(nid)

        for edge in self.edges:
            if edge.source_id in valid_node_ids and edge.target_id in valid_node_ids:
                subgraph.add_edge(edge)

        return subgraph

    def to_mermaid(self) -> str:
        """Render the evidence graph as a GitHub-compatible Mermaid diagram."""
        lines = ["graph TD"]
        # Format nodes
        for nid, node in self.nodes.items():
            clean_id = nid.replace(":", "_").replace("-", "_").replace(".", "_").replace("/", "_")
            safe_label = node.label.replace('"', "'")
            lines.append(f'    {clean_id}["{safe_label}"]')

        # Format edges
        for edge in self.edges:
            src = edge.source_id.replace(":", "_").replace("-", "_").replace(".", "_").replace("/", "_")
            tgt = edge.target_id.replace(":", "_").replace("-", "_").replace(".", "_").replace("/", "_")
            label = edge.type.value
            lines.append(f'    {src} -->|"{label}"| {tgt}')

        return "\n".join(lines)

    def summary(self) -> Dict[str, Any]:
        """Return structural summary of the graph."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "relationship_breakdown": {
                rel_type.value: len(self.get_edges_by_type(rel_type))
                for rel_type in RelationshipType
                if len(self.get_edges_by_type(rel_type)) > 0
            },
        }
