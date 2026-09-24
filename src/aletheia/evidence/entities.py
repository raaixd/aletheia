"""Structured entity representations across the system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    """Categorization of system entities."""
    INCIDENT = "INCIDENT"
    SERVICE = "SERVICE"
    DEPLOYMENT = "DEPLOYMENT"
    COMMIT = "COMMIT"
    DATABASE = "DATABASE"
    ENDPOINT = "ENDPOINT"
    METRIC = "METRIC"
    ERROR = "ERROR"
    TRACE = "TRACE"
    SPAN = "SPAN"


class Entity(BaseModel):
    """Universal entity representation within the incident landscape."""
    model_config = ConfigDict(extra="ignore")

    entity_id: str = Field(..., description="Globally unique entity ID, e.g. svc:checkout-api")
    type: EntityType = Field(..., description="Entity category")
    name: str = Field(..., description="Human-readable name")
    service: Optional[str] = Field(None, description="Associated service if applicable")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Detailed attributes")
    first_seen: Optional[datetime] = Field(None, description="Earliest known timestamp")
    last_seen: Optional[datetime] = Field(None, description="Most recent known timestamp")


def create_service_entity(name: str, version: str = "1.0.0", environment: str = "production") -> Entity:
    """Create a Service entity."""
    return Entity(
        entity_id=f"svc:{name}",
        type=EntityType.SERVICE,
        name=name,
        service=name,
        properties={"version": version, "environment": environment},
    )


def create_deployment_entity(service: str, version: str, commit_sha: str, timestamp: datetime) -> Entity:
    """Create a Deployment entity."""
    return Entity(
        entity_id=f"deploy:{service}:{version}",
        type=EntityType.DEPLOYMENT,
        name=f"Deployment {version} ({service})",
        service=service,
        first_seen=timestamp,
        last_seen=timestamp,
        properties={"version": version, "commit_sha": commit_sha, "timestamp": timestamp.isoformat()},
    )


def create_commit_entity(
    sha: str,
    author: str,
    message: str,
    timestamp: datetime,
    service: str = "checkout-api",
    changed_files: Optional[List[str]] = None,
) -> Entity:
    """Create a Git Commit entity."""
    return Entity(
        entity_id=f"commit:{sha}",
        type=EntityType.COMMIT,
        name=f"Commit {sha[:8]}",
        service=service,
        first_seen=timestamp,
        last_seen=timestamp,
        properties={
            "sha": sha,
            "author": author,
            "message": message,
            "timestamp": timestamp.isoformat(),
            "changed_files": changed_files or [],
        },
    )


def create_database_entity(name: str, db_type: str = "postgresql", host: str = "localhost") -> Entity:
    """Create a Database entity."""
    return Entity(
        entity_id=f"db:{name}",
        type=EntityType.DATABASE,
        name=f"Database {name}",
        properties={"db_type": db_type, "host": host, "database_name": name},
    )


def create_endpoint_entity(service: str, method: str, path: str) -> Entity:
    """Create an HTTP Endpoint entity."""
    clean_path = path.strip()
    return Entity(
        entity_id=f"ep:{service}:{method.upper()}:{clean_path}",
        type=EntityType.ENDPOINT,
        name=f"{method.upper()} {clean_path}",
        service=service,
        properties={"method": method.upper(), "path": clean_path},
    )


def create_metric_entity(service: str, metric_name: str, unit: str = "seconds") -> Entity:
    """Create a Metric entity."""
    return Entity(
        entity_id=f"metric:{service}:{metric_name}",
        type=EntityType.METRIC,
        name=metric_name,
        service=service,
        properties={"metric_name": metric_name, "unit": unit},
    )


def create_error_entity(service: str, error_type: str, message: str, timestamp: datetime) -> Entity:
    """Create an Error entity."""
    return Entity(
        entity_id=f"err:{service}:{error_type}",
        type=EntityType.ERROR,
        name=error_type,
        service=service,
        first_seen=timestamp,
        last_seen=timestamp,
        properties={"error_type": error_type, "message": message},
    )


def create_trace_entity(trace_id: str, service: str, duration_ms: float, timestamp: datetime) -> Entity:
    """Create a Trace entity."""
    return Entity(
        entity_id=f"trace:{trace_id}",
        type=EntityType.TRACE,
        name=f"Trace {trace_id[:8]}",
        service=service,
        first_seen=timestamp,
        last_seen=timestamp,
        properties={"trace_id": trace_id, "duration_ms": duration_ms},
    )
