"""Abstract EvidenceSource interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from aletheia.evidence.schema import EvidenceItem


class EvidenceSource(ABC):
    """Abstract interface defining standard evidence collection capabilities.

    Subclasses implement adapters for local environments, Prometheus,
    OpenTelemetry, GitHub, Sentry, CloudWatch, etc.
    """

    @abstractmethod
    def get_logs(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        """Collect application and system logs."""
        pass

    @abstractmethod
    def get_metrics(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        """Collect metric time series and measurements."""
        pass

    @abstractmethod
    def get_traces(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        """Collect distributed trace spans."""
        pass

    @abstractmethod
    def get_deployments(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        """Collect deployment and release events."""
        pass

    @abstractmethod
    def get_code_changes(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        """Collect source code commits and configuration changes."""
        pass
