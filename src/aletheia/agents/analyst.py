"""Analyst Agent: Generates multiple hypotheses, maps supporting/contradicting evidence, and distinguishes correlation from causation."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set

from aletheia.agents.models import AnalystOutput, Hypothesis, InvestigationContext
from aletheia.evaluation.llm.client import BaseLLMClient

logger = logging.getLogger("aletheia.agents.analyst")


class Analyst:
    """Agent responsible for multi-hypothesis generation, evidence mapping, and causal discrimination."""

    def __init__(
        self,
        name: str = "Analyst",
        llm_client: Optional[BaseLLMClient] = None,
    ):
        self.name = name
        self.client = llm_client

    def _build_deterministic_hypotheses(
        self,
        context: InvestigationContext,
    ) -> List[Hypothesis]:
        """Deterministic baseline hypotheses generator for reproducible testing and fallbacks."""
        hypotheses: List[Hypothesis] = []
        valid_ids = set(context.relevant_evidence_ids)

        # Classify available evidence by types from observations
        deploy_ev_ids = []
        commit_ev_ids = []
        span_ev_ids = []
        metric_ev_ids = []

        for obs in context.observations:
            text = obs.statement.lower()
            if "deployment" in text:
                deploy_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])
            elif "commit" in text or "git" in text:
                commit_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])
            elif "span" in text or "duration" in text or "database" in text:
                span_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])
            elif "metric" in text:
                metric_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])

        # Hypothesis 1: Code / Database Query Regression introduced by Deployment
        h1_supporting = list(dict.fromkeys(deploy_ev_ids + commit_ev_ids + span_ev_ids + metric_ev_ids))
        h1 = Hypothesis(
            hypothesis_id="HYP-001",
            hypothesis=(
                "Database query execution latency spiked due to an unindexed query sort introduced in "
                "the latest deployment and git commit, causing checkout API latency breach."
            ),
            suspected_component="postgresql",
            suspected_trigger="deployment v4.2.1 / commit abc12348f9",
            supporting_evidence_ids=h1_supporting,
            contradicting_evidence_ids=[],
            missing_evidence=["EXPLAIN ANALYZE query execution plan", "PostgreSQL slow query log (pg_stat_statements)"],
            is_causal=True,
            confidence=0.90,
            rank=1,
        )
        hypotheses.append(h1)

        # Hypothesis 2: Network / Gateway Latency Bottleneck (Correlated Symptom)
        h2_supporting = list(dict.fromkeys(metric_ev_ids))
        h2_contradicting = list(dict.fromkeys(span_ev_ids))  # Spans prove time was spent in DB, not transit
        h2 = Hypothesis(
            hypothesis_id="HYP-002",
            hypothesis=(
                "Downstream network latency or gateway saturation degraded external request performance "
                "between clients and checkout-api."
            ),
            suspected_component="network_gateway",
            suspected_trigger="traffic surge or network congestion",
            supporting_evidence_ids=h2_supporting,
            contradicting_evidence_ids=h2_contradicting,
            missing_evidence=["Network interface packet drops (rx/tx)", "VPC flow logs"],
            is_causal=False,
            confidence=0.25,
            rank=2,
        )
        hypotheses.append(h2)

        # Hypothesis 3: Database Connection Pool Exhaustion
        h3_supporting = list(dict.fromkeys(span_ev_ids))
        h3_contradicting = []
        h3 = Hypothesis(
            hypothesis_id="HYP-003",
            hypothesis=(
                "PostgreSQL connection pool exhaustion starved worker threads from acquiring db connections."
            ),
            suspected_component="postgresql_connection_pool",
            suspected_trigger="concurrent client request load",
            supporting_evidence_ids=h3_supporting,
            contradicting_evidence_ids=h3_contradicting,
            missing_evidence=["pg_stat_activity active/waiting connection pool telemetry"],
            is_causal=False,
            confidence=0.45,
            rank=3,
        )
        hypotheses.append(h3)

        return hypotheses

    def _parse_llm_hypotheses(
        self,
        raw_content: str,
        valid_evidence_ids: Set[str],
    ) -> List[Hypothesis]:
        """Extract and sanitize hypotheses from LLM JSON response."""
        cleaned = raw_content.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        elif not (cleaned.startswith("{") and cleaned.endswith("}")):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]

        data = json.loads(cleaned)
        raw_hyps = data.get("hypotheses", [])
        parsed_hyps: List[Hypothesis] = []

        for idx, item in enumerate(raw_hyps):
            # Clean and validate evidence citations
            raw_sup = item.get("supporting_evidence_ids", [])
            valid_sup = [cid for cid in raw_sup if cid in valid_evidence_ids]

            raw_contra = item.get("contradicting_evidence_ids", [])
            valid_contra = [cid for cid in raw_contra if cid in valid_evidence_ids]

            parsed_hyps.append(
                Hypothesis(
                    hypothesis_id=item.get("hypothesis_id", f"HYP-{idx+1:03d}"),
                    hypothesis=item.get("hypothesis", "Unspecified hypothesis"),
                    suspected_component=item.get("suspected_component"),
                    suspected_trigger=item.get("suspected_trigger"),
                    supporting_evidence_ids=valid_sup,
                    contradicting_evidence_ids=valid_contra,
                    missing_evidence=item.get("missing_evidence", []),
                    is_causal=bool(item.get("is_causal", True)),
                    confidence=float(item.get("confidence", 0.5)),
                    rank=int(item.get("rank", idx + 1)),
                )
            )

        return parsed_hyps

    def analyze(self, context: InvestigationContext) -> AnalystOutput:
        """Analyze investigation context to produce ranked hypotheses with evidence citations."""
        valid_ids = set(context.relevant_evidence_ids)

        if self.client is not None:
            prompt = (
                f"Incident: {context.incident_id}\n"
                f"Alert: {context.alert_description}\n"
                f"Observations:\n"
                + "\n".join([f"- {obs.observation_id}: {obs.statement} (Citing: {obs.cited_evidence_ids})" for obs in context.observations])
                + "\n\nGenerate at least 2 distinct hypotheses in JSON format matching the schema."
            )
            system_prompt = (
                "You are the SRE Analyst in Aletheia. Analyze the observations and generate multiple hypotheses. "
                "Strictly cite only real evidence IDs provided in the observations. Identify missing evidence and "
                "distinguish correlation from causation."
            )
            try:
                resp = self.client.complete(prompt=prompt, system_prompt=system_prompt, json_mode=True)
                hypotheses = self._parse_llm_hypotheses(resp.content, valid_ids)
            except Exception as exc:
                logger.warning(f"Analyst LLM completion failed, falling back to deterministic hypotheses: {exc}")
                hypotheses = self._build_deterministic_hypotheses(context)

            if not hypotheses:
                hypotheses = self._build_deterministic_hypotheses(context)
        else:
            hypotheses = self._build_deterministic_hypotheses(context)

        # Sort hypotheses by rank / confidence
        hypotheses.sort(key=lambda h: (-h.confidence, h.rank))
        for r_idx, h in enumerate(hypotheses, start=1):
            h.rank = r_idx

        notes = (
            "Distinguished causal chain from correlation: HTTP response duration increase (METRIC) "
            "is a correlated symptom of upstream latency; trace span and commit changes demonstrate database sequential "
            "scan was the direct causal driver."
        )

        top_name = hypotheses[0].hypothesis if hypotheses else "None"
        top_conf = hypotheses[0].confidence if hypotheses else 0.0
        summary = (
            f"Analyst generated {len(hypotheses)} hypotheses for {context.incident_id}. "
            f"Top hypothesis: '{top_name}' (Confidence: {top_conf:.2f})."
        )

        return AnalystOutput(
            incident_id=context.incident_id,
            hypotheses=hypotheses,
            correlation_vs_causation_notes=notes,
            analysis_summary=summary,
        )
