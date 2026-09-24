"""Unit tests for diagnostic evaluation metrics."""

import pytest
from datetime import datetime, timezone

from aletheia.evaluation.metrics import (
    calculate_overall_score,
    score_affected_service,
    score_evidence_citations,
    score_introduced_by,
    score_root_cause,
)
from aletheia.evaluation.models import DiagnosisResult, MetricScore
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance
from aletheia.models.incident import IncidentGroundTruth


@pytest.fixture
def inc_001_gt():
    return IncidentGroundTruth(
        incident_id="INC-001",
        name="database_query_regression",
        root_cause="slow_database_query",
        introduced_by="commit_abc123",
        affected_service="checkout-api",
        start_time="2026-09-25T02:00:00Z",
        expected_evidence=[
            "deployment_v4.2.1",
            "commit_abc123",
            "increased_db_latency",
            "increased_checkout_latency",
        ],
        ground_truth_details={
            "affected_endpoints": ["/api/orders"],
            "component": "postgresql",
            "table": "orders",
            "regression_type": "unindexed_sequential_scan",
            "commit_metadata": {
                "commit_id": "abc12348f9",
                "author": "alex.dev@example.com",
                "message": "refactor(checkout): update order history lookup without index",
                "deployment_version": "v4.2.1",
            },
        },
    )


def test_score_root_cause_accurate(inc_001_gt):
    diag = DiagnosisResult(
        incident_id="INC-001",
        root_cause="Unindexed query causing slow database scans",
        root_cause_category="slow_database_query",
        explanation="Sequential scan on orders table without index",
    )
    score = score_root_cause(diag, inc_001_gt)
    assert score.score == 1.0
    assert score.passed is True


def test_score_root_cause_false_cause(inc_001_gt):
    diag = DiagnosisResult(
        incident_id="INC-001",
        root_cause="JVM memory leak and GC pause",
        root_cause_category="memory_leak",
        explanation="OutOfMemoryError in heap",
    )
    score = score_root_cause(diag, inc_001_gt)
    assert score.score == 0.0
    assert score.passed is False


def test_score_introduced_by_accurate(inc_001_gt):
    diag = DiagnosisResult(
        incident_id="INC-001",
        root_cause="Slow query",
        introduced_by="commit abc12348f9 in release v4.2.1",
    )
    score = score_introduced_by(diag, inc_001_gt)
    assert score.score == 1.0
    assert score.passed is True


def test_score_introduced_by_unknown(inc_001_gt):
    diag = DiagnosisResult(
        incident_id="INC-001",
        root_cause="Slow query",
        introduced_by="unknown",
    )
    score = score_introduced_by(diag, inc_001_gt)
    assert score.score == 0.0
    assert score.passed is False


def test_score_affected_service(inc_001_gt):
    diag = DiagnosisResult(
        incident_id="INC-001",
        root_cause="Slow query",
        affected_service="checkout-api",
        suspected_component="postgresql",
    )
    score = score_affected_service(diag, inc_001_gt)
    assert score.score == 1.0
    assert score.passed is True


def test_score_evidence_citations_and_hallucination(inc_001_gt):
    provenance = EvidenceProvenance(
        source_type=EvidenceSourceType.GITHUB,
        source_uri="github://releases",
        extracted_at=datetime.now(timezone.utc),
        extraction_method="test",
    )
    available_evidence = [
        EvidenceItem(
            evidence_id="EV-DEP-0001",
            timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
            source=EvidenceSourceType.GITHUB,
            type=EvidenceType.DEPLOYMENT,
            service="checkout-api",
            content="Deployed v4.2.1",
            provenance=provenance,
        ),
        EvidenceItem(
            evidence_id="EV-GIT-0001",
            timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
            source=EvidenceSourceType.GITHUB,
            type=EvidenceType.COMMIT,
            service="checkout-api",
            content="Commit abc123",
            provenance=provenance,
        ),
        EvidenceItem(
            evidence_id="EV-SPAN-0001",
            timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
            source=EvidenceSourceType.OPENTELEMETRY,
            type=EvidenceType.SPAN,
            service="checkout-api",
            content="db.query orders 1500ms",
            provenance=provenance,
        ),
    ]

    # Valid citations
    diag = DiagnosisResult(
        incident_id="INC-001",
        root_cause="Slow query",
        cited_evidence_ids=["EV-DEP-0001", "EV-GIT-0001", "EV-SPAN-0001"],
    )
    recall, prec, hall = score_evidence_citations(diag, inc_001_gt, available_evidence)
    assert hall.passed is True
    assert hall.score == 1.0
    assert prec.score == 1.0
    assert recall.score == 0.75  # 3 of 4 expected evidence

    # Hallucinated citations
    diag_hall = DiagnosisResult(
        incident_id="INC-001",
        root_cause="Memory leak",
        cited_evidence_ids=["EV-FAKE-9999", "EV-NO-SUCH-ITEM"],
    )
    recall_h, prec_h, hall_h = score_evidence_citations(diag_hall, inc_001_gt, available_evidence)
    assert hall_h.passed is False
    assert hall_h.score == 0.0
    assert len(hall_h.details["hallucinated_ids"]) == 2


def test_calculate_overall_score():
    perfect = MetricScore(metric_name="m", score=1.0, passed=True)
    zero = MetricScore(metric_name="m", score=0.0, passed=False)

    score = calculate_overall_score(perfect, perfect, perfect, perfect, perfect, perfect)
    assert score == 1.0

    score_fail = calculate_overall_score(zero, zero, zero, zero, zero, perfect)
    assert score_fail == 0.0

    # Test hallucination penalty dampening
    score_hall = calculate_overall_score(perfect, perfect, perfect, perfect, perfect, zero)
    assert score_hall == 0.0
