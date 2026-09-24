"""Unit tests for evidence schema, provenance, and entity models."""

from datetime import datetime, timezone
import pytest

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
)


@pytest.mark.unit
def test_evidence_item_creation_and_provenance():
    """Verify EvidenceItem correctly stores provenance and metadata."""
    now = datetime.now(timezone.utc)
    prov = EvidenceProvenance(
        source_type=EvidenceSourceType.APPLICATION_LOG,
        source_uri="stdout",
        extracted_at=now,
        extraction_method="LogAdapter",
        raw_reference={"line": 42},
    )

    item = EvidenceItem(
        evidence_id="EV-100",
        timestamp=now,
        source=EvidenceSourceType.APPLICATION_LOG,
        type=EvidenceType.LOG,
        service="checkout-api",
        entity_ids=["svc:checkout-api"],
        content="Order lookup executed",
        data={"query": "SELECT orders"},
        provenance=prov,
        confidence=1.0,
    )

    assert item.evidence_id == "EV-100"
    assert item.provenance.source_type == EvidenceSourceType.APPLICATION_LOG
    assert item.provenance.raw_reference["line"] == 42
    assert item.confidence == 1.0


@pytest.mark.unit
def test_entity_creation_helpers():
    """Verify entity factory functions create properly formatted entity IDs and attributes."""
    now = datetime.now(timezone.utc)
    svc = create_service_entity("checkout-api", version="1.0.0")
    assert svc.entity_id == "svc:checkout-api"
    assert svc.type == EntityType.SERVICE

    deploy = create_deployment_entity("checkout-api", "v4.2.1", "abc123", now)
    assert deploy.entity_id == "deploy:checkout-api:v4.2.1"
    assert deploy.type == EntityType.DEPLOYMENT

    commit = create_commit_entity("abc12348f9", "alex.dev@example.com", "refactor query", now)
    assert commit.entity_id == "commit:abc12348f9"
    assert commit.type == EntityType.COMMIT

    db = create_database_entity("postgres", "postgresql", "localhost")
    assert db.entity_id == "db:postgres"
    assert db.type == EntityType.DATABASE

    ep = create_endpoint_entity("checkout-api", "GET", "/api/orders")
    assert ep.entity_id == "ep:checkout-api:GET:/api/orders"
    assert ep.type == EntityType.ENDPOINT
