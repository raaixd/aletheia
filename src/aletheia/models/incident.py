"""Data models for Aletheia incidents, ground truth, and scenarios."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IncidentGroundTruth(BaseModel):
    """Ground truth specification for an incident.

    CRITICAL RULE:
    Ground truth exists ONLY for evaluation and verification against the AI's diagnosis.
    Ground truth answers must never be fed directly into diagnostic agents as clues.
    """
    model_config = ConfigDict(extra="ignore")

    incident_id: str = Field(..., description="Unique incident identifier, e.g. INC-001")
    name: str = Field(..., description="Canonical incident name")
    root_cause: str = Field(..., description="The verified root cause of the incident")
    introduced_by: Optional[str] = Field(None, description="Commit, deployment, or actor that introduced the failure")
    affected_service: str = Field(..., description="Primary service impacted")
    start_time: Optional[str] = Field(None, description="Timestamp when the failure began")
    expected_evidence: List[str] = Field(
        default_factory=list,
        description="Key evidence items an accurate investigation should uncover",
    )
    ground_truth_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed technical ground truth attributes for rigorous scoring",
    )


class FailureInjectionRequest(BaseModel):
    """Request payload to dynamically inject a failure into the simulated environment."""
    incident_id: str = Field(..., description="Incident ID to activate, e.g. INC-001")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional runtime parameter overrides (e.g. latency_ms, error_rate)",
    )


class FailureStatusResponse(BaseModel):
    """Current status of failure injections in the simulator."""
    active_incidents: Dict[str, Dict[str, Any]]
    total_active: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
