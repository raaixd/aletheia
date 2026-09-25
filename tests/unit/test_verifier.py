"""Unit and integration tests for Phase 6C Verifier Agent."""

import pytest
from datetime import datetime, timezone

from aletheia.agents.analyst import Analyst
from aletheia.agents.investigator import Investigator
from aletheia.agents.models import AnalystOutput, Hypothesis, InvestigationContext
from aletheia.agents.verifier import Verifier
from aletheia.evaluation.loader import load_incident_telemetry


def test_verifier_when_analyst_is_correct():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate("INC-001", alert_desc, evidence_items, timeline)

    analyst = Analyst()
    analyst_output = analyst.analyze(context)

    verifier = Verifier()
    verif_output = verifier.verify(analyst_output, context)

    assert verif_output.verdict == "verified"
    assert verif_output.best_hypothesis is not None
    assert verif_output.best_hypothesis.hypothesis_id == "HYP-001"
    assert verif_output.final_diagnosis is not None
    assert "database" in verif_output.final_diagnosis.root_cause.lower()
    assert verif_output.final_diagnosis.confidence >= 0.80


def test_verifier_catches_and_rejects_intentionally_wrong_hypothesis():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate("INC-001", alert_desc, evidence_items, timeline)

    # Intentionally wrong hypothesis: JVM memory leak on python/postgres stack
    wrong_hyp = Hypothesis(
        hypothesis_id="HYP-WRONG-001",
        hypothesis="JVM garbage collection pause and memory leak caused outage",
        suspected_component="jvm_heap",
        suspected_trigger="commit deadbeef",
        supporting_evidence_ids=["EV-FAKE-9999"],  # Hallucinated ID
        contradicting_evidence_ids=[],
        missing_evidence=[],
        is_causal=True,
        confidence=0.99,
        rank=1,
    )
    analyst_output = AnalystOutput(
        incident_id="INC-001",
        hypotheses=[wrong_hyp],
        analysis_summary="Wrong analysis",
    )

    verifier = Verifier()
    verif_output = verifier.verify(analyst_output, context)

    # Verifier must catch the hallucinated ID, contraindicated JVM claim, and reject it
    assert verif_output.verdict == "all_hypotheses_rejected"
    assert verif_output.best_hypothesis is None
    assert len(verif_output.challenges) == 1
    challenge = verif_output.challenges[0]
    assert challenge.passed_verification is False
    assert not challenge.causal_claims_supported or len(challenge.contradictions_detected) > 0


def test_verifier_catches_contradictory_evidence():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate("INC-001", alert_desc, evidence_items, timeline)

    # Hypothesis with explicit contradicting evidence
    valid_id = context.relevant_evidence_ids[0]
    contra_hyp = Hypothesis(
        hypothesis_id="HYP-CONTRA",
        hypothesis="Network gateway buffer overflow",
        suspected_component="gateway",
        suspected_trigger="traffic surge",
        supporting_evidence_ids=[],
        contradicting_evidence_ids=[valid_id],  # Contradicted by valid telemetry
        missing_evidence=["router metrics"],
        is_causal=False,
        confidence=0.30,
        rank=1,
    )
    analyst_output = AnalystOutput(
        incident_id="INC-001",
        hypotheses=[contra_hyp],
        analysis_summary="Contradicted analysis",
    )

    verifier = Verifier()
    verif_output = verifier.verify(analyst_output, context)

    assert verif_output.verdict == "all_hypotheses_rejected"
    challenge = verif_output.challenges[0]
    assert challenge.passed_verification is False
    assert len(challenge.contradictions_detected) > 0


def test_verifier_catches_temporal_ordering_violation():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate("INC-001", alert_desc, evidence_items, timeline)

    # Hypothesis claiming post-incident event caused the problem
    temporal_violation_hyp = Hypothesis(
        hypothesis_id="HYP-TIME",
        hypothesis="Configuration update caused database slowdown",
        suspected_component="config",
        suspected_trigger="Post-incident rollback config update",
        supporting_evidence_ids=[context.relevant_evidence_ids[0]],
        contradicting_evidence_ids=[],
        missing_evidence=[],
        is_causal=True,
        confidence=0.85,
        rank=1,
    )
    analyst_output = AnalystOutput(
        incident_id="INC-001",
        hypotheses=[temporal_violation_hyp],
        analysis_summary="Temporal violation analysis",
    )

    verifier = Verifier()
    verif_output = verifier.verify(analyst_output, context)

    challenge = verif_output.challenges[0]
    assert challenge.temporal_ordering_valid is False
    assert challenge.passed_verification is False


def test_verifier_handles_insufficient_evidence():
    empty_context = InvestigationContext(
        incident_id="INC-EMPTY",
        alert_description="Alert with no telemetry",
        relevant_evidence_ids=[],
    )
    empty_analyst_output = AnalystOutput(
        incident_id="INC-EMPTY",
        hypotheses=[],
    )

    verifier = Verifier()
    verif_output = verifier.verify(empty_analyst_output, empty_context)

    assert verif_output.verdict == "insufficient_evidence"
    assert verif_output.final_diagnosis is not None
    assert verif_output.final_diagnosis.confidence == 0.0
    assert "insufficient evidence" in verif_output.final_diagnosis.root_cause.lower()


def test_verifier_ground_truth_isolation():
    """Verify that Verifier has no imports or access to ground truth."""
    import inspect
    from aletheia.agents.verifier import Verifier

    source_code = inspect.getsource(Verifier)
    assert "IncidentGroundTruth" not in source_code
    assert "load_ground_truth" not in source_code
    assert "ground_truth" not in source_code.lower()
