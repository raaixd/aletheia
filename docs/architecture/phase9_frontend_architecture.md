# Phase 9: Developer-Grade Investigation Frontend

## Architecture Overview
The Phase 9 frontend is built as a developer-first web application designed for root cause analysis and postmortem investigation.

### 1. Technology Stack
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailored Obsidian Design System (Vanilla CSS with CSS custom properties)
- **Proxy**: Next.js URL rewrites routing `/api/backend/*` to FastAPI backend on `http://127.0.0.1:8000/*`

### 2. Information Architecture
```
Aletheia Web Console
├── Top Bar: Brand, Scenario Selector, Engine Toggle, Navigation Links
├── Navigation Views:
│   ├── Investigation (Primary Linear Narrative)
│   │   ├── Incident Header (ID, Severity, Service, Status, Trigger Alert)
│   │   ├── Timeline Rail (Chronological order of commits, deploys, spans, metrics)
│   │   ├── Evidence Layer (Itemized evidence cards with provenance & raw inspect modal)
│   │   ├── Analyst Hypotheses (Ranked explanations with supporting vs contradicting facts)
│   │   ├── Verifier Challenges (Adversarial audits of temporal order and causation)
│   │   └── Final Diagnosis (Hero panel: Verified Root Cause, Fix, Attribution, Confidence)
│   ├── Incidents (Catalog of 20 benchmark scenarios with search and severity filter)
│   ├── Evidence Graph (Focused causal DAG tracing deployment -> commit -> query -> latency)
│   ├── Evaluations (3-Way Comparative Benchmark: Single-LLM vs 2-Agent vs 3-Agent Aletheia)
│   └── System (LLMOps traces, token accounting, latency percentiles, error rates)
```

### 3. API Integration
The frontend consumes live data from the following backend endpoints:
- `GET /api/v1/investigation/incidents` -> Catalog of all 20 incident scenarios.
- `POST /api/v1/investigation/diagnose/{incident_id}?system={system}` -> Triggers full investigation pipeline and returns multi-agent intermediate steps and diagnosis scorecard.
- `GET /api/v1/llmops/traces?limit=12` -> Fetches recent LLM interaction traces and telemetry.

### 4. Verification & Testing
- Static compilation: `npm run build` succeeds with zero errors.
- Python integration test suite: `tests/` passes 98/98 unit and integration tests.
- End-to-end proxy integration: Validated with `scripts/test_ui_api_integration.py`.
