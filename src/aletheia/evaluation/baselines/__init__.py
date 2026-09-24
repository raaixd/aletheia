"""Evaluation baselines package."""

from aletheia.evaluation.baselines.base import BaseDiagnosticSystem
from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline

__all__ = [
    "BaseDiagnosticSystem",
    "SingleLLMBaseline",
]
