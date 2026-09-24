"""Investigation API endpoints exposing deterministic evidence graph and timeline."""

from typing import Any, Dict, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from aletheia.graph.builder import EvidenceGraphBuilder
from aletheia.graph.cli import build_sample_inc001_builder

router = APIRouter(prefix="/api/v1/investigation", tags=["Investigation"])


class TimelineResponse(BaseModel):
    total_events: int
    events: List[Dict[str, Any]]
    ascii_timeline: str


class GraphResponse(BaseModel):
    summary: Dict[str, Any]
    nodes: Dict[str, Any]
    edges: List[Dict[str, Any]]
    mermaid: str


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline() -> TimelineResponse:
    """Retrieve chronologically sorted incident timeline."""
    builder = build_sample_inc001_builder()
    timeline = builder.timeline
    events = [e.model_dump() for e in timeline.get_events()]
    return TimelineResponse(
        total_events=len(events),
        events=events,
        ascii_timeline=timeline.format_ascii(),
    )


@router.get("/graph", response_model=GraphResponse)
def get_evidence_graph() -> GraphResponse:
    """Retrieve the full evidence graph with nodes, edges, summary, and Mermaid diagram."""
    builder = build_sample_inc001_builder()
    graph = builder.graph
    return GraphResponse(
        summary=graph.summary(),
        nodes={k: v.model_dump() for k, v in graph.nodes.items()},
        edges=[e.model_dump() for e in graph.edges],
        mermaid=graph.to_mermaid(),
    )


@router.get("/paths")
def get_causal_paths(
    source: str = Query("deploy:checkout-api:v4.2.1", description="Source node ID"),
    target: str = Query("evt:EVT-005", description="Target node ID"),
) -> Dict[str, Any]:
    """Find directed causal paths between two nodes in the evidence graph."""
    builder = build_sample_inc001_builder()
    paths = builder.graph.find_paths(source, target)
    formatted = [
        [{"source": e.source_id, "target": e.target_id, "type": e.type.value, "evidence": e.evidence_ids} for e in p]
        for p in paths
    ]
    return {
        "source": source,
        "target": target,
        "path_count": len(paths),
        "paths": formatted,
    }
