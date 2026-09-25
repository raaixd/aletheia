"""Unit and integration tests for Phase 6B Analyst Agent."""

import pytest
from aletheia.agents.analyst import Analyst
from aletheia.agents.investigator import Investigator
from aletheia.evaluation.loader import load_incident_telemetry


def test_analyst_generates_multiple_hypotheses_for_inc_001():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    analyst = Analyst()
    output = analyst.analyze(context)

    assert output.incident_id == "INC-001"
    assert len(output.hypotheses) >= 2
    # Verify hypotheses have distinct IDs and rankings
    hyp_ids = [h.hypothesis_id for h in output.hypotheses]
    assert len(hyp_ids) == len(set(hyp_ids))
    ranks = [h.rank for h in output.hypotheses]
    assert ranks == sorted(ranks)


def test_analyst_evidence_references_are_valid():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    analyst = Analyst()
    output = analyst.analyze(context)

    all_evidence_ids = {e.evidence_id for e in evidence_items}
    for hyp in output.hypotheses:
        for cid in hyp.supporting_evidence_ids:
            assert cid in all_evidence_ids
        for cid in hyp.contradicting_evidence_ids:
            assert cid in all_evidence_ids


def test_analyst_represents_contradictions_and_missing_evidence():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    analyst = Analyst()
    output = analyst.analyze(context)

    # At least one hypothesis should represent contradicting evidence (e.g. against the network red herring)
    has_contradicting = any(len(h.contradicting_evidence_ids) > 0 for h in output.hypotheses)
    assert has_contradicting

    # At least one hypothesis should represent missing evidence (e.g. pg_stat or explain plans)
    has_missing = any(len(h.missing_evidence) > 0 for h in output.hypotheses)
    assert has_missing


def test_analyst_distinguishes_correlation_from_causation():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()
    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    analyst = Analyst()
    output = analyst.analyze(context)

    assert "correlation" in output.correlation_vs_causation_notes.lower()
    # Top hypothesis should be causal, whereas secondary symptom is not
    assert output.hypotheses[0].is_causal is True


def test_analyst_ground_truth_isolation():
    """Verify that Analyst has no imports or access to ground truth."""
    import inspect
    from aletheia.agents.analyst import Analyst

    source_code = inspect.getsource(Analyst)
    assert "IncidentGroundTruth" not in source_code
    assert "load_ground_truth" not in source_code
    assert "ground_truth" not in source_code.lower()
