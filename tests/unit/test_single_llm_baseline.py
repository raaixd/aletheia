"""Unit tests for SingleLLMBaseline."""

import pytest
from datetime import datetime, timezone

from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.llm.client import MockLLMClient, MockMode
from aletheia.evidence.events import Event, EventType, Timeline
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance


@pytest.fixture
def sample_context():
    provenance = EvidenceProvenance(
        source_type=EvidenceSourceType.GITHUB,
        source_uri="github://releases",
        extracted_at=datetime.now(timezone.utc),
        extraction_method="test",
    )
    items = [
        EvidenceItem(
            evidence_id="EV-DEP-0001",
            timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
            source=EvidenceSourceType.GITHUB,
            type=EvidenceType.DEPLOYMENT,
            service="checkout-api",
            content="Deployed v4.2.1",
            provenance=provenance,
        )
    ]
    timeline = Timeline()
    timeline.add_event(Event(
        event_id="EVT-001",
        timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
        type=EventType.DEPLOYMENT_COMPLETE,
        service="checkout-api",
        summary="Deployed v4.2.1",
    ))
    return items, timeline


def test_single_llm_baseline_diagnose_accurate(sample_context):
    items, timeline = sample_context
    client = MockLLMClient(mode=MockMode.ACCURATE)
    baseline = SingleLLMBaseline(name="test-baseline", llm_client=client)

    result = baseline.diagnose(
        incident_id="INC-001",
        alert_description="Latency SLA breach",
        evidence_items=items,
        timeline=timeline,
    )

    assert result.incident_id == "INC-001"
    assert result.root_cause_category == "slow_database_query"
    assert "abc12348f9" in result.introduced_by
    assert result.confidence >= 0.90
    assert len(result.cited_evidence_ids) > 0
    assert result.usage_metadata.get("prompt_tokens", 0) > 0


def test_single_llm_baseline_markdown_fences_json_parsing(sample_context):
    items, timeline = sample_context
    raw_markdown = """Here is my diagnosis:
```json
{
  "incident_id": "INC-001",
  "root_cause": "Database query performance regression",
  "root_cause_category": "slow_database_query",
  "suspected_component": "postgresql",
  "introduced_by": "commit abc12348f9",
  "affected_service": "checkout-api",
  "explanation": "Markdown code fence test",
  "cited_evidence_ids": ["EV-DEP-0001"],
  "confidence": 0.9,
  "recommended_fix": "Add index"
}
```
Hope this helps!"""

    client = MockLLMClient(custom_response=raw_markdown)
    baseline = SingleLLMBaseline(name="test-fence", llm_client=client)

    result = baseline.diagnose(
        incident_id="INC-001",
        alert_description="Latency SLA breach",
        evidence_items=items,
        timeline=timeline,
    )

    assert result.root_cause == "Database query performance regression"
    assert result.suspected_component == "postgresql"
    assert result.confidence == 0.9


def test_single_llm_baseline_invalid_json_fallback(sample_context):
    items, timeline = sample_context
    client = MockLLMClient(mode=MockMode.INVALID_JSON)
    baseline = SingleLLMBaseline(name="test-invalid", llm_client=client)

    result = baseline.diagnose(
        incident_id="INC-001",
        alert_description="Latency SLA breach",
        evidence_items=items,
        timeline=timeline,
    )

    assert result.confidence == 0.0
    assert "Model output parsing error" in result.root_cause
