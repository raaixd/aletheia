# ADR 0001: Project Foundation & Simulated Environment Architecture

## Context

Aletheia requires a realistic software environment in which incidents can be introduced, observed, and systematically investigated. Building an investigation system directly against production systems is risky and non-reproducible. Conversely, building on mock strings or static datasets eliminates the reality of distributed timing, telemetry, and service dependencies.

## Decisions

1. **Framework & Language**:
   - Selected Python 3.12 and FastAPI for both the simulated production services (`checkout-api`) and the Aletheia platform backend (`aletheia-api`).
   - Rationale: High performance, native async support, type-safety with Pydantic v2, and direct compatibility with the target AI orchestration libraries (LangGraph) in subsequent phases.

2. **Persistence Layer**:
   - Selected PostgreSQL 16 (via Docker Compose) with SQLAlchemy 2.0 ORM.
   - Dual driver support (`psycopg` v3 and `psycopg2-binary`) to guarantee compatibility across environments.
   - For automated testing, an isolated SQLite setup provides sub-second test execution without requiring a live PostgreSQL instance for unit/integration suites.

3. **Separation of Concerns**:
   - `src/aletheia/`: The core incident investigation platform, reasoning engine, and evidence graph.
   - `simulator/`: The simulated production environment containing services (`checkout_api`), background traffic generation, and eventually failure injection hooks.
   - Keeps investigation logic strictly decoupled from target service logic.

4. **Service Health & Seeding**:
   - Services implement a `/health` endpoint that validates database reachability and measures query latency.
   - `checkout-api` auto-seeds an initial catalog of realistic tech hardware products if the database is empty, ensuring zero manual setup is needed after container launch.

5. **Configuration**:
   - Environment variables managed via `pydantic-settings` and `.env` files with strict typing and defaults.

## Consequences

- Clean local startup with a single command: `docker compose up --build`.
- Complete test coverage for models, APIs, and background traffic generator with zero dependencies on external internet access.
- Clear path forward for Phase 2 (Observability) and Phase 3 (Failure Injection).
