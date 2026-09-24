# ADR 0005: Single-LLM Baseline and Evaluation Harness

## Status
Accepted

## Date
2026-09-25

## Context
Aletheia is designed to investigate production incidents by organizing evidence into a time-aware representation and generating defensible hypotheses. A central project requirement is that the system must be measured empirically when its diagnosis is incorrect.

Before building multi-agent systems (Investigator, Analyst, Verifier), we needed an objective, repeatable evaluation framework that:
1. Operates under strict ground truth isolation (preventing diagnostic systems from accessing the answers).
2. Quantitatively evaluates root cause accuracy, attribution, service identification, evidence citation recall, evidence precision, and hallucinated evidence IDs.
3. Provides a clean single-LLM baseline against which more sophisticated multi-agent architectures can be benchmarked.

## Decisions

1. **Explicit Ground Truth Isolation**:
   - Diagnostic systems are strictly provided with observable telemetry: incident alerts, evidence items, and event timelines.
   - Ground truth files (`incidents/ground_truth/`) are accessed solely by the [EvaluationHarness](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/harness.py) during scoring.

2. **Decoupled LLM Client with Deterministic Mocking**:
   - Created [BaseLLMClient](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/llm/client.py) with [MockLLMClient](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/llm/client.py) supporting preset modes (`accurate`, `hallucinated`, `partial`, `invalid_json`) and [OpenAILLMClient](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/llm/client.py) for live HTTP execution via standard `httpx`.
   - Allows unit and integration tests to run hermetically in milliseconds with zero external API dependencies or costs.

3. **Multi-Dimensional Scoring**:
   - Root Cause Accuracy (35%): Evaluates category and causal mechanism while penalizing false claims.
   - Attribution Accuracy (20%): Evaluates commit and release version identification.
   - Affected Service & Component (15%): Evaluates service and subsystem identification.
   - Evidence Citation Recall (20%): Measures fraction of ground truth expected evidence uncovered.
   - Evidence Citation Precision (10%): Measures relevance of cited items vs noise.
   - Hallucination Penalty: Specifically audits cited Evidence IDs against the context catalog, dampening scores when fabricated IDs are cited.

4. **Structured JSON Output Discipline**:
   - Mandated [DiagnosisResult](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/models.py) with fallback handlers for markdown code fences and unparsable output.

## Consequences
- Multi-agent architectures developed in subsequent phases (Phase 6+) can immediately plug into [EvaluationHarness](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/harness.py) via the [DiagnosticSystem](file:///c:/Users/Raaid/Downloads/aletheia/src/aletheia/evaluation/models.py) interface.
- Benchmark scorecards can be compared quantitatively across architectures (Baseline A vs Baseline B vs System C).
