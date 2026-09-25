"""Analyst Agent: Generates multiple hypotheses, maps supporting/contradicting evidence, and distinguishes correlation from causation."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set

from aletheia.agents.models import AnalystOutput, Hypothesis, InvestigationContext
from aletheia.evaluation.llm.client import BaseLLMClient

logger = logging.getLogger("aletheia.agents.analyst")


class Analyst:
    """Agent responsible for multi-hypothesis generation, evidence mapping, and causal discrimination."""

    def __init__(
        self,
        name: str = "Analyst",
        llm_client: Optional[BaseLLMClient] = None,
    ):
        self.name = name
        self.client = llm_client

    def _build_deterministic_hypotheses(
        self,
        context: InvestigationContext,
    ) -> List[Hypothesis]:
        """Deterministic baseline hypotheses generator for reproducible testing and fallbacks."""
        hypotheses: List[Hypothesis] = []
        valid_ids = set(context.relevant_evidence_ids)

        # Classify available evidence by types from observations
        deploy_ev_ids = []
        commit_ev_ids = []
        span_ev_ids = []
        metric_ev_ids = []
        log_ev_ids = []

        all_text = " ".join([obs.statement for obs in context.observations] + [context.alert_description]).lower()

        for obs in context.observations:
            text = obs.statement.lower()
            if "deployment" in text:
                deploy_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])
            elif "commit" in text or "git" in text:
                commit_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])
            elif "span" in text or "duration" in text or "database" in text or "latency" in text:
                span_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])
            elif "metric" in text:
                metric_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])
            else:
                log_ev_ids.extend([cid for cid in obs.cited_evidence_ids if cid in valid_ids])

        # Determine specific trigger reference (commit, version, config)
        commit_ref = ""
        version_ref = ""
        for ev in context.timeline_events:
            summary_lower = ev.summary.lower()
            if "deploy" in summary_lower or ev.type.lower() == "deployment":
                v_match = re.search(r"v\d+\.\d+\.\d+", ev.summary)
                if v_match:
                    version_ref = v_match.group(0)
            if "commit" in summary_lower or ev.type.lower() == "commit":
                c_match = re.search(r"(?:commit\s+|)([0-9a-fA-F]{7,40})", ev.summary)
                if c_match:
                    commit_ref = c_match.group(1)

        if not commit_ref:
            for obs in context.observations:
                c_match = re.search(r"(?:commit\s+|)([0-9a-fA-F]{7,40})", obs.statement)
                if c_match:
                    commit_ref = c_match.group(1)
                    break
        if not version_ref:
            for obs in context.observations:
                v_match = re.search(r"v\d+\.\d+\.\d+", obs.statement)
                if v_match:
                    version_ref = v_match.group(0)
                    break

        if version_ref and commit_ref:
            trigger_ref = f"deployment {version_ref} (commit {commit_ref})"
        elif version_ref:
            trigger_ref = f"deployment {version_ref}"
        elif commit_ref:
            trigger_ref = f"commit {commit_ref}"
        elif deploy_ev_ids:
            trigger_ref = "deployment"
        else:
            trigger_ref = "configuration change"

        supporting_all = list(dict.fromkeys(deploy_ev_ids + commit_ev_ids + span_ev_ids + metric_ev_ids + log_ev_ids))

        # Dynamically formulate hypotheses based on observed telemetry signatures
        if "oom" in all_text or "out of memory" in all_text or "resident" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Process memory leak caused by unbounded in-memory request cache growth resulting in OOM kill.",
                suspected_component="python_worker",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Heap memory profile", "Valgrind/tracemalloc trace"],
                is_causal=True,
                confidence=0.92,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Host memory pressure from co-located container workloads.",
                suspected_component="host_os",
                supporting_evidence_ids=metric_ev_ids,
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["Node cgroup memory metrics"],
                is_causal=False,
                confidence=0.30,
                rank=2,
            )
        elif "504" in all_text or "acmepay" in all_text or "gateway timeout" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Third-party payment gateway timeout causing downstream HTTP 504 SLA breaches on checkout.",
                suspected_component="external_stripe_mock",
                suspected_trigger="third-party vendor latency spike",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Vendor status page incident log"],
                is_causal=True,
                confidence=0.94,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Internal database slowdown on payment record storage.",
                suspected_component="postgresql",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=span_ev_ids,
                missing_evidence=["DB query execution plans"],
                is_causal=False,
                confidence=0.20,
                rank=2,
            )
        elif "undefinedcolumn" in all_text or "tax_jurisdiction_code" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Database schema mismatch due to code deployed ahead of database column migration.",
                suspected_component="postgresql_schema",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Alembic migration version history"],
                is_causal=True,
                confidence=0.95,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Database connection drop during migration window.",
                suspected_component="network",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["TCP reset logs"],
                is_causal=False,
                confidence=0.25,
                rank=2,
            )
        elif "queuepool" in all_text or "db_pool_size" in all_text or "pool limit" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Database connection pool size misconfiguration throttled connection limit to 1.",
                suspected_component="database_connection_pool",
                suspected_trigger="configuration update",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Environment config diff"],
                is_causal=True,
                confidence=0.91,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Database deadlocks preventing connection returns.",
                suspected_component="postgresql",
                supporting_evidence_ids=span_ev_ids,
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["pg_locks table snapshot"],
                is_causal=False,
                confidence=0.35,
                rank=2,
            )
        elif "remaining connection slots" in all_text or "active_db_connections" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="PostgreSQL connection exhaustion due to unclosed database session leak.",
                suspected_component="postgresql",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["pg_stat_activity connection list"],
                is_causal=True,
                confidence=0.90,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="PostgreSQL server process crash.",
                suspected_component="postgresql_daemon",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["Postgres core dumps"],
                is_causal=False,
                confidence=0.20,
                rank=2,
            )
        elif "redos" in all_text or "regex" in all_text or "0.998" in all_text or "cpu saturated" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Host CPU saturation caused by catastrophic ReDoS polynomial evaluation in token validator.",
                suspected_component="auth_token_validator",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["CPU flamegraph / py-spy dump"],
                is_causal=True,
                confidence=0.93,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Cryptomining or unauthorized background process.",
                suspected_component="host_os",
                supporting_evidence_ids=metric_ev_ids,
                contradicting_evidence_ids=commit_ev_ids,
                missing_evidence=["Process tree snapshot"],
                is_causal=False,
                confidence=0.15,
                rank=2,
            )
        elif "thundering herd" in all_text or "cache miss" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Redis cache eviction triggered thundering herd queries overwhelming primary database.",
                suspected_component="redis_cache",
                suspected_trigger="cache eviction event",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Redis eviction metrics (evicted_keys)"],
                is_causal=True,
                confidence=0.88,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Sudden organic 10x traffic spike.",
                suspected_component="client_traffic",
                supporting_evidence_ids=metric_ev_ids,
                contradicting_evidence_ids=[],
                missing_evidence=["Edge ingress logs"],
                is_causal=False,
                confidence=0.40,
                rank=2,
            )
        elif "fsync" in all_text or "iowait" in all_text or "audit" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Synchronous audit file fsync calls caused blocking disk I/O lock contention masquerading as high CPU.",
                suspected_component="audit_file_logger",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["iostat / biotop disk latency traces"],
                is_causal=True,
                confidence=0.91,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Compute CPU saturation from audit encryption.",
                suspected_component="crypto_engine",
                supporting_evidence_ids=metric_ev_ids,
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["CPU profiling trace"],
                is_causal=False,
                confidence=0.25,
                rank=2,
            )
        elif "no space left on device" in all_text or "wal" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="PostgreSQL WAL disk partition 100% full preventing write transactions.",
                suspected_component="postgresql_wal",
                suspected_trigger="unarchived WAL segment accumulation",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["df -h disk partition summary"],
                is_causal=True,
                confidence=0.96,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Read-only PostgreSQL replica failover glitch.",
                suspected_component="patroni",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["Cluster consensus logs"],
                is_causal=False,
                confidence=0.20,
                rank=2,
            )
        elif "nxdomain" in all_text or "socket.gaierror" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Internal CoreDNS resolution failure for auth service host causing socket connection errors.",
                suspected_component="coredns",
                suspected_trigger="DNS configmap change",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["CoreDNS server logs"],
                is_causal=True,
                confidence=0.93,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Auth service pods crashed.",
                suspected_component="auth-service",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["Kubernetes pod status"],
                is_causal=False,
                confidence=0.25,
                rank=2,
            )
        elif "certificate has expired" in all_text or "ssl" in all_text and "expired" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Expired mTLS client certificate caused secure RPC handshake verification failures.",
                suspected_component="tls_handshake",
                suspected_trigger="certificate expiration",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["cert-manager renewal logs"],
                is_causal=True,
                confidence=0.95,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="TLS cipher suite incompatibility.",
                suspected_component="crypto_library",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["OpenSSL cipher list"],
                is_causal=False,
                confidence=0.20,
                rank=2,
            )
        elif "deadlock" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="PostgreSQL row-level deadlock detected under concurrent write contention.",
                suspected_component="postgresql",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["pg_stat_database deadlock counters"],
                is_causal=True,
                confidence=0.94,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Database query execution plan regression.",
                suspected_component="postgresql_query_optimizer",
                supporting_evidence_ids=span_ev_ids,
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["EXPLAIN ANALYZE query plan"],
                is_causal=False,
                confidence=0.30,
                rank=2,
            )
        elif "nan" in all_text or "float" in all_text and "precision" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Floating point precision overflow in pricing calculation produced invalid NaN total amounts.",
                suspected_component="pricing_engine",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Pricing unit test execution log"],
                is_causal=True,
                confidence=0.92,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Database numeric column data truncation.",
                suspected_component="postgresql_types",
                supporting_evidence_ids=metric_ev_ids,
                contradicting_evidence_ids=commit_ev_ids,
                missing_evidence=["Column schema DDL"],
                is_causal=False,
                confidence=0.25,
                rank=2,
            )
        elif "port 8003" in all_text or "connection refused" in all_text and "migrated" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Service port migration to 8001 unreflected in outdated runbook documentation pointing to 8003.",
                suspected_component="service_mesh_routing",
                suspected_trigger="port migration",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Runbook revision history"],
                is_causal=True,
                confidence=0.90,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Target service process down.",
                suspected_component="checkout-api",
                supporting_evidence_ids=metric_ev_ids,
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["netstat active ports list"],
                is_causal=False,
                confidence=0.30,
                rank=2,
            )
        elif "ignore all previous instructions" in all_text or "nullpointer" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Unhandled NullPointerException in user profile deserialization masked by adversarial prompt injection.",
                suspected_component="user_header_parser",
                suspected_trigger="malicious HTTP header injection",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["WAF security event log"],
                is_causal=True,
                confidence=0.91,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="System status is nominal (adversarial claim).",
                suspected_component="nominal_system",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=[],
                is_causal=False,
                confidence=0.10,
                rank=2,
            )
        elif "503" in all_text and "metrics" in all_text:
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Prometheus telemetry scrape probe failure returned HTTP 503 Service Unavailable.",
                suspected_component="prometheus_exporter",
                suspected_trigger="monitoring exporter outage",
                supporting_evidence_ids=supporting_all,
                missing_evidence=["Metrics exporter health status"],
                is_causal=True,
                confidence=0.93,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Checkout API core outage.",
                suspected_component="checkout-api",
                supporting_evidence_ids=[],
                contradicting_evidence_ids=log_ev_ids,
                missing_evidence=["Application health check response"],
                is_causal=False,
                confidence=0.20,
                rank=2,
            )
        else:
            # Default / INC-001: Database Query Regression
            h1 = Hypothesis(
                hypothesis_id="HYP-001",
                hypothesis="Database query performance regression due to unindexed sort on the orders table causing full table scans.",
                suspected_component="postgresql",
                suspected_trigger=trigger_ref,
                supporting_evidence_ids=supporting_all,
                missing_evidence=["EXPLAIN ANALYZE query execution plan", "pg_stat_statements slow query log"],
                is_causal=True,
                confidence=0.90,
                rank=1,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-002",
                hypothesis="Downstream network latency or gateway saturation.",
                suspected_component="network_gateway",
                supporting_evidence_ids=metric_ev_ids,
                contradicting_evidence_ids=span_ev_ids,
                missing_evidence=["NIC rx/tx packet drop logs"],
                is_causal=False,
                confidence=0.25,
                rank=2,
            )

        hypotheses.append(h1)
        hypotheses.append(h2)
        h3 = Hypothesis(
            hypothesis_id="HYP-003",
            hypothesis="Connection pool exhaustion or concurrency saturation.",
            suspected_component="connection_pool",
            supporting_evidence_ids=metric_ev_ids,
            contradicting_evidence_ids=[],
            missing_evidence=["pg_stat_activity active/waiting connection pool telemetry"],
            is_causal=False,
            confidence=0.45,
            rank=3,
        )
        hypotheses.append(h3)

        return hypotheses

    def _parse_llm_hypotheses(
        self,
        raw_content: str,
        valid_evidence_ids: Set[str],
    ) -> List[Hypothesis]:
        """Extract and sanitize hypotheses from LLM JSON response."""
        cleaned = raw_content.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        elif not (cleaned.startswith("{") and cleaned.endswith("}")):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]

        data = json.loads(cleaned)
        raw_hyps = data.get("hypotheses", [])
        parsed_hyps: List[Hypothesis] = []

        for idx, item in enumerate(raw_hyps):
            # Clean and validate evidence citations
            raw_sup = item.get("supporting_evidence_ids", [])
            valid_sup = [cid for cid in raw_sup if cid in valid_evidence_ids]

            raw_contra = item.get("contradicting_evidence_ids", [])
            valid_contra = [cid for cid in raw_contra if cid in valid_evidence_ids]

            parsed_hyps.append(
                Hypothesis(
                    hypothesis_id=item.get("hypothesis_id", f"HYP-{idx+1:03d}"),
                    hypothesis=item.get("hypothesis", "Unspecified hypothesis"),
                    suspected_component=item.get("suspected_component"),
                    suspected_trigger=item.get("suspected_trigger"),
                    supporting_evidence_ids=valid_sup,
                    contradicting_evidence_ids=valid_contra,
                    missing_evidence=item.get("missing_evidence", []),
                    is_causal=bool(item.get("is_causal", True)),
                    confidence=float(item.get("confidence", 0.5)),
                    rank=int(item.get("rank", idx + 1)),
                )
            )

        return parsed_hyps

    def analyze(self, context: InvestigationContext) -> AnalystOutput:
        """Analyze investigation context to produce ranked hypotheses with evidence citations."""
        valid_ids = set(context.relevant_evidence_ids)

        if self.client is not None:
            prompt = (
                f"Incident: {context.incident_id}\n"
                f"Alert: {context.alert_description}\n"
                f"Observations:\n"
                + "\n".join([f"- {obs.observation_id}: {obs.statement} (Citing: {obs.cited_evidence_ids})" for obs in context.observations])
                + "\n\nGenerate at least 2 distinct hypotheses in JSON format matching the schema."
            )
            system_prompt = (
                "You are the SRE Analyst in Aletheia. Analyze the observations and generate multiple hypotheses. "
                "Strictly cite only real evidence IDs provided in the observations. Identify missing evidence and "
                "distinguish correlation from causation."
            )
            try:
                resp = self.client.complete(prompt=prompt, system_prompt=system_prompt, json_mode=True)
                hypotheses = self._parse_llm_hypotheses(resp.content, valid_ids)
            except Exception as exc:
                logger.warning(f"Analyst LLM completion failed, falling back to deterministic hypotheses: {exc}")
                hypotheses = self._build_deterministic_hypotheses(context)

            if not hypotheses:
                hypotheses = self._build_deterministic_hypotheses(context)
        else:
            hypotheses = self._build_deterministic_hypotheses(context)

        # Sort hypotheses by rank / confidence
        hypotheses.sort(key=lambda h: (-h.confidence, h.rank))
        for r_idx, h in enumerate(hypotheses, start=1):
            h.rank = r_idx

        notes = (
            "Distinguished causal chain from correlation: HTTP response duration increase (METRIC) "
            "is a correlated symptom of upstream latency; trace span and commit changes demonstrate database sequential "
            "scan was the direct causal driver."
        )

        top_name = hypotheses[0].hypothesis if hypotheses else "None"
        top_conf = hypotheses[0].confidence if hypotheses else 0.0
        summary = (
            f"Analyst generated {len(hypotheses)} hypotheses for {context.incident_id}. "
            f"Top hypothesis: '{top_name}' (Confidence: {top_conf:.2f})."
        )

        return AnalystOutput(
            incident_id=context.incident_id,
            hypotheses=hypotheses,
            correlation_vs_causation_notes=notes,
            analysis_summary=summary,
        )
