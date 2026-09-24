"""Evaluation metrics measuring diagnostic accuracy, attribution, evidence precision/recall, and hallucinations."""

from typing import Any, Dict, List, Set, Tuple

from aletheia.evidence.schema import EvidenceItem, EvidenceType
from aletheia.evaluation.models import DiagnosisResult, MetricScore
from aletheia.models.incident import IncidentGroundTruth


def score_root_cause(
    diagnosis: DiagnosisResult,
    ground_truth: IncidentGroundTruth,
) -> MetricScore:
    """Evaluate whether the diagnosis accurately identified the verified root cause."""
    gt_cause = ground_truth.root_cause.lower()
    details = ground_truth.ground_truth_details
    regression_type = details.get("regression_type", "").lower()

    diag_cause = (diagnosis.root_cause or "").lower()
    diag_cat = (diagnosis.root_cause_category or "").lower()
    diag_expl = (diagnosis.explanation or "").lower()
    combined_text = f"{diag_cause} {diag_cat} {diag_expl}"

    # Disqualification / Severe penalty for known false causes
    false_causes = ["memory_leak", "memory leak", "jvm", "garbage collection", "out of memory", "oom", "network_partition"]
    for false_cause in false_causes:
        if false_cause in diag_cat or (false_cause in diag_cause and "not" not in diag_cause):
            return MetricScore(
                metric_name="root_cause_accuracy",
                score=0.0,
                passed=False,
                details={"penalized_for": false_cause, "ground_truth": gt_cause},
                explanation=f"Diagnosis incorrectly identified root cause as '{false_cause}' instead of '{gt_cause}'.",
            )

    score = 0.0
    matches = []

    # Category match
    if diag_cat == gt_cause or gt_cause in diag_cat:
        score += 0.5
        matches.append("category_match")
    elif any(k in diag_cause for k in ["database query", "db query", "slow query", "database latency"]):
        score += 0.4
        matches.append("query_latency_mentioned")

    # Specific regression mechanism match (unindexed / sequential scan / missing index / table scan)
    mechanism_keywords = ["unindexed", "missing index", "without index", "sequential scan", "table scan", "index"]
    if any(k in combined_text for k in mechanism_keywords):
        score += 0.5
        matches.append("regression_mechanism_identified")

    score = min(1.0, score)
    passed = score >= 0.70

    return MetricScore(
        metric_name="root_cause_accuracy",
        score=score,
        passed=passed,
        details={"matches": matches, "ground_truth_cause": gt_cause, "regression_type": regression_type},
        explanation=(
            f"Correctly identified root cause ({', '.join(matches)})"
            if passed
            else f"Partially or incorrectly identified root cause (score: {score:.1%})"
        ),
    )


def score_introduced_by(
    diagnosis: DiagnosisResult,
    ground_truth: IncidentGroundTruth,
) -> MetricScore:
    """Evaluate whether the diagnosis accurately attributed the incident to the commit or deployment."""
    gt_introduced = (ground_truth.introduced_by or "").lower()
    commit_meta = ground_truth.ground_truth_details.get("commit_metadata", {})
    gt_commit_id = commit_meta.get("commit_id", "").lower()
    gt_version = commit_meta.get("deployment_version", "").lower()

    diag_introduced = (diagnosis.introduced_by or "").lower()
    combined_text = f"{diag_introduced} {(diagnosis.explanation or '').lower()}"

    if diag_introduced in ("unknown", "none", "", "n/a"):
        return MetricScore(
            metric_name="introduced_by_accuracy",
            score=0.0,
            passed=False,
            details={"status": "unattributed"},
            explanation="Diagnosis failed to identify the commit or deployment that introduced the issue.",
        )

    score = 0.0
    matches = []

    # Check commit match (e.g. abc12348f9 or abc123)
    if (gt_commit_id and gt_commit_id[:6] in combined_text) or "abc123" in combined_text:
        score += 0.6
        matches.append(f"commit:{gt_commit_id[:8]}")

    # Check deployment version match (e.g. v4.2.1)
    if gt_version and gt_version in combined_text:
        score += 0.4
        matches.append(f"version:{gt_version}")

    # Penalize wrong commit citations
    if "0000deadbeef" in combined_text or "9999" in combined_text:
        score = 0.0
        matches = ["hallucinated_commit"]

    score = min(1.0, score)
    passed = score >= 0.60

    return MetricScore(
        metric_name="introduced_by_accuracy",
        score=score,
        passed=passed,
        details={"matches": matches, "ground_truth_commit": gt_commit_id, "ground_truth_version": gt_version},
        explanation=(
            f"Accurately attributed to {', '.join(matches)}"
            if passed
            else f"Incomplete or incorrect attribution (score: {score:.1%})"
        ),
    )


def score_affected_service(
    diagnosis: DiagnosisResult,
    ground_truth: IncidentGroundTruth,
) -> MetricScore:
    """Evaluate whether the diagnosis accurately identified the affected service and component."""
    gt_service = ground_truth.affected_service.lower()
    gt_component = ground_truth.ground_truth_details.get("component", "postgresql").lower()

    diag_service = (diagnosis.affected_service or "").lower()
    diag_comp = (diagnosis.suspected_component or "").lower()

    score = 0.0
    matches = []

    if diag_service == gt_service or gt_service in diag_service:
        score += 0.6
        matches.append(f"service:{gt_service}")

    if gt_component in diag_comp or "postgres" in diag_comp or "database" in diag_comp or "orders" in diag_comp:
        score += 0.4
        matches.append(f"component:{gt_component}")

    score = min(1.0, score)
    passed = score >= 0.60

    return MetricScore(
        metric_name="service_accuracy",
        score=score,
        passed=passed,
        details={"matches": matches, "expected_service": gt_service, "expected_component": gt_component},
        explanation=f"Identified {', '.join(matches)}" if matches else "Failed to identify service and component.",
    )


