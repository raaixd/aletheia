"""FastAPI route handlers for LLMOps, structured execution traces, and experiment comparison."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from aletheia.evaluation.models import ComparativeBenchmarkReport, EvaluationReport
from aletheia.reliability.store import EvaluationComparisonDiff, get_evaluation_store
from aletheia.reliability.traces import LLMCallTrace, LLMOpsMetricsSummary, get_trace_recorder

router = APIRouter(prefix="/api/v1/llmops", tags=["LLMOps & Reliability"])


class RunComparisonRequest(BaseModel):
    run_a_id: str
    run_b_id: str


@router.get("/traces", response_model=List[LLMCallTrace])
def list_traces(
    incident_id: Optional[str] = Query(None, description="Filter traces by incident ID"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    status: Optional[str] = Query(None, description="Filter by status (success, error, retried)"),
    limit: int = Query(50, ge=1, le=500),
):
    """Retrieve structured LLM and agent execution traces."""
    recorder = get_trace_recorder()
    return recorder.get_traces(
        incident_id=incident_id,
        agent_name=agent_name,
        status=status,
        limit=limit,
    )


@router.get("/metrics", response_model=LLMOpsMetricsSummary)
def get_metrics():
    """Retrieve aggregated operational LLMOps metrics (tokens, costs, latencies, failure rates)."""
    recorder = get_trace_recorder()
    return recorder.get_metrics_summary()


@router.get("/runs", response_model=List[EvaluationReport])
def list_evaluation_runs(
    incident_id: Optional[str] = Query(None, description="Filter runs by incident ID"),
    system_name: Optional[str] = Query(None, description="Filter by system name"),
    limit: int = Query(50, ge=1, le=200),
):
    """List historical evaluation runs stored on disk."""
    store = get_evaluation_store()
    return store.list_runs(incident_id=incident_id, system_name=system_name, limit=limit)


@router.get("/runs/{report_id}", response_model=EvaluationReport)
def get_evaluation_run(report_id: str):
    """Retrieve details of a specific evaluation run."""
    store = get_evaluation_store()
    run = store.get_run(report_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{report_id}' not found.")
    return run


@router.get("/benchmarks", response_model=List[ComparativeBenchmarkReport])
def list_benchmarks(limit: int = Query(20, ge=1, le=50)):
    """List historical comparative benchmarks."""
    store = get_evaluation_store()
    return store.list_benchmarks(limit=limit)


@router.get("/benchmarks/{benchmark_id}", response_model=ComparativeBenchmarkReport)
def get_benchmark(benchmark_id: str):
    """Retrieve a specific comparative benchmark report."""
    store = get_evaluation_store()
    bench = store.get_benchmark(benchmark_id)
    if not bench:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")
    return bench


@router.post("/compare", response_model=EvaluationComparisonDiff)
def compare_runs(request: RunComparisonRequest):
    """Compare two evaluation runs and calculate performance/accuracy deltas."""
    store = get_evaluation_store()
    run_a = store.get_run(request.run_a_id)
    if not run_a:
        raise HTTPException(status_code=404, detail=f"Run A '{request.run_a_id}' not found.")
    run_b = store.get_run(request.run_b_id)
    if not run_b:
        raise HTTPException(status_code=404, detail=f"Run B '{request.run_b_id}' not found.")

    return store.compare_runs(run_a, run_b)
