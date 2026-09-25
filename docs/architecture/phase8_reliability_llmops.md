# Phase 8 — Reliability & LLMOps Architecture

## Overview
Phase 8 introduces production engineering to Aletheia's diagnostic and evaluation pipelines. Rather than introducing complex external SaaS stacks, Aletheia implements a clean, robust, and measurable reliability foundation:

```
                            Agent Invocation
                     (Investigator / Analyst / Verifier)
                                    │
                                    ▼
                          [execute_with_retry]
                     ├── Exponential backoff + jitter
                     ├── Rate limit (HTTP 429) backoff
                     └── Timeout recovery
                                    │
                                    ▼
                         [OpenAI / Mock Client]
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                 Structured Traces        Evaluation Store
               (eval_results/traces/)  (eval_results/runs/)
                         │                     │
                         ▼                     ▼
                  LLMOps API           Experiment Comparison
               (/api/v1/llmops/*)        (Metric Δ Analysis)
```

---

## Core Subsystems

### 1. Structured Traces & Cost Accounting (`src/aletheia/reliability/traces.py`)
- **`LLMCallTrace`**: Captures `trace_id`, `incident_id`, `agent_name`, `model`, `latency_ms`, token counts (`prompt_tokens`, `completion_tokens`, `total_tokens`), `estimated_cost_usd`, and retry counts.
- **`TraceRecorder`**: Thread-safe in-memory and append-only JSONL file storage (`eval_results/traces/llm_traces.jsonl`).
- **`LLMOpsMetricsSummary`**: Aggregates latency percentiles (mean, p95), total financial cost, breakdown of calls by agent, and failure/retry rates.

### 2. Resilience & Rate-Limit Handling (`src/aletheia/reliability/resilience.py`)
- **`execute_with_retry` & `@retry_with_backoff`**:
  - Catches transient network errors (`LLMTimeoutError`, connection drops, HTTP 429 rate limits, HTTP 502/503/504 errors).
  - Uses randomized exponential backoff with jitter to prevent herd effects.
  - Exposes `retry_hook` for trace attribution and operational monitoring.

### 3. Evaluation Store & Experiment Comparison (`src/aletheia/reliability/store.py`)
- **`EvaluationStore`**:
  - Persists individual diagnostic evaluations (`eval_results/runs/<report_id>.json`).
  - Persists multi-system comparative benchmarks (`eval_results/benchmarks/<benchmark_id>.json`).
  - Implements `compare_runs(report_a, report_b)` to compute quantitative deltas:
    - Overall score delta ($\Delta$)
    - Root cause accuracy delta ($\Delta$)
    - Evidence recall and precision deltas ($\Delta$)
    - Hallucination reduction delta ($\Delta$)
    - Latency and dollar cost deltas ($\Delta$)

### 4. LLMOps API Endpoints (`src/aletheia/api/routes/llmops.py`)
- `GET /api/v1/llmops/traces`: Query execution traces.
- `GET /api/v1/llmops/metrics`: Aggregate operational metrics.
- `GET /api/v1/llmops/runs`: List historical runs.
- `GET /api/v1/llmops/runs/{report_id}`: Inspect run report.
- `GET /api/v1/llmops/benchmarks`: List comparative benchmarks.
- `POST /api/v1/llmops/compare`: Diff two evaluation runs.
