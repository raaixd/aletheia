"""Integration tests for EvaluationHarness on INC-001 Database Query Regression."""

import pytest
from typing import List, Optional

from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.harness import EvaluationHarness
from aletheia.evaluation.llm.client import MockLLMClient, MockMode
from aletheia.evaluation.models import DiagnosisResult
from aletheia.evidence.events import Timeline
from aletheia.evidence.schema import EvidenceItem


def test_eval_harness_accurate_mode_passes():
    client = MockLLMClient(mode=MockMode.ACCURATE)
    system = SingleLLMBaseline(name="baseline-accurate", llm_client=client)
    harness = EvaluationHarness()

    report = harness.evaluate(system=system, incident_id="INC-001")

    assert report.incident_id == "INC-001"
    assert report.overall_score >= 0.90
    assert report.root_cause_score.passed is True
    assert report.root_cause_score.score == 1.0
    assert report.introduced_by_score.passed is True
    assert report.service_score.passed is True
    assert report.evidence_recall_score.score == 1.0
    assert report.evidence_precision_score.score == 1.0
    assert report.hallucination_score.passed is True
    assert report.hallucination_score.details["count"] == 0
    assert "PASS" in report.format_ascii()


def test_eval_harness_partial_mode_intermediate_score():
    client = MockLLMClient(mode=MockMode.PARTIAL)
    system = SingleLLMBaseline(name="baseline-partial", llm_client=client)
    harness = EvaluationHarness()

    report = harness.evaluate(system=system, incident_id="INC-001")

    assert report.incident_id == "INC-001"
    # Partial identifies DB latency and service, but misses commit attribution and some evidence
    assert 0.40 <= report.overall_score <= 0.65
    assert report.root_cause_score.score == 0.50
    assert report.introduced_by_score.passed is False
    assert report.evidence_recall_score.score == 0.50
    assert report.hallucination_score.passed is True


def test_eval_harness_hallucinated_mode_fails_and_penalizes():
    client = MockLLMClient(mode=MockMode.HALLUCINATED)
    system = SingleLLMBaseline(name="baseline-hallucinated", llm_client=client)
    harness = EvaluationHarness()

    report = harness.evaluate(system=system, incident_id="INC-001")

    assert report.overall_score == 0.0
    assert report.root_cause_score.passed is False
    assert report.root_cause_score.score == 0.0
    assert report.hallucination_score.passed is False
    assert report.hallucination_score.details["count"] >= 1
    assert "EV-FAKE-9999" in report.hallucination_score.details["hallucinated_ids"]


def test_eval_harness_ground_truth_isolation():
    """Verify that the diagnostic system is NEVER passed ground truth objects or clues."""
    received_contexts = []

    class SnoopingDiagnosticSystem:
        name = "snooper"

        def diagnose(
            self,
            incident_id: str,
            alert_description: str,
            evidence_items: List[EvidenceItem],
            timeline: Optional[Timeline] = None,
        ) -> DiagnosisResult:
            received_contexts.append({
                "alert": alert_description,
                "evidence": evidence_items,
                "timeline": timeline,
            })
            return DiagnosisResult(
                incident_id=incident_id,
                root_cause="Isolation check",
                explanation="No ground truth present in inputs",
            )

    harness = EvaluationHarness()
    system = SnoopingDiagnosticSystem()
    report = harness.evaluate(system=system, incident_id="INC-001")

    assert len(received_contexts) == 1
    ctx = received_contexts[0]

    # Verify ground truth file/attributes are NOT in alert, evidence, or timeline
    assert "regression_type" not in ctx["alert"]
    assert "expected_evidence" not in ctx["alert"]

    for ev in ctx["evidence"]:
        # Verify evidence comes from adapters, not ground truth schema
        assert not hasattr(ev, "ground_truth_details")
        assert not hasattr(ev, "expected_evidence")
