# ADR 0009: Developer-Grade Incident Investigation Frontend Architecture

## Context
Phase 9 mandates an intuitive, highly polished, developer-grade frontend interface for Aletheia. The previous interface was rejected for being cluttered and resembling a generic AI dashboard rather than a serious, developer-focused infrastructure tool.

Key requirements:
1. **Aesthetic Direction**: Minimalist, matte dark theme (`#09090b`), subtle `#27272a` borders, clean typography (Geist/Inter/JetBrains Mono), disciplined spacing, and zero gratuitous gradients or "AI magic" decorations.
2. **Core Narrative Flow**: Walk investigators through a strict, progressive causal story:
   `Incident Overview -> Chronological Timeline -> Evidence Layer -> Analyst Hypotheses -> Verifier Challenges -> Final Verified Diagnosis`.
3. **Dedicated Views**: Uncluttered, focused secondary views for:
   - **Incidents Catalog**: Full 20-scenario incident benchmark suite with search and category filtering.
   - **Evidence Graph**: Focused causal chain visualization without cluttering the main diagnostic page.
   - **Comparative Benchmark**: 3-way evaluation metrics table comparing Single-LLM, 2-Agent, and 3-Agent Aletheia on accuracy, hallucination, latency, and cost.
   - **LLMOps System Traces**: Observability log with live token accounting, latency, and cost tracking.
4. **Backend Integration**: Real-time consumption of FastAPI backend endpoints (`/api/v1/investigation/incidents`, `/api/v1/investigation/diagnose/{id}`, `/api/v1/llmops/traces`) through a Next.js reverse proxy rewrite.

## Decision
1. **Framework**: Next.js 16 (React 19, TypeScript) with Turbopack for near-instant client-side transitions and zero build bloat.
2. **Design System**: Tailored Vanilla CSS design system in `frontend/app/globals.css` adhering to obsidian surfaces, muted borders, subtle status indicators (emerald, amber, rose, sky), and clear monospaced identifiers.
3. **Linear Progressive Disclosure**: The main investigation view structures diagnostic findings linearly down the screen. An incident timeline rail establishes temporal sequencing before presenting evidence cards, followed by competing hypotheses, adversarial audit results, and the authoritative root-cause diagnosis.
4. **Proxy Architecture**: `frontend/next.config.ts` proxies `/api/backend/:path*` directly to `http://127.0.0.1:8000/:path*` to eliminate CORS complexities in development and deployment.

## Consequences
- **Positive**: Clean, developer-oriented experience matching modern infrastructure platforms (Linear, Datadog, Hermes-Agent); eliminates cognitive overload while presenting verifiable proof chains.
- **Positive**: Direct integration with existing backend APIs with zero mock data in production builds.
- **Negative**: Requires Node.js and Next.js runtime alongside Python backend for full local development.
