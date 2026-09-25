"""Integration tests for Phase 7 Incident Benchmark & Comparative Evaluation."""

import pytest
from aletheia.agents.orchestrator import AletheiaMultiAgentSystem
from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.baselines.two_agent import TwoAgentBaseline
from aletheia.evaluation.harness import EvaluationHarness
from aletheia.evaluation.loader import load_ground_truth, load_incident_telemetry


def test_twenty_incidents_load_without_ground_truth_leakage():
    """Verify all 20 benchmark incidents load observable telemetry and isolated ground truth."""
    incident_ids = [f"INC-{i:03d}" for i in range(1, 21)]

    for inc_id in incident_ids:
        # Load ground truth
        gt = load_ground_truth(inc_id)
        assert gt.incident_id == inc_id
        assert len(gt.root_cause) > 0
        assert len(gt.expected_evidence) > 0

        # Load telemetry
        alert, items, timeline = load_incident_telemetry(inc_id)
        assert len(alert) > 0
        assert len(items) >= 2
        assert len(timeline.get_events()) >= 1

        # Check strict isolation: no ground truth object in telemetry items
        for it in items:
            assert "IncidentGroundTruth" not in str(it.data)


def test_two_agent_baseline_runs_on_inc_001():
    alert, items, timeline = load_incident_telemetry("INC-001")
    baseline_b = TwoAgentBaseline()
    diag = baseline_b.diagnose("INC-001", alert, items, timeline)

    assert diag.incident_id == "INC-001"
    assert "database" in diag.root_cause.lower()
    assert len(diag.cited_evidence_ids) > 0
    assert diag.usage_metadata.get("agent_pipeline") == ["Investigator", "Analyst"]


def test_comparative_benchmark_execution():
    """Run comparative benchmark across a subset of diverse incidents (e.g. INC-001 to INC-005)."""
    harness = EvaluationHarness()
    target_incidents = [f"INC-{i:03d}" for i in range(1, 6)]

    report = harness.evaluate_comparative_benchmark(incident_ids=target_incidents)

    assert len(report.incidents_evaluated) == 5
    assert "Baseline-A (Single-LLM)" in report.system_summaries
    assert "Baseline-B (2-Agent)" in report.system_summaries
    assert "Aletheia (3-Agent)" in report.system_summaries

    table = report.format_markdown_table()
    assert "Root-Cause Accuracy" in table
    assert "Evidence Recall" in table
    assert "Hallucination Rate" in table

    s3 = report.system_summaries["Aletheia (3-Agent)"]
    assert s3.mean_overall_score >= 0.70
    assert s3.hallucination_rate == 0.0
