"""Evaluation API endpoints for triggering benchmarks and inspecting scorecards."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.harness import get_evaluation_harness
from aletheia.evaluation.llm.client import MockLLMClient, MockMode, OpenAILLMClient
from aletheia.evaluation.models import EvaluationReport

router = APIRouter(prefix="/api/v1/eval", tags=["Evaluation & Benchmarks"])


class EvalRunRequest(BaseModel):
    """Payload to trigger an evaluation run."""
    incident_id: str = Field("INC-001", description="Target incident ID")
    baseline: str = Field("single-llm", description="Diagnostic baseline (e.g. 'single-llm')")
    mock_mode: Optional[str] = Field(
        "accurate",
        description="Simulation mode: 'accurate', 'hallucinated', 'partial', 'invalid_json'",
    )
    use_live_llm: bool = Field(False, description="Set True to invoke live OpenAI-compatible LLM")
    model: Optional[str] = Field(None, description="Model identifier for live LLM")


class BaselineInfo(BaseModel):
    id: str
    name: str
    description: str


@router.get("/baselines", response_model=List[BaselineInfo])
def list_baselines() -> List[BaselineInfo]:
    """List all available diagnostic baselines and systems."""
    return [
        BaselineInfo(
            id="single-llm",
            name="Baseline A: Single-LLM Context Dump",
            description="Feeds all observable alerts, logs, metrics, and timeline into a single LLM prompt for root cause diagnosis.",
        ),
        BaselineInfo(
            id="aletheia-3agent",
            name="Aletheia: 3-Agent Multi-Agent System",
            description="Specialized Investigator -> Analyst -> Verifier architecture with causal discrimination and temporal validation.",
        ),
    ]


@router.post("/run", response_model=EvaluationReport)
def run_evaluation(request: EvalRunRequest) -> EvaluationReport:
    """Execute diagnostic evaluation against ground truth and return comprehensive scorecard."""
    from aletheia.agents.orchestrator import AletheiaMultiAgentSystem

    harness = get_evaluation_harness()

    supported = ["single-llm", "aletheia-3agent"]
    if request.baseline not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported baseline '{request.baseline}'. Supported: {supported}",
        )

    if request.use_live_llm:
        client = OpenAILLMClient(model=request.model)
        label = request.model or "openai"
    else:
        try:
            mode = MockMode(request.mock_mode or "accurate")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mock_mode '{request.mock_mode}'. Valid: {[m.value for m in MockMode]}",
            )
        client = MockLLMClient(mode=mode, model_name=f"mock-{mode.value}")
        label = f"mock:{mode.value}"

    if request.baseline == "single-llm":
        system = SingleLLMBaseline(name=f"Baseline-A-Single-LLM ({label})", llm_client=client)
    else:
        system = AletheiaMultiAgentSystem(name=f"Aletheia-3Agent ({label})", llm_client=client)

    try:
        report = harness.evaluate(system=system, incident_id=request.incident_id)
        return report
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}")


@router.get("/reports", response_model=List[EvaluationReport])
def list_reports(limit: int = Query(20, ge=1, le=100)) -> List[EvaluationReport]:
    """List recent evaluation reports."""
    harness = get_evaluation_harness()
    reports = harness.list_reports()
    return reports[:limit]


@router.get("/reports/{report_id}", response_model=EvaluationReport)
def get_report(report_id: str) -> EvaluationReport:
    """Retrieve full details and scorecard for a specific evaluation report."""
    harness = get_evaluation_harness()
    report = harness.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Evaluation report '{report_id}' not found.")
    return report
