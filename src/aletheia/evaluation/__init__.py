"""Aletheia Evaluation and Benchmarking Package."""

from aletheia.evaluation.models import (
    DiagnosisResult,
    MetricScore,
    EvaluationReport,
    DiagnosticSystem,
)
from aletheia.evaluation.llm.client import (
    BaseLLMClient,
    MockLLMClient,
    MockMode,
    OpenAILLMClient,
    get_llm_client,
)
from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.harness import EvaluationHarness, get_evaluation_harness
from aletheia.evaluation.loader import load_ground_truth, load_incident_telemetry
from aletheia.evaluation.metrics import (
    score_root_cause,
    score_introduced_by,
    score_affected_service,
    score_evidence_citations,
    calculate_overall_score,
)

__all__ = [
    "DiagnosisResult",
    "MetricScore",
    "EvaluationReport",
    "DiagnosticSystem",
    "BaseLLMClient",
    "MockLLMClient",
    "MockMode",
    "OpenAILLMClient",
    "get_llm_client",
    "SingleLLMBaseline",
    "EvaluationHarness",
    "get_evaluation_harness",
    "load_ground_truth",
    "load_incident_telemetry",
    "score_root_cause",
    "score_introduced_by",
    "score_affected_service",
    "score_evidence_citations",
    "calculate_overall_score",
]
