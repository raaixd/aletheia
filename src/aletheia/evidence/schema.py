"""Evidence schema and provenance models for Aletheia."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceType(str, Enum):
    """Categorization of evidence items."""
    LOG = "LOG"
    METRIC = "METRIC"
    TRACE = "TRACE"
    SPAN = "SPAN"
    DEPLOYMENT = "DEPLOYMENT"
    COMMIT = "COMMIT"
    CONFIGURATION = "CONFIGURATION"
    DATABASE_STATE = "DATABASE_STATE"
    ALERT = "ALERT"


class EvidenceSourceType(str, Enum):
    """Origin of collected evidence."""
    APPLICATION_LOG = "APPLICATION_LOG"
    PROMETHEUS = "PROMETHEUS"
    OPENTELEMETRY = "OPENTELEMETRY"
    GITHUB = "GITHUB"
    POSTGRESQL = "POSTGRESQL"
    LOCAL_SIMULATOR = "LOCAL_SIMULATOR"


class EvidenceProvenance(BaseModel):
    """Audit trail detailing the exact provenance of an evidence item."""
    model_config = ConfigDict(extra="ignore")

    source_type: EvidenceSourceType
    source_uri: str = Field(..., description="File path, URL, or stream URI where evidence originated")
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when evidence was ingested/collected",
    )
    extraction_method: str = Field(..., description="Adapter or query mechanism used to collect evidence")
    raw_reference: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Pointer to raw source data (e.g., line number, span ID, metric sample)",
    )


class EvidenceItem(BaseModel):
    """A discrete, verifiable unit of evidence gathered from the system."""
    model_config = ConfigDict(extra="ignore")

    evidence_id: str = Field(..., description="Unique evidence identifier, e.g. E-101")
    timestamp: datetime = Field(..., description="UTC timestamp of the underlying event or measurement")
    source: EvidenceSourceType = Field(..., description="Source system")
    type: EvidenceType = Field(..., description="Category of evidence")
    service: str = Field(..., description="Associated service identifier")
    entity_ids: List[str] = Field(default_factory=list, description="IDs of entities referenced by this evidence")
    content: str = Field(..., description="Descriptive, factual representation of the evidence")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured factual data")
    provenance: EvidenceProvenance = Field(..., description="Provenance information")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Collection provenance confidence")
