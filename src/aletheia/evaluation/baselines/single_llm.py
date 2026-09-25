"""Baseline A: Single-LLM incident diagnosis implementation."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from aletheia.evidence.events import Timeline
from aletheia.evidence.schema import EvidenceItem
from aletheia.evaluation.baselines.base import BaseDiagnosticSystem
from aletheia.evaluation.llm.client import BaseLLMClient, get_llm_client
from aletheia.evaluation.llm.prompts import BaselinePromptBuilder
from aletheia.evaluation.models import DiagnosisResult

logger = logging.getLogger("aletheia.eval.baseline.single_llm")


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate USD cost based on token counts and model pricing."""
    # Standard rates per 1,000,000 tokens
    pricing = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "mock-eval-model": {"input": 0.0, "output": 0.0},
        "mock": {"input": 0.0, "output": 0.0},
    }
    rates = pricing.get(model, {"input": 0.15, "output": 0.60})
    cost = (prompt_tokens / 1_000_000 * rates["input"]) + (completion_tokens / 1_000_000 * rates["output"])
    return round(cost, 6)


class SingleLLMBaseline(BaseDiagnosticSystem):
    """Baseline A: Dumps all telemetry, logs, metrics, and timeline into a single LLM prompt."""

    def __init__(
        self,
        name: str = "Baseline-A-Single-LLM",
        llm_client: Optional[BaseLLMClient] = None,
    ):
        super().__init__(name=name)
        self.client = llm_client or get_llm_client()

    def _extract_json(self, raw_text: str) -> Dict[str, Any]:
        """Robustly extract JSON object from markdown or raw LLM output."""
        cleaned = raw_text.strip()

        # Handle ```json ... ``` code blocks
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        elif cleaned.startswith("{") and cleaned.endswith("}"):
            pass
        else:
            # Fallback search for outer-most curly braces
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]

        return json.loads(cleaned)

    def diagnose(
        self,
        incident_id: str,
        alert_description: str,
        evidence_items: List[EvidenceItem],
        timeline: Optional[Timeline] = None,
    ) -> DiagnosisResult:
        """Query single LLM with full context dump and return structured diagnosis."""
        user_prompt = BaselinePromptBuilder.build_user_prompt(
            incident_id=incident_id,
            alert_description=alert_description,
            evidence_items=evidence_items,
            timeline=timeline,
        )

        try:
            resp = self.client.complete(
                prompt=user_prompt,
                system_prompt=BaselinePromptBuilder.SYSTEM_PROMPT,
                json_mode=True,
            )
        except Exception as exc:
            logger.error(f"LLM completion call failed: {exc}")
            return DiagnosisResult(
                incident_id=incident_id,
                root_cause=f"LLM API failure: {exc}",
                root_cause_category="api_error",
                suspected_component="unknown",
                introduced_by="unknown",
                affected_service="unknown",
                explanation=f"LLM completion call failed: {exc}",
                cited_evidence_ids=[],
                confidence=0.0,
                recommended_fix="Check LLM connectivity, credentials, and API status.",
                raw_response=str(exc),
                usage_metadata={"latency_seconds": 0.0, "estimated_cost_usd": 0.0},
            )

        cost = calculate_cost(resp.model, resp.prompt_tokens, resp.completion_tokens)
        usage_meta = {
            "model": resp.model,
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "total_tokens": resp.total_tokens,
            "latency_seconds": resp.latency_seconds,
            "estimated_cost_usd": cost,
        }

        try:
            parsed = self._extract_json(resp.content)
            return DiagnosisResult(
                incident_id=parsed.get("incident_id", incident_id),
                root_cause=parsed.get("root_cause", "Unspecified root cause"),
                root_cause_category=parsed.get("root_cause_category"),
                suspected_component=parsed.get("suspected_component"),
                introduced_by=parsed.get("introduced_by"),
                affected_service=parsed.get("affected_service"),
                explanation=parsed.get("explanation", ""),
                cited_evidence_ids=parsed.get("cited_evidence_ids", []),
                confidence=float(parsed.get("confidence", 0.8)),
                recommended_fix=parsed.get("recommended_fix", ""),
                raw_response=resp.content,
                usage_metadata=usage_meta,
            )
        except Exception as exc:
            logger.warning(f"Failed to parse LLM response as JSON: {exc}. Raw content: {resp.content[:200]}")
            return DiagnosisResult(
                incident_id=incident_id,
                root_cause=f"Model output parsing error: {exc}",
                root_cause_category="unknown",
                suspected_component="unknown",
                introduced_by="unknown",
                affected_service="unknown",
                explanation=f"The model failed to produce valid JSON: {resp.content}",
                cited_evidence_ids=[],
                confidence=0.0,
                recommended_fix="Review raw LLM output or retry.",
                raw_response=resp.content,
                usage_metadata=usage_meta,
            )
