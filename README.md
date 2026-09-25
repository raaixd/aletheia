# Aletheia.

> *The goal isn't to build an AI that guesses what went wrong. It's to build an investigation system that gathers evidence, constructs explanations, challenges them, and can be measured when it gets the diagnosis wrong.*

Aletheia is an AI-powered incident investigation system for software systems. When a production system experiences an incident, Aletheia gathers evidence from multiple sources, aligns it in time, constructs an evidence graph, generates competing hypotheses, challenges them through an adversarial verifier, and outputs an evidence-backed diagnosis that can be measured against ground truth.

---

## Current Status: Phase 8 — Reliability & LLMOps Complete

- **Phase 1 (Foundation)**: Simulated checkout service, PostgreSQL 16, Docker Compose, automated product seeding, synthetic traffic generator.
- **Phase 2 (Observability)**: Correlated telemetry triad across all services (structured JSON logging, context-aware correlation IDs, Prometheus metrics, OpenTelemetry distributed tracing).
- **Phase 3 (Failure Injection)**: Controlled, reproducible failure injection system with ground truth isolation (`INC-001` database query regression).
- **Phase 4 (Evidence Model & Graph)**: Deterministic, time-aware evidence layer without an LLM (evidence schema, provenance, entity models, timeline, graph engine, and traversal).
- **Phase 5 (Single-LLM Baseline & Evaluation Harness)**:
  - **Ground Truth Isolation**: Diagnostic models are evaluated strictly against observable evidence, never given ground truth clues or answers.
  - **Baseline A (Single-LLM Context Dump)**: Full telemetry serialization into a structured diagnosis with strict JSON discipline.
  - **Six-Dimensional Evaluation Metrics**: Root cause accuracy, attribution accuracy, affected service/component, evidence recall, evidence precision, and hallucination penalty.
  - **Hermetic Mocking & Live LLM Client**: Built-in mock simulation modes (`accurate`, `hallucinated`, `partial`, `invalid_json`) and live OpenAI-compatible provider with robust error/timeout handling.
- **Phase 6 (Multi-Agent Investigation & LangGraph Orchestration)**:
  - **Investigator Agent**: Queries the deterministic Evidence Graph, filters out irrelevant background noise, extracts key entities/timeline, and formats grounded observations.
  - **Analyst Agent**: Formulates multiple competing hypotheses, maps supporting and contradicting evidence, identifies missing telemetry, and distinguishes correlation from causation.
  - **Verifier Agent**: Adversarially challenges hypotheses, audits temporal order (causes must precede effects), checks causal evidence, catches contradictions, and forms final diagnosis or flags insufficient evidence.
  - **LangGraph StateGraph Workflow**: Connects Investigator -> Analyst -> Verifier into a clean state machine.
- **Phase 7 (Incident Benchmark & Comparative Evaluation)**:
  - **20-Incident Benchmark Catalog**: 20 distinct reproducible incidents across 15 failure categories (query regressions, memory leaks, third-party timeouts, schema drifts, connection pool exhaustion, ReDoS CPU saturation, WAL disk full, deadlocks, cascading failures).
  - **Baseline B (2-Agent System)**: Investigator + Analyst without Verifier challenge loop.
  - **Rigorous 3-Way Comparative Benchmark (20 Incidents × 3 Systems)**:

| Metric | Baseline A (Single-LLM) | Baseline B (2-Agent) | Aletheia (3-Agent) |
|---|---|---|---|
| **Root-Cause Accuracy** | 46.5% | 68.0% | **69.5%** |
| **Top-3 Hypothesis Accuracy** | 100.0% | 95.0% | 95.0% |
| **Evidence Recall** | 49.6% | 56.2% | **56.2%** |
| **Evidence Precision** | 73.8% | **100.0%** | **100.0%** |
| **Hallucination Rate** | 95.0% | **0.0%** | **0.0%** |
| **False-Positive Rate** | 70.0% | 30.0% | **25.0%** |
| **Verification Success** | 5.0% | 15.0% | **100.0%** |
| **Overall Composite Score** | 22.1% | 65.5% | **66.1%** |
| **Mean Latency** | **0.000s** | 0.000s | 0.001s |
- **Phase 8 (Reliability & LLMOps)**:
  - **Structured LLM Traces**: Thread-safe `TraceRecorder` tracking token accounting, latency percentiles, models, and cost per invocation.
  - **Exponential Backoff Resilience**: `@retry_with_backoff` handling transient network drops, rate limits (HTTP 429), and API timeouts with jitter.
  - **Evaluation Run Storage & Comparison Engine**: Automatic persistence to disk (`eval_results/runs/`, `eval_results/benchmarks/`) with pairwise run diffing (`compare_runs`).
  - **LLMOps API**: `/api/v1/llmops/traces`, `/api/v1/llmops/metrics`, `/api/v1/llmops/runs`, and `/api/v1/llmops/compare`.
