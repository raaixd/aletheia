"""LangGraph orchestration pipeline for the multi-agent incident diagnostic workflow.

Pipeline architecture:
Deterministic Evidence Graph
         ↓
    Investigator
         ↓
      Analyst
         ↓
     Verifier
         ↓
  Final Diagnosis
"""

import logging
import time
from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import END, START, StateGraph

from aletheia.agents.analyst import Analyst
from aletheia.agents.investigator import Investigator
from aletheia.agents.models import (
    AnalystOutput,
    InvestigationContext,
    VerifierOutput,
)
from aletheia.agents.verifier import Verifier
from aletheia.evaluation.baselines.base import BaseDiagnosticSystem
from aletheia.evaluation.llm.client import BaseLLMClient
from aletheia.evaluation.models import DiagnosisResult
from aletheia.evidence.events import Timeline
from aletheia.evidence.schema import EvidenceItem
from aletheia.graph.graph import EvidenceGraph

logger = logging.getLogger("aletheia.agents.orchestrator")


class MultiAgentState(TypedDict, total=False):
    """Execution state container flowing through the LangGraph multi-agent diagnostic graph."""
    incident_id: str
    alert_description: str
    evidence_items: List[EvidenceItem]
    timeline: Optional[Timeline]
    evidence_graph: Optional[EvidenceGraph]
    investigation_context: Optional[InvestigationContext]
    analyst_output: Optional[AnalystOutput]
    verifier_output: Optional[VerifierOutput]
    final_diagnosis: Optional[DiagnosisResult]
    execution_trace: List[str]


class AletheiaWorkflow:
    """Orchestrates Investigator, Analyst, and Verifier into a compiled LangGraph pipeline."""

    def __init__(
        self,
        investigator: Optional[Investigator] = None,
        analyst: Optional[Analyst] = None,
        verifier: Optional[Verifier] = None,
        llm_client: Optional[BaseLLMClient] = None,
    ):
        self.investigator = investigator or Investigator(llm_client=llm_client)
        self.analyst = analyst or Analyst(llm_client=llm_client)
        self.verifier = verifier or Verifier(llm_client=llm_client)
        self.graph = self._build_graph()

    def _node_investigate(self, state: MultiAgentState) -> Dict[str, Any]:
        logger.info(f"[{state['incident_id']}] Executing Investigator Agent...")
        trace = list(state.get("execution_trace", []))
        trace.append("Investigator: inspecting evidence graph and timeline")

        context = self.investigator.investigate(
            incident_id=state["incident_id"],
            alert_description=state["alert_description"],
            evidence_items=state["evidence_items"],
            timeline=state.get("timeline"),
            evidence_graph=state.get("evidence_graph"),
        )
        return {
            "investigation_context": context,
            "execution_trace": trace,
        }

    def _node_analyze(self, state: MultiAgentState) -> Dict[str, Any]:
        logger.info(f"[{state['incident_id']}] Executing Analyst Agent...")
        trace = list(state.get("execution_trace", []))
        trace.append("Analyst: generating hypotheses and mapping supporting/contradicting evidence")

        context = state["investigation_context"]
        output = self.analyst.analyze(context)
        return {
            "analyst_output": output,
            "execution_trace": trace,
        }

    def _node_verify(self, state: MultiAgentState) -> Dict[str, Any]:
        logger.info(f"[{state['incident_id']}] Executing Verifier Agent...")
        trace = list(state.get("execution_trace", []))
        trace.append("Verifier: auditing temporal ordering, causal claims, and contradictions")

        context = state["investigation_context"]
        analyst_output = state["analyst_output"]
        output = self.verifier.verify(analyst_output, context)

        final_diag = output.final_diagnosis
        trace.append(f"Verifier verdict: '{output.verdict}'")

        return {
            "verifier_output": output,
            "final_diagnosis": final_diag,
            "execution_trace": trace,
        }

    def _build_graph(self):
        builder = StateGraph(MultiAgentState)

        builder.add_node("investigate", self._node_investigate)
        builder.add_node("analyze", self._node_analyze)
        builder.add_node("verify", self._node_verify)

        builder.add_edge(START, "investigate")
        builder.add_edge("investigate", "analyze")
        builder.add_edge("analyze", "verify")
        builder.add_edge("verify", END)

        return builder.compile()

    def run(
        self,
        incident_id: str,
        alert_description: str,
        evidence_items: List[EvidenceItem],
        timeline: Optional[Timeline] = None,
        evidence_graph: Optional[EvidenceGraph] = None,
    ) -> MultiAgentState:
        """Execute the multi-agent diagnostic graph to completion."""
        initial_state: MultiAgentState = {
            "incident_id": incident_id,
            "alert_description": alert_description,
            "evidence_items": evidence_items,
            "timeline": timeline,
            "evidence_graph": evidence_graph,
            "execution_trace": [],
        }
        return self.graph.invoke(initial_state)


class AletheiaMultiAgentSystem(BaseDiagnosticSystem):
    """Adapter exposing the 3-agent LangGraph system to the EvaluationHarness."""

    def __init__(
        self,
        name: str = "Aletheia-3Agent-Investigator-Analyst-Verifier",
        workflow: Optional[AletheiaWorkflow] = None,
        llm_client: Optional[BaseLLMClient] = None,
    ):
        super().__init__(name=name)
        self.workflow = workflow or AletheiaWorkflow(llm_client=llm_client)

    def diagnose(
        self,
        incident_id: str,
        alert_description: str,
        evidence_items: List[EvidenceItem],
        timeline: Optional[Timeline] = None,
    ) -> DiagnosisResult:
        start_time = time.perf_counter()
        result_state = self.workflow.run(
            incident_id=incident_id,
            alert_description=alert_description,
            evidence_items=evidence_items,
            timeline=timeline,
        )
        latency = round(time.perf_counter() - start_time, 4)

        final_diagnosis = result_state.get("final_diagnosis")
        if final_diagnosis is None:
            final_diagnosis = DiagnosisResult(
                incident_id=incident_id,
                root_cause="Workflow execution produced no final diagnosis",
                root_cause_category="workflow_failure",
                suspected_component="unknown",
                introduced_by="unknown",
                affected_service="unknown",
                explanation="Multi-agent graph did not produce a final diagnosis result.",
                cited_evidence_ids=[],
                confidence=0.0,
                recommended_fix="Check workflow state transitions.",
            )

        # Attach telemetry usage metadata
        trace = result_state.get("execution_trace", [])
        final_diagnosis.usage_metadata = {
            "latency_seconds": latency,
            "agent_pipeline": ["Investigator", "Analyst", "Verifier"],
            "execution_trace": trace,
            "estimated_cost_usd": 0.0,
        }

        return final_diagnosis
