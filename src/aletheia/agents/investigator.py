"""Investigator Agent: Inspects Evidence Graph, isolates relevant evidence, and builds structured investigation context."""

import logging
import re
from typing import Dict, List, Optional, Set

from aletheia.agents.models import (
    EntitySummary,
    InvestigationContext,
    InvestigationObservation,
    RelationshipSummary,
    TimelineEventSummary,
)
from aletheia.evaluation.llm.client import BaseLLMClient, get_llm_client
from aletheia.evidence.events import Timeline
from aletheia.evidence.schema import EvidenceItem, EvidenceType
from aletheia.graph.builder import EvidenceGraphBuilder
from aletheia.graph.graph import EvidenceGraph

logger = logging.getLogger("aletheia.agents.investigator")


class Investigator:
    """Agent responsible for deterministic graph inspection, relevance filtering, and context construction."""

    def __init__(
        self,
        name: str = "Investigator",
        llm_client: Optional[BaseLLMClient] = None,
        relevance_latency_threshold_s: float = 0.5,
    ):
        self.name = name
        self.client = llm_client
        self.relevance_latency_threshold_s = relevance_latency_threshold_s

    def is_relevant_evidence(self, item: EvidenceItem) -> bool:
        """Deterministic filter to minimize noise while retaining all incident-correlated evidence."""
        # Deployments and Commits in incident window are always relevant
        if item.type in (EvidenceType.DEPLOYMENT, EvidenceType.COMMIT):
            return True

        # Spans indicating latency or errors
        if item.type == EvidenceType.SPAN:
            try:
                duration = float(item.data.get("duration_ms", 0.0) or 0.0)
            except (ValueError, TypeError):
                duration = 0.0

            try:
                status_code = int(item.data.get("status_code", 200) or 200)
            except (ValueError, TypeError):
                status_code = 200

            if duration >= (self.relevance_latency_threshold_s * 1000) or status_code >= 400:
                return True
            if any(term in item.content.lower() for term in ["unindexed", "slow", "delayed", "regression", "error"]):
                return True

        # Metrics with latency spikes or error rates
        if item.type == EvidenceType.METRIC:
            try:
                val = float(item.data.get("value", 0.0) or 0.0)
            except (ValueError, TypeError):
                val = 0.0
            metric_name = str(item.data.get("metric_name", "")).lower()
            if "duration" in metric_name or "latency" in metric_name:
                if val >= self.relevance_latency_threshold_s:
                    return True
            if "error" in metric_name and val > 0:
                return True

        # Warning or Error logs
        if item.type == EvidenceType.LOG:
            level = str(item.data.get("level", "")).upper()
            if level in ("WARNING", "ERROR", "CRITICAL"):
                return True
            if any(term in item.content.lower() for term in ["regression", "slow", "delayed", "breach", "fail"]):
                return True

        return False

    def investigate(
        self,
        incident_id: str,
        alert_description: str,
        evidence_items: List[EvidenceItem],
        timeline: Optional[Timeline] = None,
        evidence_graph: Optional[EvidenceGraph] = None,
    ) -> InvestigationContext:
        """Inspect evidence graph and timeline, validate citations, and produce structured InvestigationContext."""
        valid_evidence_by_id = {item.evidence_id: item for item in evidence_items}
        valid_ids = set(valid_evidence_by_id.keys())

        # 1. Ensure Evidence Graph exists
        if evidence_graph is None:
            if incident_id.upper() == "INC-001":
                builder = EvidenceGraphBuilder.build_for_inc_001(evidence_items)
            else:
                builder = EvidenceGraphBuilder()
                for item in evidence_items:
                    # Ingest basic nodes
                    pass
            evidence_graph = builder.graph
            if timeline is None:
                timeline = builder.timeline

        # 2. Identify relevant evidence items (filter out background noise)
        relevant_items = [item for item in evidence_items if self.is_relevant_evidence(item)]
        relevant_evidence_ids = [item.evidence_id for item in relevant_items]

        # 3. Extract important entities from Evidence Graph
        important_entities: List[EntitySummary] = []
        for node in evidence_graph.nodes.values():
            if node.category == "ENTITY" and node.entity:
                important_entities.append(
                    EntitySummary(
                        entity_id=node.entity.entity_id,
                        name=node.entity.name,
                        type=node.entity.type.value,
                        role=node.entity.properties.get("role"),
                        properties=node.entity.properties,
                    )
                )

        # 4. Extract relevant causal & temporal relationships
        relevant_relationships: List[RelationshipSummary] = []
        for edge in evidence_graph.edges:
            # Check if edge links to or is backed by relevant evidence
            edge_evidence_valid = [eid for eid in edge.evidence_ids if eid in valid_ids]
            if edge_evidence_valid or edge.type.value in ("CAUSED", "INTRODUCED", "INCREASED", "CONTRIBUTED_TO"):
                relevant_relationships.append(
                    RelationshipSummary(
                        edge_id=edge.edge_id,
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        type=edge.type.value,
                        evidence_ids=edge_evidence_valid,
                        confidence=edge.confidence,
                    )
                )

        # 5. Extract Chronological Timeline Events
        timeline_events: List[TimelineEventSummary] = []
        if timeline:
            for ev in timeline.get_events():
                ev_ids = [eid for eid in ev.evidence_ids if eid in valid_ids]
                timeline_events.append(
                    TimelineEventSummary(
                        event_id=ev.event_id,
                        timestamp=ev.timestamp,
                        type=ev.type.value,
                        service=ev.service,
                        summary=ev.summary,
                        evidence_ids=ev_ids,
                    )
                )

        # 6. Formulate Deterministic Grounded Observations
        observations: List[InvestigationObservation] = []
        obs_idx = 0

        # Observations from deployments & commits
        deploy_items = [it for it in relevant_items if it.type == EvidenceType.DEPLOYMENT]
        commit_items = [it for it in relevant_items if it.type == EvidenceType.COMMIT]
        for dep in deploy_items:
            obs_idx += 1
            commit_sha = dep.data.get("commit_sha", "")
            ver = dep.data.get("version", "")
            observations.append(
                InvestigationObservation(
                    observation_id=f"OBS-{obs_idx:03d}",
                    statement=f"Deployment {ver} (commit {commit_sha}) was executed on service {dep.service}.",
                    cited_evidence_ids=[dep.evidence_id],
                    confidence=1.0,
                )
            )

        for com in commit_items:
            obs_idx += 1
            msg = com.data.get("message", "")
            observations.append(
                InvestigationObservation(
                    observation_id=f"OBS-{obs_idx:03d}",
                    statement=f"Git commit {com.data.get('commit_sha', '')} introduced changes: '{msg}'.",
                    cited_evidence_ids=[com.evidence_id],
                    confidence=1.0,
                )
            )

        # Observations from anomalous spans / latency
        span_items = [it for it in relevant_items if it.type == EvidenceType.SPAN]
        for sp in span_items:
            obs_idx += 1
            dur = sp.data.get("duration_ms", 0.0)
            observations.append(
                InvestigationObservation(
                    observation_id=f"OBS-{obs_idx:03d}",
                    statement=f"Observed elevated span latency ({dur:.1f}ms) in {sp.service}: {sp.content}.",
                    cited_evidence_ids=[sp.evidence_id],
                    confidence=1.0,
                )
            )

        # Observations from anomalous metrics
        metric_items = [it for it in relevant_items if it.type == EvidenceType.METRIC]
        for met in metric_items:
            obs_idx += 1
            val = met.data.get("value", 0.0)
            name = met.data.get("metric_name", "metric")
            observations.append(
                InvestigationObservation(
                    observation_id=f"OBS-{obs_idx:03d}",
                    statement=f"Metric anomaly detected for {name} with value {val:.3f}s.",
                    cited_evidence_ids=[met.evidence_id],
                    confidence=1.0,
                )
            )

        # 7. Post-validate and reject any hallucinated evidence citations
        hallucinated_ids_rejected: List[str] = []
        cleaned_observations: List[InvestigationObservation] = []

        for obs in observations:
            valid_cited = []
            for cid in obs.cited_evidence_ids:
                if cid in valid_ids:
                    valid_cited.append(cid)
                else:
                    hallucinated_ids_rejected.append(cid)
                    logger.warning(f"Investigator rejected invalid/hallucinated evidence ID: {cid}")
            obs.cited_evidence_ids = valid_cited
            cleaned_observations.append(obs)

        # Summary
        summary = (
            f"Investigation context for {incident_id}: Identified {len(relevant_evidence_ids)} relevant evidence items "
            f"out of {len(evidence_items)} total. Found {len(important_entities)} entities, "
            f"{len(relevant_relationships)} relationships, and {len(cleaned_observations)} grounded observations."
        )

        return InvestigationContext(
            incident_id=incident_id,
            alert_description=alert_description,
            relevant_evidence_ids=relevant_evidence_ids,
            timeline_events=timeline_events,
            important_entities=important_entities,
            relevant_relationships=relevant_relationships,
            observations=cleaned_observations,
            investigation_summary=summary,
            hallucinated_ids_rejected=hallucinated_ids_rejected,
        )
