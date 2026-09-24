"""Base interface for incident diagnostic systems."""

from abc import ABC, abstractmethod
from typing import List, Optional

from aletheia.evidence.events import Timeline
from aletheia.evidence.schema import EvidenceItem
from aletheia.evaluation.models import DiagnosisResult


class BaseDiagnosticSystem(ABC):
    """Abstract base class for diagnostic systems under evaluation."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def diagnose(
        self,
        incident_id: str,
        alert_description: str,
        evidence_items: List[EvidenceItem],
        timeline: Optional[Timeline] = None,
    ) -> DiagnosisResult:
        """Execute diagnosis over observable evidence and timeline."""
        pass
