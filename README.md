<div align="center">

# Aletheia

**An AI-powered incident investigation system for software systems.**

*The goal isn't to build an AI that guesses what went wrong. It's to build an investigation system that gathers evidence, constructs explanations, challenges them, and can be measured when it gets the diagnosis wrong.*

[![Status](https://img.shields.io/badge/status-Phase%209%20Complete%20(Working%20on%20Phase%2010)-6E56CF?style=flat-square)](#roadmap)
[![Tests](https://img.shields.io/badge/tests-98%2F98%20passing-2EA043?style=flat-square)](#running-the-automated-test-suite)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square)](#quickstart-local-python-setup)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED?style=flat-square)](#quickstart-docker-compose)

</div>

---

When a production system experiences an incident, Aletheia gathers evidence from multiple sources, aligns it in time, constructs an evidence graph, generates competing hypotheses, challenges them through an adversarial verifier, and outputs an **evidence-backed diagnosis** that can be measured against ground truth.

### Live Production Deployments (Vercel)
- **Frontend Dashboard**: [https://aletheia-khaki-tau.vercel.app](https://aletheia-khaki-tau.vercel.app)
- **FastAPI Investigation Backend**: [https://aletheia-backend-ten.vercel.app](https://aletheia-backend-ten.vercel.app)
  - Interactive OpenAPI Documentation: [https://aletheia-backend-ten.vercel.app/docs](https://aletheia-backend-ten.vercel.app/docs)
  - Health Endpoint: [https://aletheia-backend-ten.vercel.app/health](https://aletheia-backend-ten.vercel.app/health)
  - 20-Incident Benchmark Catalog: [https://aletheia-backend-ten.vercel.app/api/v1/investigation/incidents](https://aletheia-backend-ten.vercel.app/api/v1/investigation/incidents)


## Table of Contents

- [Current Status](#current-status)
- [Results at a Glance](#results-at-a-glance)
- [Repository Structure](#repository-structure)
- [Quickstart — Docker Compose](#quickstart-docker-compose)
- [Quickstart — Local Python Setup](#quickstart-local-python-setup)
- [Running the Test Suite](#running-the-automated-test-suite)
- [Running the Traffic Generator](#running-the-traffic-generator)
- [API Examples](#api-examples)
- [Roadmap](#roadmap)

---

## Current Status

**Phase 9 — Developer-Grade Frontend & Vercel Deployment Complete (Working on Phase 10 — Final Portfolio Release)**

<details open>
<summary><b>Phase 1 — Foundation</b></summary>
<br>

Simulated checkout service, PostgreSQL 16, Docker Compose, automated product seeding, synthetic traffic generator.
</details>

<details open>
<summary><b>Phase 2 — Observability</b></summary>
<br>

Correlated telemetry triad across all services: structured JSON logging, context-aware correlation IDs, Prometheus metrics, and OpenTelemetry distributed tracing.
</details>

<details open>
<summary><b>Phase 3 — Failure Injection</b></summary>
<br>

Controlled, reproducible failure injection system with ground truth isolation (`INC-001` database query regression).
</details>

<details open>
<summary><b>Phase 4 — Evidence Model & Graph</b></summary>
<br>

Deterministic, time-aware evidence layer built without an LLM: evidence schema, provenance, entity models, timeline, graph engine, and traversal.
</details>

<details open>
<summary><b>Phase 5 — Single-LLM Baseline & Evaluation Harness</b></summary>
<br>

- **Ground truth isolation** — diagnostic models are evaluated strictly against observable evidence, never given ground truth clues or answers.
- **Baseline A (Single-LLM context dump)** — full telemetry serialization into a structured diagnosis with strict JSON discipline.
- **Six-dimensional evaluation metrics** — root cause accuracy, attribution accuracy, affected service/component, evidence recall, evidence precision, hallucination penalty.
- **Hermetic mocking & live LLM client** — built-in mock simulation modes (`accurate`, `hallucinated`, `partial`, `invalid_json`) and a live OpenAI-compatible provider with robust error/timeout handling.
</details>

<details open>
<summary><b>Phase 6 — Multi-Agent Investigation & LangGraph Orchestration</b></summary>
<br>

- **Investigator Agent** — queries the deterministic Evidence Graph, filters background noise, extracts key entities/timeline, formats grounded observations.
- **Analyst Agent** — formulates competing hypotheses, maps supporting/contradicting evidence, identifies missing telemetry, distinguishes correlation from causation.
- **Verifier Agent** — adversarially challenges hypotheses, audits temporal order (causes must precede effects), checks causal evidence, catches contradictions, forms the final diagnosis or flags insufficient evidence.
- **LangGraph StateGraph workflow** — connects Investigator → Analyst → Verifier into a clean state machine.
</details>

<details open>
<summary><b>Phase 7 — Incident Benchmark & Comparative Evaluation</b></summary>
<br>

- **20-incident benchmark catalog** — 20 distinct reproducible incidents across 15 failure categories (query regressions, memory leaks, third-party timeouts, schema drifts, connection pool exhaustion, ReDoS CPU saturation, WAL disk full, deadlocks, cascading failures).
- **Baseline B (2-agent system)** — Investigator + Analyst, without the Verifier challenge loop.
- **Rigorous 3-way comparative benchmark** across 20 incidents × 3 systems — see [Results at a Glance](#results-at-a-glance).
</details>

<details open>
<summary><b>Phase 8 — Reliability & LLMOps</b></summary>
<br>

- **Structured LLM traces** — thread-safe `TraceRecorder` tracking token accounting, latency percentiles, models, and cost per invocation.
- **Exponential backoff resilience** — `@retry_with_backoff` handles transient network drops, rate limits (HTTP 429), and API timeouts with jitter.
- **Evaluation run storage & comparison engine** — automatic persistence to disk (`eval_results/runs/`, `eval_results/benchmarks/`) with pairwise run diffing (`compare_runs`).
- **LLMOps API** — `/api/v1/llmops/traces`, `/api/v1/llmops/metrics`, `/api/v1/llmops/runs`, `/api/v1/llmops/compare`.
</details>

<details open>
<summary><b>Phase 9 — Developer-Grade Frontend & Investigation Interface</b></summary>
<br>

- **Minimalist Obsidian UI** — built with Next.js 16 and vanilla CSS; dark obsidian aesthetic (`#09090b`), restrained typography, monospaced metadata badges, zero visual clutter or gratuitous gradients.
- **Linear diagnostic narrative** — a guided progression designed for incident commanders:
  `Incident → Timeline → Evidence Layer → Analyst Hypotheses → Verifier Challenges → Final Diagnosis`
- **Dedicated operational views:**
  - *Incidents Catalog* — filterable catalog of all 20 reproducible incident scenarios, with severity levels and categories.
  - *Evidence Graph* — focused causal dependency chain connecting deployments, commits, spans, and metrics.
  - *Comparative Benchmark* — 3-way evaluation comparison against single-model and 2-agent baselines.
  - *System & LLMOps* — telemetry traces, live token usage accounting, and latency percentiles.
- **Live backend integration** — direct proxy architecture (`/api/backend/*`) connecting the web client to the FastAPI investigation engine.
- **Dual Vercel Serverless Deployment** — both the Next.js frontend and Python FastAPI multi-agent backend are deployed live to Vercel Serverless with production API rewrites and real-time multi-agent execution.
- **Quality gate verification** — 100% passing tests (98/98), static compilation verified via `npm run build`, and API proxy validated.
</details>

<details open>
<summary><b>Phase 10 — Final Portfolio Release (In Progress)</b></summary>
<br>

- **Architectural writeups & formal ADR catalog** — comprehensive decision records for telemetry design, evidence graph indexing, and multi-agent consensus.
- **Benchmark methodology & empirical analysis** — detailed breakdown of the 20-incident benchmark across 15 failure categories.
- **Incident investigation demonstration guide** — end-to-end walkthroughs from telemetry ingestion to causal root-cause diagnosis.
- **Final portfolio release packaging** — release artifacts and public documentation.
</details>

---

## Results at a Glance

3-way comparative benchmark across 20 incidents:

| Metric | Baseline A (Single-LLM) | Baseline B (2-Agent) | Aletheia (3-Agent) |
|---|:---:|:---:|:---:|
| Root-Cause Accuracy | 46.5% | 68.0% | **69.5%** |
| Top-3 Hypothesis Accuracy | **100.0%** | 95.0% | 95.0% |
| Evidence Recall | 49.6% | 56.2% | **56.2%** |
| Evidence Precision | 73.8% | **100.0%** | **100.0%** |
| Hallucination Rate | 95.0% | **0.0%** | **0.0%** |
| False-Positive Rate | 70.0% | 30.0% | **25.0%** |
| Verification Success | 5.0% | 15.0% | **100.0%** |
| **Overall Composite Score** | 22.1% | 65.5% | **66.1%** |
| Mean Latency | **0.000s** | 0.000s | 0.001s |


> Aletheia's adversarial verification loop is the standout: near-perfect verification success and zero hallucinations, while still edging out the 2-agent baseline on root-cause accuracy.

---

## Repository Structure

```text
aletheia/
├── api/                            # Vercel Serverless Function entrypoint
│   └── index.py
├── frontend/                       # Next.js 16 UI Dashboard
├── vercel.json                     # Vercel deployment & routing configuration
├── docker-compose.yml              # Multi-container orchestration (postgres, checkout, aletheia)
├── Dockerfile.aletheia             # Container build for Aletheia investigation platform
├── pyproject.toml                  # Project metadata and tool configuration
├── requirements.txt                # Pinned dependencies
├── .env.example                    # Environment variable template
├── README.md                       # Project documentation
│
├── incidents/                      # Incident definitions (ground truth & scenarios)
│   ├── ground_truth/               #   Verified ground truth, for evaluation only
│   │   └── inc_001_ground_truth.json
│   └── scenarios/                  #   Scenario parameters & injection specifications
│       └── inc_001_db_regression.json
│
├── src/aletheia/                   # Aletheia core platform
│   ├── api/                        #   FastAPI routers & endpoints
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   └── investigation.py
│   │   └── app.py
│   ├── config/                     #   Typed Pydantic settings
│   │   └── settings.py
│   ├── evidence/                   #   Deterministic evidence layer
│   │   ├── schema.py               #     EvidenceItem & EvidenceProvenance models
│   │   ├── entities.py             #     Entity models & factory functions
│   │   ├── events.py               #     Event models & deterministic Timeline
│   │   └── sources/                #     Telemetry adapters
│   │       ├── base.py             #       EvidenceSource abstract base class
│   │       ├── local.py            #       LocalEvidenceSource aggregator
│   │       ├── log_adapter.py      #       JSON log parser
│   │       ├── trace_adapter.py    #       OpenTelemetry span parser
│   │       ├── metric_adapter.py   #       Prometheus metric anomaly parser
│   │       └── deploy_adapter.py   #       Release & commit metadata parser
│   ├── graph/                      #   Evidence graph & query engine
│   │   ├── schema.py               #     GraphNode, GraphEdge, RelationshipType
│   │   ├── graph.py                #     Directed EvidenceGraph & path finder
│   │   ├── builder.py              #     Deterministic graph constructor
│   │   └── cli.py                  #     CLI inspector (timeline, paths, mermaid)
│   ├── observability/              #   Telemetry triad (logging, tracing, metrics)
│   │   ├── logging.py              #     Structured JSON formatter & correlation context
│   │   ├── tracing.py              #     OpenTelemetry TracerProvider & span utilities
│   │   ├── metrics.py              #     Prometheus metric definitions & /metrics endpoint
│   │   └── middleware.py           #     FastAPI ObservabilityMiddleware
│   ├── models/                     #   Incident & failure injection models
│   │   └── incident.py
│   └── services/                   #   Investigation orchestration
│
├── simulator/                      # Simulated production environment
│   ├── failure_injection/          #   Dynamic failure injection controller
│   │   ├── manager.py              #     Thread-safe FailureInjectionManager singleton
│   │   └── cli.py                  #     CLI controller (inject, reset, status)
│   ├── services/
│   │   └── checkout_api/           #   Target service for incidents
│   │       ├── Dockerfile
│   │       ├── main.py             #     FastAPI entrypoint & lifespan
│   │       ├── config.py           #     Service settings
│   │       ├── database.py         #     SQLAlchemy engine & session manager
│   │       ├── models.py           #     Product, Order, OrderItem models
│   │       ├── schemas.py          #     Pydantic v2 schemas
│   │       ├── routes.py           #     Endpoints + /api/simulator/ controls
│   │       └── seed.py             #     Initial catalog seeder
│   └── traffic_generator.py        #   Synthetic customer traffic script
│
├── tests/                          # Automated tests
│   ├── conftest.py                 #   Isolated test fixtures
│   ├── unit/                       #   Unit tests (models, config, failure injection)
│   └── integration/                #   Integration tests (APIs, E2E telemetry, INC-001)
│
└── docs/                           # Architecture & decisions
    ├── architecture/
    └── decisions/
```

---

## Quickstart: Docker Compose

Start the entire environment with a single command:

```bash
docker compose up --build
```

**Services started:**

| Service | URL |
|---|---|
| Aletheia Platform API | [localhost:8000](http://localhost:8000) &nbsp;·&nbsp; [docs](http://localhost:8000/docs) |
| Checkout API | [localhost:8001](http://localhost:8001) &nbsp;·&nbsp; [docs](http://localhost:8001/docs) |
| PostgreSQL Database | `localhost:5432` (`checkout_db`) |

---

## Quickstart: Local Python Setup

**1. Prerequisites**
- Python 3.12+
- `venv`

**2. Set up a virtual environment**
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

**3. Configure environment**
```bash
cp .env.example .env
```

**4. Run the checkout service locally**
```bash
python -m uvicorn simulator.services.checkout_api.main:app --port 8001 --reload
```

**5. Run the Aletheia platform locally**
```bash
python -m uvicorn aletheia.api.app:app --port 8000 --reload
```

---

## Running the Automated Test Suite

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
```text
[traffic-gen] Health check OK: status=healthy db_latency=1.15ms
[traffic-gen] Retrieved 5 products from catalog.
[traffic-gen] Order placed successfully: order_number=ORD-E2614C8F total=$1899.99 (8.4ms)
[traffic-gen] Simulation completed. Summary: {'health_checks': 2, 'catalog_views': 4, 'orders_placed': 6, 'failed_requests': 0}
```

---

## API Examples

<details>
<summary><b>Health Check — Checkout API</b></summary>

```bash
curl http://localhost:8001/health
```

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
</details>

<details>
<summary><b>List Catalog Products</b></summary>

```bash
curl http://localhost:8001/api/products
```
</details>

<details>
<summary><b>Place a Checkout Order</b></summary>

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
</details>

<details>
<summary><b>Health Check — Aletheia Platform API</b></summary>

```bash
curl http://localhost:8000/health
```
</details>

<details>
<summary><b>Failure Injection Controls (Phase 3)</b></summary>

Via CLI:
```bash
# Inject INC-001 (Database Query Regression)
python -m simulator.failure_injection.cli inject INC-001

# Inject with customized latency
python -m simulator.failure_injection.cli inject INC-001 --latency 1200

# Inspect active failures
python -m simulator.failure_injection.cli status

# Reset all active failures
python -m simulator.failure_injection.cli reset
```

Via HTTP API:
```bash
# Inject
curl -X POST http://localhost:8001/api/simulator/inject \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-001", "parameters": {"latency_ms": 1500}}'

# Query status
curl http://localhost:8001/api/simulator/incidents

# Reset
curl -X POST http://localhost:8001/api/simulator/reset
```
</details>

<details>
<summary><b>Evidence Graph & Timeline Inspection (Phase 4)</b></summary>

Via CLI:
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

Via Aletheia REST API:
```bash
# Get chronological timeline
curl http://localhost:8000/api/v1/investigation/timeline

# Get full evidence graph
curl http://localhost:8000/api/v1/investigation/graph

# Find causal paths
curl "http://localhost:8000/api/v1/investigation/paths?source=deploy:checkout-api:v4.2.1&target=evt:EVT-005"
```
</details>

<details>
<summary><b>Evaluation Harness & Baseline Benchmarking (Phase 5)</b></summary>

Via CLI:
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

Via Aletheia REST API:
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
</details>

---

## Roadmap

- [x] **Phase 1 — Foundation** — simulated checkout service, PostgreSQL, Docker Compose, initial catalog, traffic generator, test suite.
- [x] **Phase 2 — Observability** — structured JSON logging, OpenTelemetry distributed traces, Prometheus metrics, correlation IDs.
- [x] **Phase 3 — Failure Injection** — controlled failure scenarios (`INC-001`) with ground truth definitions.
- [x] **Phase 4 — Evidence Model & Graph** — time-aware evidence schema, provenance, entity models, deterministic timeline, graph query engine.
- [x] **Phase 5 — Single-LLM Baseline & Evaluation Harness** — ground truth isolation, single-LLM baseline, 6-dimensional scoring, hermetic mock clients, scorecard CLI/API.
- [x] **Phase 6 — Multi-Agent Investigation** — Investigator, Analyst, and Verifier agents with LangGraph orchestration and comprehensive evaluation.
- [x] **Phase 7 — Incident Benchmark & Comparative Evaluation** — 20 reproducible failure scenarios across 15 failure categories; 3-way comparative evaluation.
- [x] **Phase 8 — Reliability & LLMOps** — token/cost/latency telemetry, retries, rate limits, structured run persistence.
- [x] **Phase 9 — Frontend & Vercel Deployment** — Next.js dashboard with interactive timeline, evidence graph, and serverless Vercel deployments.
- [ ] **Phase 10 — Final Portfolio Release (In Progress)** — architecture writeups, benchmark results, demonstration guide, and ADRs.
