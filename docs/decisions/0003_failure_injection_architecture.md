# ADR 0003: Controlled Failure Injection and Ground Truth Isolation

## Context

To test and measure an incident investigation AI system, incidents must be reproducible, deterministic, and accompanied by unambiguous ground truth. If failures are uncontrolled or injected destructively, automated regression testing and repeatable evaluations become impossible.

## Decisions

1. **Strict Separation of Ground Truth**:
   - Ground truth definitions are stored under `incidents/ground_truth/`.
   - Ground truth schemas (`IncidentGroundTruth`) are used solely by evaluation harnesses and integration tests. Agents are strictly prohibited from querying ground truth files during investigations.

2. **In-Process Failure Manager with API/CLI Controls**:
   - Implemented `FailureInjectionManager` to dynamically activate/deactivate failures in memory without restarting services or modifying container images.
   - Provided both REST endpoints (`/api/simulator/inject`, `/api/simulator/reset`, `/api/simulator/incidents`) and CLI commands (`python -m simulator.failure_injection.cli`).

3. **Observable Injected Symptoms**:
   - INC-001 (Database Query Regression) deliberately injects both elapsed latency and a distinct OpenTelemetry child span (`db.query: SELECT orders (unindexed)`).
   - This ensures that later investigation agents can discover concrete evidence in logs, traces, and metrics rather than guessing.

## Consequences

- Any incident can be turned on or off with a single command or API call.
- Zero destructive database modification required for query regression tests.
- Perfect foundation for Phase 4 (Evidence Model & Graph).
