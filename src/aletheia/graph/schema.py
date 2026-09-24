"""Graph schema defining relationship types, nodes, and edges."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from aletheia.evidence.entities import Entity
from aletheia.evidence.events import Event


class RelationshipType(str, Enum):
    """Explicit typed relationships between graph nodes."""
    # Causality and Influence
    INTRODUCED = "INTRODUCED"
    MODIFIED = "MODIFIED"
    EXECUTES_ON = "EXECUTES_ON"
    CALLS = "CALLS"
    INCREASED = "INCREASED"
    CONTRIBUTED_TO = "CONTRIBUTED_TO"
    CAUSED = "CAUSED"

    # Temporal
    PRECEDES = "PRECEDES"
    COINCIDES_WITH = "COINCIDES_WITH"

    # Associative and Adversarial
    CORRELATES_WITH = "CORRELATES_WITH"
    CONTRADICTS = "CONTRADICTS"
    DEPENDS_ON = "DEPENDS_ON"


class GraphNode(BaseModel):
    """A node in the evidence graph representing an Entity or Event."""
    model_config = ConfigDict(extra="ignore")

    node_id: str = Field(..., description="Unique node ID")
    label: str = Field(..., description="Human-readable display label")
    category: str = Field(..., description="Node category: ENTITY or EVENT")
    entity: Optional[Entity] = None
    event: Optional[Event] = None
    timestamp: Optional[datetime] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed, typed relationship connecting two graph nodes."""
    model_config = ConfigDict(extra="ignore")

    edge_id: str = Field(..., description="Unique edge identifier")
    source_id: str = Field(..., description="Origin node ID")
    target_id: str = Field(..., description="Destination node ID")
    type: RelationshipType = Field(..., description="Typed relationship classification")
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="IDs of backing evidence supporting this relationship",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in this relationship")
    properties: Dict[str, Any] = Field(default_factory=dict)
