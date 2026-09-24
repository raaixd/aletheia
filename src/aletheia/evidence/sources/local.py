"""Local evidence source integrating local telemetry adapters."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from aletheia.evidence.schema import EvidenceItem
from aletheia.evidence.sources.base import EvidenceSource
from aletheia.evidence.sources.log_adapter import LogAdapter
from aletheia.evidence.sources.trace_adapter import TraceAdapter
from aletheia.evidence.sources.metric_adapter import MetricAdapter
from aletheia.evidence.sources.deploy_adapter import DeployAdapter
from aletheia.observability.tracing import get_memory_exporter


class LocalEvidenceSource(EvidenceSource):
    """Gathers evidence from local memory buffers, structured logs, and simulated telemetry."""

    def __init__(self, default_service: str = "checkout-api"):
        self.default_service = default_service
        self.log_adapter = LogAdapter(default_service=default_service)
        self.trace_adapter = TraceAdapter(default_service=default_service)
        self.metric_adapter = MetricAdapter(default_service=default_service)
        self.deploy_adapter = DeployAdapter()

        # In-memory stores for manual ingestion / simulation replay
        self._raw_logs: List[Dict[str, Any]] = []
        self._raw_spans: List[Any] = []
        self._raw_metrics: List[Dict[str, Any]] = []
        self._raw_deployments: List[Dict[str, Any]] = []
        self._raw_commits: List[Dict[str, Any]] = []

    def ingest_log_entry(self, entry: Dict[str, Any]) -> None:
        """Add a raw log dictionary to local store."""
        self._raw_logs.append(entry)

    def ingest_deployment(self, service: str, version: str, commit_sha: str, timestamp: datetime) -> None:
        """Add a deployment event."""
        self._raw_deployments.append({
            "service": service,
            "version": version,
            "commit_sha": commit_sha,
            "timestamp": timestamp,
        })

    def ingest_commit(
        self,
        service: str,
        commit_sha: str,
        author: str,
        message: str,
        timestamp: datetime,
        changed_files: Optional[List[str]] = None,
    ) -> None:
        """Add a commit record."""
        self._raw_commits.append({
            "service": service,
            "commit_sha": commit_sha,
            "author": author,
            "message": message,
            "timestamp": timestamp,
            "changed_files": changed_files or [],
        })

    def ingest_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: datetime,
        service: str = "checkout-api",
        endpoint: str = "/api/orders",
    ) -> None:
        """Add a metric sample."""
        self._raw_metrics.append({
            "metric_name": metric_name,
            "value": value,
            "timestamp": timestamp,
            "service": service,
            "endpoint": endpoint,
        })

    def get_logs(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        items = []
        for idx, entry in enumerate(self._raw_logs, start=1):
            if service and entry.get("service") != service:
                continue
            item = self.log_adapter.parse_log_entry(entry, item_index=idx)
            if start_time and item.timestamp < start_time:
                continue
            if end_time and item.timestamp > end_time:
                continue
            items.append(item)
        return items

    def get_traces(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        # Collect from in-memory OpenTelemetry exporter if available
        exporter = get_memory_exporter()
        spans_to_parse = list(self._raw_spans)
        if exporter:
            spans_to_parse.extend(exporter.get_finished_spans())

        items = []
        for idx, span in enumerate(spans_to_parse, start=1):
            item = self.trace_adapter.parse_span(span, item_index=idx)
            if service and item.service != service:
                continue
            if start_time and item.timestamp < start_time:
                continue
            if end_time and item.timestamp > end_time:
                continue
            items.append(item)
        return items

    def get_metrics(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        items = []
        for idx, m in enumerate(self._raw_metrics, start=1):
            if service and m.get("service") != service:
                continue
            item = self.metric_adapter.create_metric_evidence(
                metric_name=m["metric_name"],
                value=m["value"],
                timestamp=m["timestamp"],
                service=m.get("service", self.default_service),
                endpoint=m.get("endpoint", "/api/orders"),
                item_index=idx,
            )
            if start_time and item.timestamp < start_time:
                continue
            if end_time and item.timestamp > end_time:
                continue
            items.append(item)
        return items

    def get_deployments(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        items = []
        for idx, d in enumerate(self._raw_deployments, start=1):
            if service and d.get("service") != service:
                continue
            item = self.deploy_adapter.create_deployment_evidence(
                service=d["service"],
                version=d["version"],
                commit_sha=d["commit_sha"],
                timestamp=d["timestamp"],
                item_index=idx,
            )
            if start_time and item.timestamp < start_time:
                continue
            if end_time and item.timestamp > end_time:
                continue
            items.append(item)
        return items

    def get_code_changes(
        self,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EvidenceItem]:
        items = []
        for idx, c in enumerate(self._raw_commits, start=1):
            if service and c.get("service") != service:
                continue
            item = self.deploy_adapter.create_commit_evidence(
                service=c["service"],
                commit_sha=c["commit_sha"],
                author=c["author"],
                message=c["message"],
                timestamp=c["timestamp"],
                changed_files=c.get("changed_files"),
                item_index=idx,
            )
            if start_time and item.timestamp < start_time:
                continue
            if end_time and item.timestamp > end_time:
                continue
            items.append(item)
        return items
