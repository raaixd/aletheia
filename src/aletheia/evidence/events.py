"""Event representations and deterministic timeline builder."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Categorization of discrete system events."""
    NORMAL_TRAFFIC = "NORMAL_TRAFFIC"
    DEPLOYMENT_START = "DEPLOYMENT_START"
    DEPLOYMENT_COMPLETE = "DEPLOYMENT_COMPLETE"
    CODE_CHANGE = "CODE_CHANGE"
    QUERY_CHANGED = "QUERY_CHANGED"
    DB_LATENCY_INCREASE = "DB_LATENCY_INCREASE"
    API_LATENCY_INCREASE = "API_LATENCY_INCREASE"
    ERROR_RATE_INCREASE = "ERROR_RATE_INCREASE"
    SERVICE_DEGRADATION = "SERVICE_DEGRADATION"
    EXTERNAL_DEPENDENCY_CALL = "EXTERNAL_DEPENDENCY_CALL"


class Event(BaseModel):
    """A discrete temporal event occurring in the system."""
    model_config = ConfigDict(extra="ignore")

    event_id: str = Field(..., description="Unique event identifier, e.g. EVT-001")
    timestamp: datetime = Field(..., description="Precise UTC timestamp of occurrence")
    type: EventType = Field(..., description="Classification of the event")
    service: str = Field(..., description="Service where the event manifested")
    summary: str = Field(..., description="Human-readable summary of the event")
    entity_ids: List[str] = Field(default_factory=list, description="Associated entity identifiers")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of backing evidence items")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured event parameters")


class Timeline(BaseModel):
    """Deterministic, chronologically ordered sequence of system events."""
    model_config = ConfigDict(extra="ignore")

    events: List[Event] = Field(default_factory=list)

    def add_event(self, event: Event) -> None:
        """Add an event and maintain chronological ordering."""
        self.events.append(event)
        self.events.sort(key=lambda e: e.timestamp)

    def get_events(self) -> List[Event]:
        """Return events strictly ordered by timestamp."""
        return sorted(self.events, key=lambda e: e.timestamp)

    def get_events_for_service(self, service: str) -> List[Event]:
        """Filter events by associated service."""
        return [e for e in self.get_events() if e.service == service]

    def get_time_window(self, start: datetime, end: datetime) -> List[Event]:
        """Filter events within a specific time range [start, end]."""
        return [e for e in self.get_events() if start <= e.timestamp <= end]

    def format_ascii(self) -> str:
        """Format the timeline into an engineer-readable ASCII diagram."""
        if not self.events:
            return "No events recorded in timeline."

        sorted_events = self.get_events()
        lines = ["=== INCIDENT TIMELINE ==="]
        for e in sorted_events:
            time_str = e.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            lines.append(f"[{time_str}] [{e.service}] [{e.type.value}] {e.summary} (evidence: {', '.join(e.evidence_ids) or 'none'})")
        lines.append("=========================")
        return "\n".join(lines)