- **Phase 9 (Developer-Grade Frontend & Investigation Interface)**:
  - **Minimalist Obsidian UI**: Built with Next.js 16 and Vanilla CSS; dark obsidian aesthetic (`#09090b`), restrained typography, monospaced metadata badges, zero visual clutter or gratuitous gradients.
  - **Linear Diagnostic Narrative**: Guided progression designed specifically for incident commanders:
    `Incident -> Timeline -> Evidence Layer -> Analyst Hypotheses -> Verifier Challenges -> Final Diagnosis`.
  - **Dedicated Operational Views**:
    - **Incidents Catalog**: Filterable catalog of all 20 reproducible incident scenarios with severity levels and categories.
    - **Evidence Graph**: Focused causal dependency chain connecting deployments, commits, spans, and metrics.
    - **Comparative Benchmark**: 3-way evaluation comparison demonstrating measurable performance against single-model and 2-agent baselines.
    - **System & LLMOps**: Telemetry traces, live token usage accounting, and latency percentiles.
  - **Live Backend Integration**: Direct proxy architecture (`/api/backend/*`) connecting the web client to the FastAPI investigation engine.
  - **Quality Gate Verification**: 100% passing tests (98/98 tests), static compilation verified via `npm run build`, and API proxy validated.


## Repository Structure

```
aletheia/
├── docker-compose.yml              # Multi-container orchestration (postgres, checkout, aletheia)
├── Dockerfile.aletheia             # Container build for Aletheia investigation platform
├── pyproject.toml                  # Project metadata and tool configuration
├── requirements.txt                # Pinned dependencies
├── .env.example                    # Environment variable template
├── README.md                       # Project documentation
│
├── incidents/                      # Incident Definitions (Ground Truth & Scenarios)
│   ├── ground_truth/               # Verified ground truth for evaluation only
│   │   └── inc_001_ground_truth.json
│   └── scenarios/                  # Scenario parameters & injection specifications
│       └── inc_001_db_regression.json
│
├── src/aletheia/                   # Aletheia Core Platform
│   ├── api/                        # FastAPI routers & endpoints (/health, /investigation)
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   └── investigation.py
│   │   └── app.py
│   ├── config/                     # Typed Pydantic Settings
│   │   └── settings.py
│   ├── evidence/                   # Deterministic Evidence Layer
│   │   ├── schema.py               # EvidenceItem & EvidenceProvenance models
│   │   ├── entities.py             # Entity models & factory functions
│   │   ├── events.py               # Event models & deterministic Timeline
│   │   └── sources/                # Telemetry adapters
│   │       ├── base.py             # EvidenceSource abstract base class
│   │       ├── local.py            # LocalEvidenceSource aggregator
│   │       ├── log_adapter.py      # JSON log parser
│   │       ├── trace_adapter.py    # OpenTelemetry span parser
│   │       ├── metric_adapter.py   # Prometheus metric anomaly parser
│   │       └── deploy_adapter.py   # Release & commit metadata parser
│   ├── graph/                      # Evidence Graph & Query Engine
│   │   ├── schema.py               # GraphNode, GraphEdge, RelationshipType
│   │   ├── graph.py                # Directed EvidenceGraph & path finder
│   │   ├── builder.py              # Deterministic graph constructor
│   │   └── cli.py                  # CLI inspector (timeline, paths, mermaid)
│   ├── observability/              # Telemetry Triad (Logging, Tracing, Metrics)
│   │   ├── logging.py              # Structured JSON formatter & correlation context
│   │   ├── tracing.py              # OpenTelemetry TracerProvider & span utilities
│   │   ├── metrics.py              # Prometheus metric definitions & /metrics endpoint
│   │   └── middleware.py           # FastAPI ObservabilityMiddleware
│   ├── models/                     # Incident & failure injection models
│   │   └── incident.py
│   └── services/                   # Investigation orchestration (future phases)
│
├── simulator/                      # Simulated Production Environment
│   ├── failure_injection/          # Dynamic failure injection controller
│   │   ├── manager.py              # Thread-safe FailureInjectionManager singleton
│   │   └── cli.py                  # CLI controller (inject, reset, status)
│   ├── services/
│   │   └── checkout_api/           # Target service for incidents
│   │       ├── Dockerfile
│   │       ├── main.py             # FastAPI entrypoint & lifespan
│   │       ├── config.py           # Service settings
│   │       ├── database.py         # SQLAlchemy engine & session manager
│   │       ├── models.py           # Product, Order, OrderItem models
│   │       ├── schemas.py          # Pydantic v2 schemas
│   │       ├── routes.py           # Endpoints + /api/simulator/ controls
│   │       └── seed.py             # Initial catalog seeder
│   └── traffic_generator.py        # Synthetic customer traffic script
│
├── tests/                          # Automated Tests
│   ├── conftest.py                 # Isolated test fixtures
│   ├── unit/                       # Unit tests (models, config, failure injection)
│   └── integration/                # Integration tests (APIs, E2E telemetry, INC-001)
│
└── docs/                           # Architecture & Decisions
    ├── architecture/
    └── decisions/
```

