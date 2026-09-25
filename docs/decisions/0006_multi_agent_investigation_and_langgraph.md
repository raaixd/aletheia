# ADR 0006: Multi-Agent Investigation Architecture with LangGraph Orchestration

## Status
Accepted

## Context
In Phase 5, we established Baseline A (Single-LLM context dump) and the Evaluation Harness. While a single LLM can parse dumped telemetry, real incident investigations suffer from cognitive bias, ungrounded speculation, anchoring on symptoms rather than root causes, and citing fabricated/hallucinated evidence.

To resolve these failure modes, we required a multi-stage diagnostic architecture:
```
Deterministic Evidence Graph
             ↓
        Investigator (Relevance filtering & context extraction)
             ↓
          Analyst (Multi-hypothesis generation & contradiction mapping)
             ↓
          Verifier (Temporal ordering, causal challenge & final diagnosis)
```

## Architectural Decisions

1. **Separation of Concerns across 3 Agents**:
   - **Investigator**: Interrogates the deterministic Evidence Graph, filters out irrelevant background noise (e.g. healthy baseline metrics), extracts key entities, extracts chronological timeline events, and produces structured observations strictly backed by valid evidence IDs.
   - **Analyst**: Ingests the `InvestigationContext` and produces *multiple* candidate hypotheses. It explicitly maps supporting evidence, contradicting evidence (e.g. symptoms that refute alternative explanations), and missing evidence (e.g. slow query logs or flamegraphs). It disallows anchoring to a single premature conclusion and distinguishes correlation from causation.
   - **Verifier**: Functions as an adversarial reviewer. It audits each hypothesis against temporal ordering (cause must precede effect), checks whether claimed causal mechanisms are backed by telemetry, rejects hypotheses contradicted by observations, catches hallucinated IDs, and allows an explicit `insufficient_evidence` verdict when data is inadequate.

2. **LangGraph as an Orchestration Primitive, Not the Intelligence**:
   - Agent reasoning and evidence queries are encapsulated in clean, testable agent classes (`Investigator`, `Analyst`, `Verifier`).
   - `langgraph.graph.StateGraph` manages the state transitions (`investigate` -> `analyze` -> `verify` -> `END`).
   - The deterministic Evidence Graph remains the single source of truth; LangGraph merely directs the control flow.

3. **Strict Evidence Provenance and Ground-Truth Isolation**:
   - Neither the Investigator, Analyst, nor Verifier is ever provided access to `IncidentGroundTruth` or ground-truth files.
   - All cited evidence IDs are verified against known IDs in the Evidence Graph.
   - Any hallucinated IDs are immediately rejected and penalized by the Evaluation Harness.

## Consequences

- **Strengths**:
  - Deterministic tests verify each agent independently before orchestration.
  - Verifier demonstrably catches incorrect hypotheses, temporal contradictions, and unsupported causal assertions.
  - Compatible with `EvaluationHarness` through the `BaseDiagnosticSystem` adapter (`AletheiaMultiAgentSystem`).
- **Trade-offs**:
  - Increases total pipeline steps compared to a single-shot prompt, but dramatically improves evidence recall, precision, and hallucination resistance.
