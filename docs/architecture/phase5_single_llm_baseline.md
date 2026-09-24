# Aletheia Architecture: Phase 5 Single-LLM Baseline & Evaluation Harness

## Overview

Phase 5 establishes the empirical evaluation foundation of Aletheia. In accordance with the core project principle:

> *"The goal isn't to build an AI that guesses what went wrong. It's to build an investigation system that gathers evidence, constructs explanations, challenges them, and can be measured when it gets the diagnosis wrong."*

Before introducing complex multi-agent architectures (Investigator, Analyst, Verifier), we construct:
1. **The Evaluation Harness**: An isolated, objective scoring framework that measures diagnostic accuracy, attribution, evidence discipline, and hallucination penalties against verified Ground Truth.
2. **Baseline A (Single-LLM Context Dump)**: The standard baseline where observable telemetry (alerts, timeline, and raw evidence items) is serialized into a single prompt for a single LLM to analyze.

---

## 1. Ground Truth Isolation Guarantee

A fundamental architectural constraint in Aletheia is **strict isolation** between ground truth and diagnostic systems:

```
+-------------------------------------------------------------+
|                      EVALUATION HARNESS                     |
|                                                             |
|  +------------------------+      +------------------------+ |
|  |  Observable Telemetry  |      |   Ground Truth Store   | |
|  |  (Logs, Spans, Alerts) |      | (incidents/ground_truth)| |
|  +-----------+------------+      +-----------+------------+ |
|              |                               |              |
|              v                               v              |
|  +------------------------+      +------------------------+ |
|  |   Diagnostic System    |      |    Metric Evaluator    | |
|  |  (Baseline A / Agents) |      |   (Scoring & Auditing) | |
|  +-----------+------------+      +-----------+------------+ |
|              |                               ^              |
|              +-------- Diagnosis Output -----+              |
+-------------------------------------------------------------+
```

- **Diagnostic Systems (e.g. SingleLLMBaseline)** receive ONLY:
  - Incident ID & Alert description
  - Chronological timeline of observed events
  - Catalog of Evidence Items with IDs (`EV-DEP-0001`, `EV-GIT-0001`, `EV-SPAN-0001`, etc.)
- **Diagnostic Systems NEVER receive**:
  - Ground truth JSON files
  - Ground truth expected evidence lists
  - Ground truth root cause labels or answers

---

## 2. Baseline A: Single-LLM Architecture

Baseline A implements the standard prompt-engineering approach to incident diagnosis:
- **System Prompt**: Defines the persona as an expert SRE, enforces strict grounding in provided evidence, forbids fabricating evidence IDs, and mandates JSON output.
- **Context Serializer**: Formats the incident alert, formatted ASCII timeline, and evidence item catalog into a single coherent prompt.
- **JSON Extractor**: Robustly handles Markdown code fences (````json ... ````), extracts valid JSON, and maps it into a typed [DiagnosisResult](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/models.py).
- **Resource Tracking**: Measures wall-clock latency, prompt tokens, completion tokens, and estimates USD cost.

### Structured Output Schema (`DiagnosisResult`)
```json
{
  "incident_id": "INC-001",
  "root_cause": "Database query performance regression due to unindexed sort on the orders table",
  "root_cause_category": "slow_database_query",
  "suspected_component": "postgresql",
  "introduced_by": "commit abc12348f9 (deployment v4.2.1)",
  "affected_service": "checkout-api",
  "explanation": "Deployment v4.2.1 introduced commit abc12348f9...",
  "cited_evidence_ids": [
    "EV-DEP-0001",
    "EV-GIT-0001",
    "EV-SPAN-0001",
    "EV-METRIC-0002"
  ],
  "confidence": 0.95,
  "recommended_fix": "Add index on orders(created_at, user_id) or rollback deployment v4.2.1."
}
```

---

## 3. Evaluation Metrics Formulation

The evaluation harness scores a diagnosis across six orthogonal dimensions:

| Metric Dimension | Weight | Scoring Logic | Pass Threshold |
|---|---|---|---|
| **Root Cause Accuracy** | 35% | Evaluates category match and technical mechanism (e.g. unindexed query vs false claims like memory leaks/GC pauses). Disqualifies known false causes. | $\ge 70\%$ |
| **Introduced By (Attribution)** | 20% | Matches commit SHA (`abc12348f9` / `abc123`) and/or deployment version (`v4.2.1`). Penalizes "unknown" or wrong commits. | $\ge 60\%$ |
| **Affected Service & Component** | 15% | Matches primary service (`checkout-api`) and faulty component (`postgresql`/`orders`). | $\ge 60\%$ |
| **Evidence Citation Recall** | 20% | Fraction of ground truth `expected_evidence` categories matched by the diagnosis's cited evidence items ($4/4$ in INC-001). | $\ge 75\%$ |
| **Evidence Citation Precision** | 10% | Fraction of cited evidence items that are genuinely relevant to the failure chain versus irrelevant noise. | $\ge 70\%$ |
| **Hallucination Penalty** | Multiplier | Detects citations of nonexistent Evidence IDs (e.g. `EV-FAKE-9999`). If hallucinations occur, penalizes overall score proportionally. | $100\%$ (0 fake IDs) |

### Composite Score Formula
$$\text{Score}_{\text{composite}} = \left( 0.35 S_{\text{rc}} + 0.20 S_{\text{intro}} + 0.15 S_{\text{svc}} + 0.20 S_{\text{recall}} + 0.10 S_{\text{prec}} \right) \times S_{\text{hallucination}}$$

---

## 4. Benchmark Validation on INC-001

The evaluation harness was verified across four deterministic mock modes and test cases:

```
========================================================================
ALETHEIA EVALUATION SCORECARD SUMMARY: INC-001
========================================================================
Mode           | Overall | Root Cause | Attribution | Recall | Hallucinations
------------------------------------------------------------------------
Accurate       | 100.0%  | 100.0%     | 100.0%      | 100.0% | 0 (PASS)
Partial        | 52.5%   | 50.0%      | 0.0%        | 50.0%  | 0 (PASS)
Hallucinated   | 0.0%    | 0.0%       | 0.0%        | 0.0%   | 2 (FAIL)
Invalid JSON   | 0.0%    | 0.0%       | 0.0%        | 0.0%   | 0 (FAIL - Handled)
========================================================================
```

---

## 5. Inspection Interfaces

### 1. Command-Line Interface (CLI)
Run evaluation benchmark from terminal:
```bash
# Accurate model simulation
python -m aletheia.evaluation.cli --incident INC-001 --mock accurate

# Hallucinated model simulation
python -m aletheia.evaluation.cli --incident INC-001 --mock hallucinated

# Partial model simulation
python -m aletheia.evaluation.cli --incident INC-001 --mock partial

# Live OpenAI-compatible LLM
python -m aletheia.evaluation.cli --incident INC-001 --live --model gpt-4o-mini
```

### 2. REST API Endpoints
- `GET /api/v1/eval/baselines`: List registered evaluation baselines.
- `POST /api/v1/eval/run`: Trigger an evaluation run against an incident.
- `GET /api/v1/eval/reports`: List past evaluation reports and scorecards.
- `GET /api/v1/eval/reports/{report_id}`: Retrieve full evaluation report JSON.
