<div align="center">

<br>

# ALETHEIA

**AI-powered incident investigation for software systems**

<br>

*Not an AI that guesses what went wrong —*
*an investigation system that gathers evidence, builds explanations,*
*challenges them, and can be measured when it's wrong.*

<br>

`Phase 9 Complete` · `Phase 10 In Progress` · `98/98 Tests` · `Python 3.12+`

<br>

[Frontend](https://aletheia-khaki-tau.vercel.app) · [API](https://aletheia-backend-ten.vercel.app) · [Docs](https://aletheia-backend-ten.vercel.app/docs) · [Health](https://aletheia-backend-ten.vercel.app/health)

<br>

</div>

---

<br>

## What it does

When a production system breaks, Aletheia gathers evidence from logs, traces, metrics, and deploys — aligns it in time, builds an evidence graph, generates competing hypotheses, and adversarially challenges them until it reaches a diagnosis it can defend.

```
Incident → Timeline → Evidence Graph → Hypotheses → Verification → Diagnosis
```

<br>

## Results

Three systems, twenty incidents, same evidence.

<br>

|  | Single-LLM | 2-Agent | **Aletheia** |
|:--|:--:|:--:|:--:|
| Root-cause accuracy | 46.5% | 68.0% | **69.5%** |
| Evidence precision | 73.8% | 100.0% | **100.0%** |
| Hallucination rate | 95.0% | 0.0% | **0.0%** |
| Verification success | 5.0% | 15.0% | **100.0%** |
| **Composite score** | **22.1%** | **65.5%** | **66.1%** |

<br>

The gap that matters isn't root-cause accuracy — it's verification. A three-agent system that checks its own work catches what a single model quietly gets wrong.

<br>

## How it's built

```
Evidence Layer   →   deterministic, no LLM. logs + traces + metrics + deploys,
                     time-aligned into a directed graph.

Investigator     →   queries the graph, filters noise, extracts what matters.

Analyst          →   builds competing hypotheses, separates correlation from cause.

Verifier         →   adversarially audits each hypothesis — temporal order,
                     causal evidence, contradictions — before it becomes a diagnosis.
```

Orchestrated as a LangGraph state machine. Benchmarked against 20 reproducible incidents across 15 failure categories — query regressions, memory leaks, deadlocks, cascading failures, and more.

<br>

## Quickstart

**Docker**

```bash
docker compose up --build
```

| Service | URL |
|:--|:--|
| Aletheia API | `localhost:8000` / `/docs` |
| Checkout API | `localhost:8001` / `/docs` |
| PostgreSQL | `localhost:5432` |

<br>

**Local**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

python -m uvicorn simulator.services.checkout_api.main:app --port 8001 --reload
python -m uvicorn aletheia.api.app:app --port 8000 --reload
```

<br>

**Test**

```bash
pytest -v
```

<br>

## Try it

```bash
# inject a failure
python -m simulator.failure_injection.cli inject INC-001

# inspect the evidence graph
python -m aletheia.graph.cli --inspect-inc001 --timeline

# run the 3-agent investigation
python -m aletheia.evaluation.cli --baseline aletheia-3agent --incident INC-001

# compare against the single-LLM baseline
python -m aletheia.evaluation.cli --baseline single-llm --incident INC-001 --mock hallucinated
```

<br>

## Structure

```
aletheia/
├── src/aletheia/
│   ├── evidence/       deterministic evidence layer — schema, entities, timeline
│   ├── graph/           evidence graph — nodes, edges, causal path finding
│   ├── observability/   logging, tracing, metrics
│   └── api/              FastAPI routes
├── simulator/
│   ├── failure_injection/   controlled, reproducible failure scenarios
│   └── services/              target checkout service
├── frontend/            Next.js dashboard
├── incidents/           20-incident benchmark catalog + ground truth
└── tests/
```

<br>

## Roadmap

```
✓  Foundation             simulated service, Docker, traffic generator
✓  Observability          logs, traces, metrics, correlation IDs
✓  Failure Injection      reproducible incident scenarios
✓  Evidence Graph         deterministic, LLM-free evidence layer
✓  Single-LLM Baseline    ground-truth isolated evaluation harness
✓  Multi-Agent System     Investigator → Analyst → Verifier
✓  Benchmark              20 incidents, 15 categories, 3-way comparison
✓  LLMOps                 traces, cost, retries, run persistence
✓  Frontend               Next.js dashboard, dual Vercel deployment
·  Portfolio Release      ADRs, benchmark writeup, demo guide
```

<br>

---

<div align="center">

<br>

*Built to be wrong in a way you can measure.*

<br>

</div>
