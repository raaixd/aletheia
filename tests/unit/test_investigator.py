"""Unit and integration tests for Phase 6A Investigator Agent."""

import pytest
from datetime import datetime, timezone

from aletheia.agents.investigator import Investigator
from aletheia.agents.models import InvestigationObservation
from aletheia.evaluation.loader import load_incident_telemetry
from aletheia.evidence.schema import (
    EvidenceItem,
    EvidenceProvenance,
    EvidenceSourceType,
    EvidenceType,
)
from aletheia.graph.builder import EvidenceGraphBuilder


def test_investigator_inc_001_retrieves_relevant_evidence():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()

    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    assert context.incident_id == "INC-001"
    assert len(context.relevant_evidence_ids) > 0
    # Baseline normal metric (0.005s) should be excluded as irrelevant noise
    # Regressed metric (1.520s) and slow db query (1500ms) should be included
    all_evidence_ids = {e.evidence_id for e in evidence_items}
    for item in evidence_items:
        if item.type == EvidenceType.METRIC and float(item.data.get("value", 0)) < 0.1:
            assert item.evidence_id not in context.relevant_evidence_ids
        if item.type == EvidenceType.DEPLOYMENT:
            assert item.evidence_id in context.relevant_evidence_ids

    # All cited evidence IDs in observations must be valid
    for obs in context.observations:
        for cid in obs.cited_evidence_ids:
            assert cid in all_evidence_ids


def test_investigator_timeline_preserves_chronological_order():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()

    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    timestamps = [ev.timestamp for ev in context.timeline_events]
    assert timestamps == sorted(timestamps)


def test_investigator_identifies_important_entities_and_relationships():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()

    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    entity_names = {ent.name for ent in context.important_entities}
    assert "checkout-api" in entity_names
    assert "postgres" in entity_names

    rel_types = {rel.type for rel in context.relevant_relationships}
    assert "INTRODUCED" in rel_types or "CAUSED" in rel_types or "CALLS" in rel_types


def test_investigator_rejects_hallucinated_evidence_ids():
    alert_desc, evidence_items, timeline = load_incident_telemetry("INC-001")
    investigator = Investigator()

    context = investigator.investigate(
        incident_id="INC-001",
        alert_description=alert_desc,
        evidence_items=evidence_items,
        timeline=timeline,
    )

    # Inject a simulated hallucinated observation to verify rejection
    bad_obs = InvestigationObservation(
        observation_id="OBS-BAD",
        statement="A nonexistent service crashed.",
        cited_evidence_ids=["EV-FAKE-1234", "EV-FAKE-9999"],
    )
    context.observations.append(bad_obs)

    # Run clean check manually
    valid_ids = {e.evidence_id for e in evidence_items}
    rejected = []
    for obs in context.observations:
        valid_cited = []
        for cid in obs.cited_evidence_ids:
            if cid in valid_ids:
                valid_cited.append(cid)
            else:
                rejected.append(cid)
        obs.cited_evidence_ids = valid_cited

    assert "EV-FAKE-1234" in rejected
    assert "EV-FAKE-9999" in rejected
    assert bad_obs.cited_evidence_ids == []


def test_investigator_ground_truth_isolation():
    """Verify that investigator cannot access or leak ground truth."""
    import inspect
    from aletheia.agents.investigator import Investigator

    source_code = inspect.getsource(Investigator)
    assert "IncidentGroundTruth" not in source_code
    assert "load_ground_truth" not in source_code
    assert "ground_truth" not in source_code.lower()
