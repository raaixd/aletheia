# ADR 0009: Incident Investigation Instrument Frontend Architecture

## Context
The Aletheia frontend has been completely redesigned from the ground up as a specialized **investigation instrument** rather than a generic SaaS dashboard or CRUD admin panel.

Key requirements:
1. **Instrument Identity**:
   - Palette: Deep matte obsidian (`#08090d`) base paired with Crimson Blue (Prussian slate navy: `#0a1120`, `#14223b`, `#1e3356`), sharp Crimson Red accents (`#e11d48`) for alerts, contradictions, and critical severity, and calm verified emerald (`#10b981`) for grounded evidence.
   - Typography: Plus Jakarta Sans for confident, editorial interface text paired with JetBrains Mono for technical identifiers (evidence IDs, trace IDs, timestamps, commit SHAs, metrics).
   - Removed decorative clichés: Zero fake AI brain graphics, zero quotes around definition statements, zero Greek translation characters.
2. **Editorial Progressive Narrative**:
   - The primary investigation page is structured as a vertical investigative narrative rather than a boxed card grid:
     `Incident Header → What Happened (Timeline Rail) → Indexed Evidence Record → Competing Hypotheses → Adversarial Verifier Audit → Deterministic Root Cause Diagnosis`.
3. **Dedicated Operational Views**:
   - **Overview**: Product introduction with active investigation preview, compact timeline sequence, and architectural proof pillars.
   - **Investigate**: Deep investigative narrative with interactive evidence inspection.
   - **Incidents**: List-based catalog of 20 benchmark scenarios with real-time text search and severity filters.
   - **Evidence Map**: Focused causal dependency DAG tracing triggers, commit diffs, query regressions, and SLA breaches.
   - **Evaluations**: Scientific 3-way comparative benchmark table (Single-LLM vs 2-Agent vs 3-Agent Aletheia).
   - **System**: Live LLMOps telemetry workstation with token accounting and trace inspection.
4. **Backend Integration**: Real-time consumption of FastAPI backend endpoints (`/api/v1/investigation/*`, `/api/v1/llmops/*`) through Next.js proxy rewrites (`/api/backend/*`).

## Decision
- Build with Next.js 16 (App Router + Turbopack) and custom CSS custom property tokens.
- Keep the existing backend architecture intact; consume real data without mock fallbacks in standard runs.
- Provide slide-out provenance inspection for raw evidence telemetry.

## Consequences
- Produces a calm, high-precision developer-grade instrument suitable for production incident commanders and AI infrastructure portfolios.
