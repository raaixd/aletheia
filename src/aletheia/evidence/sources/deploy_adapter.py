"""Adapter converting deployment releases and code commits into EvidenceItems."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance


class DeployAdapter:
    """Parses deployment releases and Git commits into EvidenceItems."""

    def create_deployment_evidence(
        self,
        service: str,
        version: str,
        commit_sha: str,
        timestamp: datetime,
        item_index: int = 1,
        source_uri: str = "github://releases/v4.2.1",
    ) -> EvidenceItem:
        """Create evidence item representing a service deployment."""
        evidence_id = f"EV-DEP-{item_index:04d}"
        entity_ids = [
            f"svc:{service}",
            f"deploy:{service}:{version}",
            f"commit:{commit_sha}",
        ]

        provenance = EvidenceProvenance(
            source_type=EvidenceSourceType.GITHUB,
            source_uri=source_uri,
            extracted_at=datetime.now(timezone.utc),
            extraction_method="DeployAdapter.create_deployment_evidence",
            raw_reference={"version": version, "commit_sha": commit_sha},
        )

        return EvidenceItem(
            evidence_id=evidence_id,
            timestamp=timestamp,
            source=EvidenceSourceType.GITHUB,
            type=EvidenceType.DEPLOYMENT,
            service=service,
            entity_ids=entity_ids,
            content=f"Deployed {service} version {version} (commit {commit_sha[:8]})",
            data={
                "version": version,
                "commit_sha": commit_sha,
                "service": service,
            },
            provenance=provenance,
            confidence=1.0,
        )

    def create_commit_evidence(
        self,
        service: str,
        commit_sha: str,
        author: str,
        message: str,
        timestamp: datetime,
        changed_files: Optional[List[str]] = None,
        item_index: int = 1,
        source_uri: str = "github://commits/abc12348f9",
    ) -> EvidenceItem:
        """Create evidence item representing a Git commit."""
        evidence_id = f"EV-GIT-{item_index:04d}"
        entity_ids = [
            f"svc:{service}",
            f"commit:{commit_sha}",
        ]

        provenance = EvidenceProvenance(
            source_type=EvidenceSourceType.GITHUB,
            source_uri=source_uri,
            extracted_at=datetime.now(timezone.utc),
            extraction_method="DeployAdapter.create_commit_evidence",
            raw_reference={"commit_sha": commit_sha, "author": author},
        )

        return EvidenceItem(
            evidence_id=evidence_id,
            timestamp=timestamp,
            source=EvidenceSourceType.GITHUB,
            type=EvidenceType.COMMIT,
            service=service,
            entity_ids=entity_ids,
            content=f"Commit {commit_sha[:8]}: {message} by {author}",
            data={
                "commit_sha": commit_sha,
                "author": author,
                "message": message,
                "changed_files": changed_files or [],
            },
            provenance=provenance,
            confidence=1.0,
        )
