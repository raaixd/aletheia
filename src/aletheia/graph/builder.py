"""Deterministic evidence graph builder."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from aletheia.evidence.entities import Entity, EntityType
from aletheia.evidence.events import Event, EventType, Timeline
from aletheia.evidence.schema import EvidenceItem, EvidenceType
from aletheia.graph.graph import EvidenceGraph
from aletheia.graph.schema import GraphEdge, GraphNode, RelationshipType


class EvidenceGraphBuilder:
    """Constructs a deterministic EvidenceGraph and Timeline from raw evidence and entities."""

    def __init__(self):
        self.graph = EvidenceGraph()
        self.timeline = Timeline()
        self._edge_counter = 0

    def _next_edge_id(self) -> str:
        self._edge_counter += 1
        return f"edge-{self._edge_counter:04d}"

    def add_entity_node(self, entity: Entity) -> GraphNode:
        """Register an entity as a graph node."""
        node = GraphNode(
            node_id=entity.entity_id,
            label=f"{entity.type.value}: {entity.name}",
            category="ENTITY",
            entity=entity,
            timestamp=entity.first_seen,
            properties=entity.properties,
        )
        self.graph.add_node(node)
        return node

    def add_event_node(self, event: Event) -> GraphNode:
        """Register an event as a graph node and append to the chronological timeline."""
        node = GraphNode(
            node_id=f"evt:{event.event_id}",
            label=f"{event.type.value}: {event.summary}",
            category="EVENT",
            event=event,
            timestamp=event.timestamp,
            properties=event.details,
        )
        self.graph.add_node(node)
        self.timeline.add_event(event)
        return node

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        evidence_ids: Optional[List[str]] = None,
        confidence: float = 1.0,
        properties: Optional[Dict] = None,
    ) -> GraphEdge:
        """Create a directed relationship edge backed by evidence provenance."""
        edge = GraphEdge(
            edge_id=self._next_edge_id(),
            source_id=source_id,
            target_id=target_id,
            type=rel_type,
            evidence_ids=evidence_ids or [],
            confidence=confidence,
            properties=properties or {},
        )
        self.graph.add_edge(edge)
        return edge

    def build_temporal_sequence(self) -> None:
        """Link consecutive timeline events with PRECEDES edges."""
        sorted_events = self.timeline.get_events()
        for i in range(len(sorted_events) - 1):
            e1 = sorted_events[i]
            e2 = sorted_events[i + 1]
            src_node_id = f"evt:{e1.event_id}"
            tgt_node_id = f"evt:{e2.event_id}"
            if src_node_id in self.graph.nodes and tgt_node_id in self.graph.nodes:
                self.add_relationship(
                    source_id=src_node_id,
                    target_id=tgt_node_id,
                    rel_type=RelationshipType.PRECEDES,
                    evidence_ids=list(set(e1.evidence_ids + e2.evidence_ids)),
                    properties={"time_delta_seconds": (e2.timestamp - e1.timestamp).total_seconds()},
                )

    @classmethod
    def build_for_inc_001(
        cls,
        evidence_items: List[EvidenceItem],
        start_time: Optional[datetime] = None,
    ) -> "EvidenceGraphBuilder":
        """Deterministic graph constructor for INC-001 Database Query Regression.

        Reconstructs the full causal and temporal chain:
        Deployment v4.2.1
            ↓ (INTRODUCED)
        Commit abc12348f9
            ↓ (MODIFIED)
        Database Query (SELECT orders)
            ↓ (INCREASED)
        Database Query Latency
            ↓ (CONTRIBUTED_TO)
        Checkout API Latency
            ↓ (CAUSED)
        Errors / Degradation
        """
        builder = cls()
        base_time = start_time or datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc)

        # 1. Map evidence by type for provenance association
        evidence_by_type: Dict[EvidenceType, List[EvidenceItem]] = {}
        for item in evidence_items:
            evidence_by_type.setdefault(item.type, []).append(item)

        deploy_ev_ids = [e.evidence_id for e in evidence_by_type.get(EvidenceType.DEPLOYMENT, [])]
        commit_ev_ids = [e.evidence_id for e in evidence_by_type.get(EvidenceType.COMMIT, [])]
        span_ev_ids = [e.evidence_id for e in evidence_by_type.get(EvidenceType.SPAN, [])]
        log_ev_ids = [e.evidence_id for e in evidence_by_type.get(EvidenceType.LOG, [])]
        metric_ev_ids = [e.evidence_id for e in evidence_by_type.get(EvidenceType.METRIC, [])]

        # 2. Add System Entities
        service_node = builder.add_entity_node(
            Entity(
                entity_id="svc:checkout-api",
                type=EntityType.SERVICE,
                name="checkout-api",
                service="checkout-api",
                properties={"environment": "production-sim", "version": "v4.2.1"},
            )
        )
        db_node = builder.add_entity_node(
            Entity(
                entity_id="db:postgres",
                type=EntityType.DATABASE,
                name="postgres",
                properties={"system": "postgresql", "name": "checkout_db"},
            )
        )
        endpoint_node = builder.add_entity_node(
            Entity(
                entity_id="ep:checkout-api:GET:/api/orders",
                type=EntityType.ENDPOINT,
                name="GET /api/orders",
                service="checkout-api",
            )
        )
        deploy_node = builder.add_entity_node(
            Entity(
                entity_id="deploy:checkout-api:v4.2.1",
                type=EntityType.DEPLOYMENT,
                name="Release v4.2.1",
                service="checkout-api",
                first_seen=datetime(2026, 9, 25, 2, 2, 0, tzinfo=timezone.utc),
            )
        )
        commit_node = builder.add_entity_node(
            Entity(
                entity_id="commit:abc12348f9",
                type=EntityType.COMMIT,
                name="Commit abc12348f9",
                service="checkout-api",
                first_seen=datetime(2026, 9, 25, 2, 1, 0, tzinfo=timezone.utc),
                properties={
                    "message": "refactor: optimize orders lookup without index",
                    "changed_files": ["simulator/services/checkout_api/routes.py"],
                },
            )
        )

        # 3. Add Temporal Events
        e1 = Event(
            event_id="EVT-001",
            timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
            type=EventType.NORMAL_TRAFFIC,
            service="checkout-api",
            summary="Normal background traffic across checkout endpoints (<10ms latency)",
            evidence_ids=metric_ev_ids[:1],
        )
        e2 = Event(
            event_id="EVT-002",
            timestamp=datetime(2026, 9, 25, 2, 2, 0, tzinfo=timezone.utc),
            type=EventType.DEPLOYMENT_COMPLETE,
            service="checkout-api",
            summary="Deployment of release v4.2.1 completed on checkout-api",
            entity_ids=[deploy_node.node_id, commit_node.node_id],
            evidence_ids=deploy_ev_ids,
        )
        e3 = Event(
            event_id="EVT-003",
            timestamp=datetime(2026, 9, 25, 2, 3, 0, tzinfo=timezone.utc),
            type=EventType.QUERY_CHANGED,
            service="checkout-api",
            summary="Order history SQL query execution plan modified (unindexed sort)",
            entity_ids=[commit_node.node_id, db_node.node_id],
            evidence_ids=commit_ev_ids,
        )
        e4 = Event(
            event_id="EVT-004",
            timestamp=datetime(2026, 9, 25, 2, 4, 0, tzinfo=timezone.utc),
            type=EventType.DB_LATENCY_INCREASE,
            service="checkout-api",
            summary="Database query execution time rose from 3ms to 1500ms on orders query",
            entity_ids=[db_node.node_id],
            evidence_ids=span_ev_ids,
        )
        e5 = Event(
            event_id="EVT-005",
            timestamp=datetime(2026, 9, 25, 2, 5, 0, tzinfo=timezone.utc),
            type=EventType.API_LATENCY_INCREASE,
            service="checkout-api",
            summary="GET /api/orders average and P99 latency exceeded 1500ms SLA",
            entity_ids=[endpoint_node.node_id, service_node.node_id],
            evidence_ids=metric_ev_ids + log_ev_ids,
        )

        builder.add_event_node(e1)
        builder.add_event_node(e2)
        builder.add_event_node(e3)
        builder.add_event_node(e4)
        builder.add_event_node(e5)

        # 4. Add Causal and Structural Relationships with Provenance
        builder.add_relationship(
            service_node.node_id,
            db_node.node_id,
            RelationshipType.EXECUTES_ON,
        )
        builder.add_relationship(
            service_node.node_id,
            endpoint_node.node_id,
            RelationshipType.CALLS,
        )
        builder.add_relationship(
            deploy_node.node_id,
            commit_node.node_id,
            RelationshipType.INTRODUCED,
            evidence_ids=deploy_ev_ids + commit_ev_ids,
        )
        builder.add_relationship(
            commit_node.node_id,
            "evt:EVT-003",
            RelationshipType.MODIFIED,
            evidence_ids=commit_ev_ids,
        )
        builder.add_relationship(
            "evt:EVT-003",
            "evt:EVT-004",
            RelationshipType.INCREASED,
            evidence_ids=span_ev_ids or log_ev_ids,
        )
        builder.add_relationship(
            "evt:EVT-004",
            "evt:EVT-005",
            RelationshipType.CONTRIBUTED_TO,
            evidence_ids=span_ev_ids + metric_ev_ids,
        )

        # 5. Build Temporal Precedence Sequence
        builder.build_temporal_sequence()

        return builder
