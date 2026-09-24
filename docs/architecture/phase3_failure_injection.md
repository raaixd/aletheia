# Aletheia Architecture: Phase 3 Failure Injection

## Overview

Aletheia is an incident investigation system designed to gather evidence, formulate competing hypotheses, challenge them adversarially, and measure its diagnostic accuracy. To evaluate the investigation system rigorously, we cannot rely on arbitrary synthetic text; we must have **controlled, reproducible incidents** injected into a realistic running application with **verifiable ground truth**.

---

## Core Principle: Ground Truth Isolation

> **CRITICAL RULE**:
> Ground truth exists **only** for evaluation. Ground truth files and expected evidence definitions are strictly isolated from the AI agents and are never provided as prompts or hints during investigation. Ground truth is consulted solely by the evaluation harness after diagnosis has completed.

---

## Architecture of Failure Injection

```
┌─────────────────────────────────────────────────────────────┐
│                 Controller / Evaluation Runner              │
│                                                             │
│   CLI: python -m simulator.failure_injection.cli inject     │
│   API: POST /api/simulator/inject                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             FailureInjectionManager (Singleton)             │
│                                                             │
│   1. Load scenario defaults from incidents/scenarios/       │
│   2. Merge custom runtime parameter overrides               │
│   3. Activate incident state in memory (thread-safe)        │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             Target Service (checkout-api)                   │
│                                                             │
│   Endpoint: GET /api/orders                                 │
│   Check: if failure_manager.is_active("INC-001"):           │
│     - Execute regressed query plan / delayed execution      │
│     - Create child OpenTelemetry span:                      │
│       "db.query: SELECT orders (unindexed)"                 │
│     - Record elevated duration in Prometheus metrics        │
│     - Emit structured warning log with latency & context    │
└─────────────────────────────────────────────────────────────┘
```

---

## Incident 001: Database Query Regression (`INC-001`)

### 1. Scenario Definition
- **Scenario File**: `incidents/scenarios/inc_001_db_regression.json`
- **Target Service**: `checkout-api`
- **Target Endpoint**: `GET /api/orders`
- **Default Injected Latency**: 1500ms

### 2. Ground Truth Specification
- **Ground Truth File**: `incidents/ground_truth/inc_001_ground_truth.json`
- **Root Cause**: `slow_database_query`
- **Introduced By**: `commit_abc123` (Deployment `v4.2.1`)
- **Expected Evidence**:
  - `deployment_v4.2.1`
  - `commit_abc123`
  - `increased_db_latency`
  - `increased_checkout_latency`

### 3. Observable Symptoms
- **Baseline Latency**: ~2ms – 5ms
- **Regressed Latency**: ~1500ms
- **Distributed Trace**: Contains child span `db.query: SELECT orders (unindexed)` taking >95% of total request time.
- **Prometheus Metric**: Histogram buckets `http_request_duration_seconds` shift into `1.0` and `2.5` second tiers.
- **Log Message**: `Database query execution delayed by 1500ms due to unindexed sort regression (INC-001)`.

---

## CLI and API Controls

### Via CLI:
```bash
# Inject INC-001
python -m simulator.failure_injection.cli inject INC-001

# Inject with custom latency
python -m simulator.failure_injection.cli inject INC-001 --latency 800

# Check active failures
python -m simulator.failure_injection.cli status

# Reset all active failures
python -m simulator.failure_injection.cli reset
```

### Via HTTP API:
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
