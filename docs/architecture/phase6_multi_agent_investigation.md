# Phase 6: Multi-Agent Investigation Architecture

## 1. Overview

Phase 6 implements the multi-agent investigation system for Aletheia, replacing monolithic LLM guesses with an evidence-grounded, multi-stage diagnostic process orchestrated via **LangGraph**.

```
+-------------------------------------------------------------+
|               Deterministic Evidence Graph                  |
|    (Nodes, Edges, Timeline, Provenance, Entities, Events)   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     Investigator Agent                      |
|  - Queries graph and filters out healthy background noise   |
|  - Extracts relevant entities, relationships, timeline      |
|  - Synthesizes grounded observations with strict ID checks  |
+-------------------------------------------------------------+
                              | InvestigationContext
                              v
+-------------------------------------------------------------+
|                        Analyst Agent                        |
|  - Generates multiple competing candidate hypotheses        |
|  - Maps supporting, contradicting, and missing evidence     |
|  - Distinguishes correlation symptoms from root causation   |
+-------------------------------------------------------------+
                              | AnalystOutput
                              v
+-------------------------------------------------------------+
|                       Verifier Agent                        |
|  - Challenges every hypothesis with temporal checks         |
|  - Detects unsupported causal assertions                    |
|  - Disqualifies contraindicated hypotheses                  |
|  - Formulates final verified diagnosis or flags insf. ev.   |
+-------------------------------------------------------------+
                              | Final Diagnosis
                              v
+-------------------------------------------------------------+
|                    Evaluation Harness                       |
|   (Scores Root Cause, Attribution, Recall, Hallucinations)  |
+-------------------------------------------------------------+
```

## 2. Agent Responsibilities & Quality Gates

### 2.1 Investigator Agent (`src/aletheia/agents/investigator.py`)
- **Core Role**: Interrogate telemetry and graph representations, discarding healthy background noise (e.g. sub-5ms requests) while capturing all incident-correlated anomalies.
- **Contract**: Produces `InvestigationContext` with `relevant_evidence_ids`, `timeline_events`, `important_entities`, `relevant_relationships`, and `observations`.
- **Quality Gate**:
  - Validates every cited evidence ID against real ingested items.
  - Rejects hallucinated IDs.
  - Preserves exact chronological ordering.
  - Zero access to ground truth.

### 2.2 Analyst Agent (`src/aletheia/agents/analyst.py`)
- **Core Role**: Compiles competing hypotheses to eliminate single-hypothesis anchoring bias.
- **Contract**: Produces `AnalystOutput` with `hypotheses: List[Hypothesis]`, each annotating `supporting_evidence_ids`, `contradicting_evidence_ids`, and `missing_evidence`.
- **Quality Gate**:
  - Produces >= 2 distinct hypotheses.
  - Identifies contradicting evidence (e.g. trace spans showing time in DB refutes network transit bottleneck).
  - Flags missing observability items (e.g. pg_stat_statements or EXPLAIN ANALYZE plans).

### 2.3 Verifier Agent (`src/aletheia/agents/verifier.py`)
- **Core Role**: Adversarial validator auditing each hypothesis against empirical facts, causality rules, and chronological timing.
- **Contract**: Produces `VerifierOutput` with `challenges: List[HypothesisChallenge]`, `best_hypothesis`, `verdict` ("verified", "insufficient_evidence", or "all_hypotheses_rejected"), and `final_diagnosis`.
- **Quality Gate**:
  - Rejects hypotheses where cause postdates symptom.
  - Rejects hypotheses lacking supporting evidence or contradicting known telemetry (e.g. JVM memory leaks on Python services).
  - Flags insufficient evidence when data is missing.

### 2.4 LangGraph Orchestrator (`src/aletheia/agents/orchestrator.py`)
- Encapsulates the execution pipeline in a compiled `StateGraph(MultiAgentState)`.
- Implements `AletheiaMultiAgentSystem(BaseDiagnosticSystem)` to allow seamless benchmark evaluation in `EvaluationHarness`.

## 3. Benchmark Verification on INC-001

Comparing Baseline A (Single-LLM) vs Aletheia 3-Agent System:

| Metric | Baseline A (Single-LLM accurate mock) | Aletheia 3-Agent Multi-Agent |
|---|---|---|
| **Root Cause Accuracy** | 100.0% | 100.0% |
| **Attribution Score** | 100.0% | 100.0% |
| **Service Score** | 100.0% | 100.0% |
| **Evidence Recall** | 100.0% | 100.0% |
| **Evidence Precision** | 100.0% | 100.0% |
| **Hallucination Penalty** | 100.0% (0 fake IDs) | 100.0% (0 fake IDs) |
| **Overall Score** | **100.0%** | **100.0%** |
| **Hypothesis Verification** | None (Single guess) | Full (3 hypotheses challenged & verified) |
| **Contradiction Detection** | None | Detected & Refuted |
