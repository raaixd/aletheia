# Aletheia (ἀλήθεια)

> *"The goal isn't to build an AI that guesses what went wrong. It's to build an investigation system that gathers evidence, constructs explanations, challenges them, and can be measured when it gets the diagnosis wrong."*

Aletheia is an AI-powered incident investigation system for software systems. When a production system experiences an incident, Aletheia gathers evidence from multiple sources, aligns it in time, constructs an evidence graph, generates competing hypotheses, challenges them through an adversarial verifier, and outputs an evidence-backed diagnosis that can be measured against ground truth.

---

## Current Status: Phase 2 — Observability Complete

- **Phase 1 (Foundation)**: Simulated checkout service, PostgreSQL 16, Docker Compose, automated product seeding, synthetic traffic generator.
- **Phase 2 (Observability)**: Correlated telemetry triad across all services:
  - **Structured JSON Logging**: UTC ISO timestamps, service identifiers, context-aware correlation IDs, OpenTelemetry trace/span IDs.
  - **Context-Aware Correlation IDs**: Thread-safe propagation via `contextvars`, client header extraction, and response header injection (`X-Correlation-ID`).
  - **Prometheus Metrics**: `/metrics` endpoint on all services exporting request counts (`http_requests_total`), duration histograms (`http_request_duration_seconds`), error counts (`http_errors_total`), and active request gauges (`http_active_requests`).
  - **OpenTelemetry Distributed Tracing**: Automated span creation with standard HTTP semantics and header propagation (`X-Trace-ID`, `X-Span-ID`).
  - **Automated Verification**: 100% passing test suite (25/25 unit, integration, and E2E correlation tests).

---

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
├── src/aletheia/                   # Aletheia Core Platform
│   ├── api/                        # FastAPI routers & endpoints (/health)
│   │   ├── routes/
│   │   └── app.py
│   ├── config/                     # Typed Pydantic Settings
│   │   └── settings.py
│   ├── observability/              # Telemetry Triad (Logging, Tracing, Metrics)
│   │   ├── logging.py              # Structured JSON formatter & correlation context
│   │   ├── tracing.py              # OpenTelemetry TracerProvider & span utilities
│   │   ├── metrics.py              # Prometheus metric definitions & /metrics endpoint
│   │   └── middleware.py           # FastAPI ObservabilityMiddleware
│   ├── models/                     # Evidence & domain models (future phases)
│   └── services/                   # Investigation orchestration (future phases)
│
├── simulator/                      # Simulated Production Environment
│   ├── services/
│   │   └── checkout_api/           # Target service for incidents
│   │       ├── Dockerfile
│   │       ├── main.py             # FastAPI entrypoint & lifespan
│   │       ├── config.py           # Service settings
│   │       ├── database.py         # SQLAlchemy engine & session manager
│   │       ├── models.py           # Product, Order, OrderItem models
│   │       ├── schemas.py          # Pydantic v2 schemas
│   │       ├── routes.py           # /health, /api/products, /api/orders
│   │       └── seed.py             # Initial catalog seeder
│   └── traffic_generator.py        # Synthetic customer traffic script
│
├── tests/                          # Automated Tests
│   ├── conftest.py                 # Isolated test fixtures
│   ├── unit/                       # Unit tests (models, config, generator)
│   └── integration/                # Integration tests (APIs, DB workflows)
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

---

## Development Roadmap

- [x] **Phase 1 — Foundation**: Simulated checkout service, PostgreSQL, Docker Compose, initial catalog, traffic generator, test suite.
- [x] **Phase 2 — Observability**: Structured JSON logging, OpenTelemetry distributed traces, Prometheus metrics, and correlation IDs.
- [ ] **Phase 3 — Failure Injection**: Controlled failure scenarios (e.g., `INC-001` Database Query Regression) with ground truth definitions.
- [ ] **Phase 4 — Evidence Model & Graph**: Time-aware evidence schema, provenance, and graph representation.
- [ ] **Phase 5 — Single-LLM Baseline**: Baseline diagnostic evaluator.
- [ ] **Phase 6 — Agent 1: Investigator**: Evidence collection, entity extraction, and timeline construction.
- [ ] **Phase 7 — Agent 2: Analyst**: Multi-hypothesis generation with supporting and contradicting evidence.
- [ ] **Phase 8 — Agent 3: Verifier**: Adversarial hypothesis challenge, temporal validation, and confidence scoring.
- [ ] **Phase 9 — Evaluation Harness**: Accuracy, evidence precision/recall, latency, and cost benchmarking.
- [ ] **Phase 10 — Hard Cases & Adversarial Robustness**: Prompt injection, noisy logs, conflicting signals.
- [ ] **Phase 11 — Frontend Dashboard**: Visual timeline, evidence graph, and investigation trace.
- [ ] **Phase 12 — Cloud Deployment**: AWS ECS/Fargate, RDS PostgreSQL, OpenTelemetry.
