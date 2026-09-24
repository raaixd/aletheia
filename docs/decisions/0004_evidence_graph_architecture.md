# ADR 0004: Deterministic Evidence Graph and Temporal Modeling

## Context

A fundamental flaw of generic "AI for DevOps" systems is sending raw, unordered telemetry dumps into an LLM context window with the prompt *"What caused this?"*. This leads to hallucinated causal links, temporal confusion (mistaking effect for cause), and uncalibrated guesses.

To fulfill Aletheia's core principle, the incident investigation platform must first convert raw telemetry into a structured, time-aware **Evidence Graph** before any diagnostic reasoning takes place.

## Decisions

1. **No LLM in Evidence Graph Construction**:
   - The evidence graph is built deterministically from observable telemetry (logs, metrics, traces, Git commits, deployments).
   - Guarantees 100% reproducibility and prevents the LLM from becoming the observability database or fabricating nonexistent evidence.

2. **Explicit Evidence Provenance**:
   - Every `EvidenceItem` includes an `EvidenceProvenance` object specifying `source_type`, `source_uri`, `extracted_at`, `extraction_method`, and `raw_reference`.
   - Every graph edge connects to a list of backing `evidence_ids`. Every diagnosis can be traced to verifiable evidence IDs.

3. **Dual Temporal and Causal Edges**:
   - The graph simultaneously maintains:
     - **Causal / Structural Edges**: `INTRODUCED`, `MODIFIED`, `EXECUTES_ON`, `CALLS`, `INCREASED`, `CONTRIBUTED_TO`, `CAUSED`.
     - **Temporal Edges**: `PRECEDES` edges linking consecutive events in chronological order.
   - This enables diagnostic agents to verify whether an alleged cause strictly preceded an effect.

4. **Modular Adapter Pattern (`EvidenceSource`)**:
   - Created an abstract `EvidenceSource` with initial `LocalEvidenceSource` combining `LogAdapter`, `TraceAdapter`, `MetricAdapter`, and `DeployAdapter`.
   - Allows seamless drop-in of external data sources (`PrometheusEvidenceSource`, `GitHubEvidenceSource`, `SentryEvidenceSource`) in later phases without altering the graph builder.

5. **In-Memory Graph Query Engine**:
   - Implemented `EvidenceGraph` with DFS path-finding, temporal window filtering, and Mermaid export.
   - Kept zero external graph database dependencies for local execution while providing standard serialization.

## Consequences

- Diagnostic agents have access to structured graph queries (`find_paths`, `get_temporal_subgraph`, `get_neighbors`) rather than parsing raw text logs.
- Enables adversarial review in Phase 8 (Verifier can challenge hypotheses if temporal precedence or evidence links are violated).
