"""Aletheia Evidence Package."""

from aletheia.evidence.schema import (
    EvidenceItem,
    EvidenceType,
    EvidenceSourceType,
    EvidenceProvenance,
)
from aletheia.evidence.entities import (
    Entity,
    EntityType,
    create_service_entity,
    create_deployment_entity,
    create_commit_entity,
    create_database_entity,
    create_endpoint_entity,
    create_metric_entity,
    create_error_entity,
    create_trace_entity,
)
from aletheia.evidence.events import Event, EventType, Timeline
from aletheia.evidence.sources.base import EvidenceSource
from aletheia.evidence.sources.local import LocalEvidenceSource
from aletheia.evidence.sources.log_adapter import LogAdapter
from aletheia.evidence.sources.trace_adapter import TraceAdapter
from aletheia.evidence.sources.metric_adapter import MetricAdapter
from aletheia.evidence.sources.deploy_adapter import DeployAdapter

__all__ = [
    "EvidenceItem",
    "EvidenceType",
    "EvidenceSourceType",
    "EvidenceProvenance",
    "Entity",
    "EntityType",
    "create_service_entity",
    "create_deployment_entity",
    "create_commit_entity",
    "create_database_entity",
    "create_endpoint_entity",
    "create_metric_entity",
    "create_error_entity",
    "create_trace_entity",
    "Event",
    "EventType",
    "Timeline",
    "EvidenceSource",
    "LocalEvidenceSource",
    "LogAdapter",
    "TraceAdapter",
    "MetricAdapter",
    "DeployAdapter",
]
