# ADR 0008: Production Reliability, Resilience, and LLMOps

## Status
Accepted

## Context
As Aletheia evolved from prototype to benchmarked multi-agent system, operational reliability and telemetry became essential:
1. Production LLM providers (e.g., OpenAI, Gemini, vLLM) experience transient connection timeouts, HTTP 429 rate limits, and server overload.
2. Without structured operational telemetry, diagnosing why an investigation failed (e.g., latency spikes, token budget explosions, rate limits) requires ad-hoc debugging.
3. Comparative evaluation experiments require persistent tracking and delta comparison to ensure agent, prompt, or model changes do not introduce silent regressions.

## Decision
1. **Lightweight, Zero-Overhead Telemetry (`src/aletheia/reliability/traces.py`):**
   - Implemented `TraceRecorder` collecting structured `LLMCallTrace` records:
     - `trace_id`, `incident_id`, `agent_name`, `model`, `latency_ms`
     - Token accounting (`prompt_tokens`, `completion_tokens`, `total_tokens`)
     - Financial accounting (`estimated_cost_usd`)
     - Operational status (`success`, `retried`, `rate_limited`, `timeout`, `error`)
   - Emits append-only JSONL files (`eval_results/traces/llm_traces.jsonl`) without external SaaS dependencies.
2. **Resilience & Rate-Limit Handling (`src/aletheia/reliability/resilience.py`):**
   - Implemented `execute_with_retry` and `@retry_with_backoff` using exponential backoff with random jitter.
   - Automatically detects transient HTTP errors (429, 502, 503, 504), network disconnects, and `LLMTimeoutError`.
   - Fails fast on unrecoverable errors (e.g. 400 Bad Request, auth failures).
3. **Evaluation Run & Benchmark Storage (`src/aletheia/reliability/store.py`):**
   - Implemented `EvaluationStore` to persist individual evaluation runs (`eval_results/runs/`) and benchmarks (`eval_results/benchmarks/`).
   - Added experiment comparison (`compare_runs`) computing performance deltas: overall score, root cause accuracy, evidence recall, hallucination rate, and cost deltas.
4. **LLMOps API Surface (`src/aletheia/api/routes/llmops.py`):**
   - Exposed endpoints for frontend and external monitoring:
     - `GET /api/v1/llmops/traces`: Query execution traces by agent/incident
     - `GET /api/v1/llmops/metrics`: Aggregate operational metrics (latency percentiles, failure rates, cost)
     - `GET /api/v1/llmops/runs`: List historical runs
     - `GET /api/v1/llmops/benchmarks`: List comparative benchmarks
     - `POST /api/v1/llmops/compare`: Diff two evaluation runs

## Consequences
- **High Availability & Fault Tolerance:** Transient network glitches or provider throttling no longer cause diagnostic failure.
- **Accurate Cost & Performance Visibility:** Every LLM call tracks its tokens and cost with sub-millisecond precision.
- **No Heavy Third-Party Lock-in:** Provides essential LLMOps capabilities locally without requiring external SaaS setups.