def score_evidence_citations(
    diagnosis: DiagnosisResult,
    ground_truth: IncidentGroundTruth,
    available_evidence: List[EvidenceItem],
) -> Tuple[MetricScore, MetricScore, MetricScore]:
    """Evaluate Evidence Recall, Evidence Precision, and Hallucination Count."""
    available_ids = {e.evidence_id for e in available_evidence}
    evidence_by_id = {e.evidence_id: e for e in available_evidence}

    cited_ids = diagnosis.cited_evidence_ids or []

    # 1. Hallucination Check: Citing IDs that do not exist in the prompt context
    hallucinated_ids = [cid for cid in cited_ids if cid not in available_ids]
    if hallucinated_ids:
        hallucination_penalty = max(0.0, 1.0 - 0.5 * len(hallucinated_ids))
        hallucination_score = MetricScore(
            metric_name="evidence_hallucination",
            score=hallucination_penalty,
            passed=False,
            details={"hallucinated_ids": hallucinated_ids, "count": len(hallucinated_ids)},
            explanation=f"Cited {len(hallucinated_ids)} nonexistent evidence IDs: {hallucinated_ids}",
        )
    else:
        hallucination_score = MetricScore(
            metric_name="evidence_hallucination",
            score=1.0,
            passed=True,
            details={"hallucinated_ids": [], "count": 0},
            explanation="No hallucinated evidence IDs cited.",
        )

    # 2. Evidence Recall: Matching Ground Truth Expected Evidence
    # Expected categories in INC-001:
    # - "deployment_v4.2.1"
    # - "commit_abc123"
    # - "increased_db_latency"
    # - "increased_checkout_latency"
    matched_expected = set()
    valid_cited_items = [evidence_by_id[cid] for cid in cited_ids if cid in evidence_by_id]

    for item in valid_cited_items:
        # Check deployment
        if item.type == EvidenceType.DEPLOYMENT and "v4.2.1" in (item.content + str(item.data)):
            matched_expected.add("deployment_v4.2.1")
        # Check commit
        if item.type == EvidenceType.COMMIT and "abc123" in (item.content + str(item.data)):
            matched_expected.add("commit_abc123")
        # Check database latency
        if item.type == EvidenceType.SPAN and ("orders" in item.content or "db" in item.content):
            matched_expected.add("increased_db_latency")
        # Check checkout latency
        if item.type in (EvidenceType.METRIC, EvidenceType.LOG) and ("1500" in item.content or "1.5" in item.content or "delay" in item.content or "duration" in item.content):
            matched_expected.add("increased_checkout_latency")

    expected_total = len(ground_truth.expected_evidence)
    recall_score_val = (len(matched_expected) / expected_total) if expected_total > 0 else 1.0
    evidence_recall_score = MetricScore(
        metric_name="evidence_recall",
        score=round(recall_score_val, 3),
        passed=recall_score_val >= 0.75,
        details={
            "matched_expected": list(matched_expected),
            "missing_expected": [exp for exp in ground_truth.expected_evidence if exp not in matched_expected],
            "total_expected": expected_total,
        },
        explanation=f"Uncovered {len(matched_expected)}/{expected_total} expected evidence items.",
    )

    # 3. Evidence Precision: Fraction of cited items that are relevant vs irrelevant noise
    # Relevant items are those addressing the regression chain
    relevant_count = 0
    for item in valid_cited_items:
        if item.type in (EvidenceType.DEPLOYMENT, EvidenceType.COMMIT, EvidenceType.SPAN):
            relevant_count += 1
        elif item.type == EvidenceType.METRIC and (item.data.get("value", 0) > 1.0 or "1.5" in item.content):
            relevant_count += 1
        elif item.type == EvidenceType.LOG and "regression" in item.content.lower():
            relevant_count += 1

    total_cited = len(cited_ids)
    if total_cited == 0:
        precision_val = 0.0
    else:
        precision_val = relevant_count / total_cited

    evidence_precision_score = MetricScore(
        metric_name="evidence_precision",
        score=round(precision_val, 3),
        passed=precision_val >= 0.70,
        details={"relevant_count": relevant_count, "total_cited": total_cited},
        explanation=f"{relevant_count}/{total_cited} cited evidence items were relevant.",
    )

    return evidence_recall_score, evidence_precision_score, hallucination_score


def calculate_overall_score(
    root_cause_score: MetricScore,
    introduced_by_score: MetricScore,
    service_score: MetricScore,
    evidence_recall_score: MetricScore,
    evidence_precision_score: MetricScore,
    hallucination_score: MetricScore,
) -> float:
    """Calculate normalized composite score with hallucination penalty."""
    weights = {
        "root_cause": 0.35,
        "introduced_by": 0.20,
        "service": 0.15,
        "recall": 0.20,
        "precision": 0.10,
    }

    raw_score = (
        weights["root_cause"] * root_cause_score.score
        + weights["introduced_by"] * introduced_by_score.score
        + weights["service"] * service_score.score
        + weights["recall"] * evidence_recall_score.score
        + weights["precision"] * evidence_precision_score.score
    )

    # Hallucination deduction
    if hallucination_score.score < 1.0:
        raw_score *= hallucination_score.score

    return round(max(0.0, min(1.0, raw_score)), 3)
