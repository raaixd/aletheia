"""Integration tests for Phase 6D LangGraph multi-agent orchestration."""

import pytest
from aletheia.agents.orchestrator import AletheiaMultiAgentSystem, AletheiaWorkflow
from aletheia.evaluation.harness import EvaluationHarness
from aletheia.evaluation.loader import load_incident_telemetry


def test_langgraph_workflow_runs_end_to_end_on_inc_001():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    workflow = AletheiaWorkflow()

    state = workflow.run(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    # 1. Verify investigator executed and populated context
    assert "investigation_context" in state
    assert len(state["investigation_context"].relevant_evidence_ids) > 0

    # 2. Verify analyst executed and generated hypotheses
    assert "analyst_output" in state
    assert len(state["analyst_output"].hypotheses) >= 2

    # 3. Verify verifier executed, challenged hypotheses, and formed diagnosis
    assert "verifier_output" in state
    assert state["verifier_output"].verdict == "verified"
    assert state["final_diagnosis"] is not None
    assert "database" in state["final_diagnosis"].root_cause.lower()

    # 4. Verify execution trace captures pipeline progression
    trace = state.get("execution_trace", [])
    assert any("Investigator" in t for t in trace)
    assert any("Analyst" in t for t in trace)
    assert any("Verifier" in t for t in trace)


def test_aletheia_multi_agent_system_evaluation_harness_integration():
    harness = EvaluationHarness()
    system = AletheiaMultiAgentSystem()

    report = harness.evaluate(system, incident_id="INC-001")

    assert report.incident_id == "INC-001"
    assert report.system_name == "Aletheia-3Agent-Investigator-Analyst-Verifier"
    # Root cause accuracy must pass
    assert report.root_cause_score.passed is True
    # Zero hallucinated citations
    assert report.hallucination_score.details.get("count", 0) == 0
    # Overall score should be high (> 0.85)
    assert report.overall_score >= 0.85
    assert report.latency_seconds >= 0.0
