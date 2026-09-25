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


@router.get("/incidents")
def list_incidents() -> List[Dict[str, Any]]:
    """List all available incident scenarios with metadata."""
    import json
    from pathlib import Path
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    scenarios_dir = repo_root / "incidents" / "scenarios"
    incidents = []
    if scenarios_dir.exists():
        for p in sorted(scenarios_dir.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                incidents.append({
                    "incident_id": data.get("incident_id", p.stem.replace("_scenario", "").upper()),
                    "name": data.get("name", ""),
                    "category": data.get("category", "system"),
                    "severity": data.get("severity", "CRITICAL"),
                    "affected_service": data.get("affected_service", "checkout-api"),
                    "description": data.get("description", ""),
                })
            except Exception:
                continue
    return incidents


@router.post("/diagnose/{incident_id}")
def diagnose_incident(
    incident_id: str,
    system: str = Query("aletheia-3agent", description="System: aletheia-3agent, two-agent, single-llm"),
) -> Dict[str, Any]:
    """Run full diagnostic workflow on any incident and return complete agent outputs and scorecard."""
    from aletheia.agents.orchestrator import AletheiaMultiAgentSystem
    from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
    from aletheia.evaluation.baselines.two_agent import TwoAgentBaseline
    from aletheia.evaluation.harness import EvaluationHarness
    from aletheia.evaluation.loader import load_incident_telemetry

    alert_desc, items, timeline = load_incident_telemetry(incident_id)
    harness = EvaluationHarness()

    if system == "aletheia-3agent":
        sys_instance = AletheiaMultiAgentSystem()
    elif system in ("two-agent", "baseline-b"):
        sys_instance = TwoAgentBaseline()
    else:
        sys_instance = SingleLLMBaseline()

    eval_report = harness.evaluate(sys_instance, incident_id=incident_id)

    agent_steps = {}
    if system == "aletheia-3agent":
        mas = AletheiaMultiAgentSystem()
        ctx = mas.workflow.investigator.investigate(incident_id, alert_desc, items, timeline)
        ana = mas.workflow.analyst.analyze(ctx)
        ver = mas.workflow.verifier.verify(ana, ctx)
        agent_steps = {
            "investigator": ctx.model_dump(),
            "analyst": ana.model_dump(),
            "verifier": ver.model_dump(),
        }

    return {
        "incident_id": incident_id,
        "system": system,
        "diagnosis": eval_report.diagnosis.model_dump() if eval_report.diagnosis else {},
        "evaluation": eval_report.model_dump(),
        "agent_steps": agent_steps,
        "telemetry_count": len(items),
        "timeline_events": [e.model_dump() for e in timeline.get_events()],
    }
