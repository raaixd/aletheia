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
    regression_type = str(details.get("regression_type", "")).lower()

    diag_cause = (diagnosis.root_cause or "").lower()
    diag_cat = (diagnosis.root_cause_category or "").lower()
    diag_expl = (diagnosis.explanation or "").lower()
    combined_text = f"{diag_cause} {diag_cat} {diag_expl}"

    # Disqualification for claiming a completely contraindicated cause
    # e.g. claiming jvm/memory leak when ground truth is database query, or vice versa
    if "memory" not in gt_cause and "oom" not in gt_cause:
        for fc in ["jvm", "garbage collection"]:
            if fc in combined_text and "not" not in diag_cause:
                return MetricScore(
                    metric_name="root_cause_accuracy",
                    score=0.0,
                    passed=False,
                    details={"penalized_for": fc, "ground_truth": gt_cause},
                    explanation=f"Diagnosis incorrectly claimed '{fc}' which is contraindicated for '{gt_cause}'.",
                )

    score = 0.0
    matches = []

    # 1. Category / Root cause match
    gt_tokens = [t for t in gt_cause.replace("_", " ").split() if len(t) > 2]
    matched_tokens = [t for t in gt_tokens if t in combined_text]

    if diag_cat == gt_cause or gt_cause in diag_cat:
        score += 0.5
        matches.append("category_match")
    elif len(matched_tokens) >= max(1, len(gt_tokens) // 2):
        score += 0.5
        matches.append(f"cause_tokens:{','.join(matched_tokens)}")
    elif any(k in diag_cause for k in ["database query", "db query", "slow query", "database latency"]):
        score += 0.4
        matches.append("query_latency_mentioned")

    # 2. Specific regression mechanism match
    if regression_type and regression_type in combined_text:
        score += 0.5
        matches.append("mechanism_identified")
    elif regression_type:
        reg_tokens = [t for t in regression_type.replace("_", " ").split() if len(t) > 2]
        if reg_tokens and all(t in combined_text for t in reg_tokens):
            score += 0.5
            matches.append("mechanism_identified")
        elif any(t in combined_text for t in reg_tokens):
            score += 0.3
            matches.append("partial_mechanism_match")
    elif any(k in combined_text for k in ["table scan", "sequential scan", "missing index", "unindexed"]):
        score += 0.5
        matches.append("mechanism_identified")

    score = min(1.0, score)
    passed = score >= 0.60

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
    """Evaluate whether the diagnosis accurately attributed the incident to the commit, deployment, or actor."""
    gt_introduced = (ground_truth.introduced_by or "").lower()
    commit_meta = ground_truth.ground_truth_details.get("commit_metadata", {})
    gt_commit_id = str(commit_meta.get("commit_id", "")).lower()
    gt_version = str(commit_meta.get("deployment_version", "")).lower()

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

    # Check commit match
    if gt_commit_id and gt_commit_id[:6] in combined_text:
        score += 0.6
        matches.append(f"commit:{gt_commit_id[:8]}")

    # Check deployment version match
    if gt_version and gt_version in combined_text:
        score += 0.4
        matches.append(f"version:{gt_version}")

    # Check general introduced_by token match if no commit metadata
    if not gt_commit_id and gt_introduced:
        gt_intro_tokens = [t for t in gt_introduced.replace("_", " ").split() if len(t) > 3]
        if any(t in combined_text for t in gt_intro_tokens):
            score += 0.8
            matches.append(f"actor:{gt_introduced}")

    # Penalize wrong commit citations
    if "0000deadbeef" in combined_text or "fake" in combined_text:
        score = 0.0
        matches = ["hallucinated_commit"]

    score = min(1.0, score)
    passed = score >= 0.50

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
    gt_component = str(ground_truth.ground_truth_details.get("component", "")).lower()

    diag_service = (diagnosis.affected_service or "").lower()
    diag_comp = (diagnosis.suspected_component or "").lower()
    combined_diag = f"{diag_service} {diag_comp} {(diagnosis.root_cause or '').lower()}"

    score = 0.0
    matches = []

    if gt_service in diag_service or diag_service in gt_service:
        score += 0.6
        matches.append(f"service:{gt_service}")

    if gt_component:
        comp_tokens = [t for t in gt_component.replace("_", " ").split() if len(t) > 3]
        if any(t in combined_diag for t in comp_tokens) or gt_component in combined_diag:
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

    # 2. Evidence Recall: Matching Ground Truth Expected Evidence categories
    matched_expected = set()
    valid_cited_items = [evidence_by_id[cid] for cid in cited_ids if cid in evidence_by_id]

    for expected_cat in ground_truth.expected_evidence:
        exp_clean = expected_cat.lower().replace("_", " ")
        exp_tokens = [t for t in exp_clean.split() if len(t) >= 2]

        for item in valid_cited_items:
            content_str = (item.content + " " + str(item.data) + " " + item.type.value).lower()
            if any(t in content_str for t in exp_tokens):
                matched_expected.add(expected_cat)
                break
            elif "deployment" in exp_clean and item.type == EvidenceType.DEPLOYMENT:
                matched_expected.add(expected_cat)
                break
            elif "commit" in exp_clean and item.type == EvidenceType.COMMIT:
                matched_expected.add(expected_cat)
                break
            elif ("db" in exp_clean or "database" in exp_clean) and item.type == EvidenceType.SPAN and any(k in content_str for k in ["db", "query", "sql", "select", "orders", "postgres"]):
                matched_expected.add(expected_cat)
                break
            elif "checkout" in exp_clean and (
                item.type in (EvidenceType.SPAN, EvidenceType.METRIC)
                and any(k in content_str for k in ["checkout", "cart", "/checkout", "order_create"])
            ):
                matched_expected.add(expected_cat)
                break

    expected_total = len(ground_truth.expected_evidence)
    recall_score_val = (len(matched_expected) / expected_total) if expected_total > 0 else 1.0
    evidence_recall_score = MetricScore(
        metric_name="evidence_recall",
        score=round(recall_score_val, 3),
        passed=recall_score_val >= 0.60,
        details={
            "matched_expected": list(matched_expected),
            "missing_expected": [exp for exp in ground_truth.expected_evidence if exp not in matched_expected],
            "total_expected": expected_total,
        },
        explanation=f"Uncovered {len(matched_expected)}/{expected_total} expected evidence items.",
    )

    # 3. Evidence Precision: Fraction of cited items that are relevant vs irrelevant noise
    relevant_count = 0
    for item in valid_cited_items:
        # Deployments, Commits, Spans with errors or duration, anomaly metrics, error logs are relevant
        if item.type in (EvidenceType.DEPLOYMENT, EvidenceType.COMMIT, EvidenceType.SPAN):
            relevant_count += 1
        elif item.type == EvidenceType.METRIC:
            val = float(item.data.get("value", 0.0) or 0.0)
            if val > 0.1 or "error" in str(item.data.get("metric_name", "")).lower():
                relevant_count += 1
        elif item.type == EvidenceType.LOG:
            level = str(item.data.get("level", "")).upper()
            if level in ("WARNING", "ERROR", "CRITICAL") or any(k in item.content.lower() for k in ["regression", "slow", "timeout", "fail", "error"]):
                relevant_count += 1

    total_cited = len(cited_ids)
    if total_cited == 0:
        precision_val = 0.0
    else:
        precision_val = relevant_count / total_cited

    evidence_precision_score = MetricScore(
        metric_name="evidence_precision",
        score=round(precision_val, 3),
        passed=precision_val >= 0.60,
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