---

## Quickstart: Docker Compose

Start the entire environment with a single command:

```bash
docker compose up --build
```

### Services Started:
- **Aletheia Platform API**: [http://localhost:8000](http://localhost:8000) (Docs: [http://localhost:8000/docs](http://localhost:8000/docs))
- **Checkout API**: [http://localhost:8001](http://localhost:8001) (Docs: [http://localhost:8001/docs](http://localhost:8001/docs))
- **PostgreSQL Database**: `localhost:5432` (`checkout_db`)

---

## Quickstart: Local Python Setup

### 1. Prerequisites
- Python 3.12+
- Virtual environment (`venv`)

### 2. Setup Virtual Environment
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```

### 4. Run the Checkout Service Locally
```bash
python -m uvicorn simulator.services.checkout_api.main:app --port 8001 --reload
```

### 5. Run the Aletheia Platform Locally
```bash
python -m uvicorn aletheia.api.app:app --port 8000 --reload
```

---

## Running the Automated Test Suite

Run all unit and integration tests:

```bash
pytest -v
```

All integration tests execute against an isolated in-memory/temp database and do not depend on external services.

---

## Running the Traffic Generator

Simulate realistic traffic against the Checkout API:

```bash
# Run 10 request cycles
python -m simulator.traffic_generator --requests 10 --delay 0.5

# Run continuous traffic loop
python -m simulator.traffic_generator --loop --delay 1.0
```

Sample output:
```
[traffic-gen] Health check OK: status=healthy db_latency=1.15ms
[traffic-gen] Retrieved 5 products from catalog.
[traffic-gen] Order placed successfully: order_number=ORD-E2614C8F total=$1899.99 (8.4ms)
[traffic-gen] Simulation completed. Summary: {'health_checks': 2, 'catalog_views': 4, 'orders_placed': 6, 'failed_requests': 0}
```

---

## API Examples

### Health Check (Checkout API)
```bash
curl http://localhost:8001/health
```
Response:
```json
{
  "status": "healthy",
  "service": "checkout-api",
  "version": "1.0.0",
  "environment": "production-sim",
  "timestamp": "2026-09-25T01:50:00Z",
  "database": {
    "status": "healthy",
    "latency_ms": 1.25,
    "error": null
  }
}
```

### List Catalog Products
```bash
curl http://localhost:8001/api/products
```

### Place a Checkout Order
```bash
curl -X POST http://localhost:8001/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "jane.doe@example.com",
    "items": [
      {"product_id": 1, "quantity": 1}
    ]
  }'
```

### Health Check (Aletheia Platform API)
```bash
curl http://localhost:8000/health
```

### Failure Injection Controls (Phase 3)

```bash
# Inject INC-001 (Database Query Regression) via CLI
python -m simulator.failure_injection.cli inject INC-001

# Inject with customized latency
python -m simulator.failure_injection.cli inject INC-001 --latency 1200

# Inspect active failures
python -m simulator.failure_injection.cli status

# Reset all active failures
python -m simulator.failure_injection.cli reset
```

Or via HTTP API:
```bash
# Inject
curl -X POST http://localhost:8001/api/simulator/inject \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-001", "parameters": {"latency_ms": 1500}}'

# Query status
curl http://localhost:8001/api/simulator/incidents

# Reset
curl -X POST http://localhost:8001/api/simulator/reset
### Evidence Graph & Timeline Inspection (Phase 4)

```bash
# Print reconstructed incident timeline (ASCII)
python -m aletheia.graph.cli --inspect-inc001 --timeline

# Discover causal paths from Deployment to API Latency Spike
python -m aletheia.graph.cli --inspect-inc001 --paths

# Export graph as GitHub Mermaid diagram
python -m aletheia.graph.cli --inspect-inc001 --mermaid

# Export graph as structured JSON
python -m aletheia.graph.cli --inspect-inc001 --json
```

Or query via Aletheia REST API:
```bash
# Get chronological timeline
curl http://localhost:8000/api/v1/investigation/timeline

# Get full evidence graph
curl http://localhost:8000/api/v1/investigation/graph

# Find causal paths
curl "http://localhost:8000/api/v1/investigation/paths?source=deploy:checkout-api:v4.2.1&target=evt:EVT-005"
```

### Evaluation Harness & Baseline Benchmarking (Phase 5)

Run benchmark evaluations across mock simulation modes or live LLMs:

```bash
# Evaluate Aletheia 3-Agent Multi-Agent system on INC-001
python -m aletheia.evaluation.cli --baseline aletheia-3agent --incident INC-001

# Evaluate Baseline A with accurate model simulation
python -m aletheia.evaluation.cli --baseline single-llm --incident INC-001 --mock accurate

# Evaluate Baseline A with hallucinated model (demonstrates hallucination penalty & audit)
python -m aletheia.evaluation.cli --baseline single-llm --incident INC-001 --mock hallucinated

# Evaluate with partial model (demonstrates partial recall and attribution loss)
python -m aletheia.evaluation.cli --baseline single-llm --incident INC-001 --mock partial

# Export evaluation scorecard as JSON
python -m aletheia.evaluation.cli --baseline aletheia-3agent --incident INC-001 --json

# Run live evaluation with OpenAI or compatible endpoint (requires OPENAI_API_KEY)
python -m aletheia.evaluation.cli --baseline aletheia-3agent --incident INC-001 --live --model gpt-4o-mini
```

Or trigger evaluation via Aletheia REST API:
```bash
# Run 3-Agent evaluation via API
curl -X POST http://localhost:8000/api/v1/eval/run \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-001", "baseline": "aletheia-3agent", "mock_mode": "accurate"}'

# List available diagnostic baselines
curl http://localhost:8000/api/v1/eval/baselines

# List past evaluation reports
curl http://localhost:8000/api/v1/eval/reports
```

---

## Development Roadmap

- [x] **Phase 1 — Foundation**: Simulated checkout service, PostgreSQL, Docker Compose, initial catalog, traffic generator, test suite.
- [x] **Phase 2 — Observability**: Structured JSON logging, OpenTelemetry distributed traces, Prometheus metrics, and correlation IDs.
- [x] **Phase 3 — Failure Injection**: Controlled failure scenarios (e.g., `INC-001` Database Query Regression) with ground truth definitions.
- [x] **Phase 4 — Evidence Model & Graph**: Time-aware evidence schema, provenance, entity models, deterministic timeline, and evidence graph query engine.
- [x] **Phase 5 — Single-LLM Baseline & Evaluation Harness**: Ground truth isolation, single-LLM context dump baseline, 6-dimensional scoring, hermetic mock clients, and scorecard CLI/API.
- [x] **Phase 6 — Multi-Agent Investigation**: Investigator, Analyst, and Verifier agents with LangGraph orchestration and comprehensive evaluation.
- [ ] **Phase 7 — Incident Benchmark & Comparative Evaluation**: 20–50 reproducible failure scenarios across 15+ failure categories; 3-way comparative evaluation (Single-LLM vs 2-Agent vs 3-Agent).
- [ ] **Phase 8 — Reliability & LLMOps**: Token/cost/latency telemetry, retries, rate limits, structured run persistence.
- [ ] **Phase 9 — Frontend & Deployment**: Modern Next.js + TypeScript dashboard with interactive timeline, evidence graph, and deployment.
- [ ] **Phase 10 — Final Portfolio Release**: Architecture writeups, benchmark results, demonstration guide, and ADRs.

