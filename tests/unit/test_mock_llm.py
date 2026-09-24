"""Unit tests for MockLLMClient and prompt generation."""

import pytest
from datetime import datetime, timezone

from aletheia.evaluation.baselines.single_llm import calculate_cost
from aletheia.evaluation.llm.client import MockLLMClient, MockMode
from aletheia.evaluation.llm.prompts import BaselinePromptBuilder
from aletheia.evidence.events import Event, EventType, Timeline
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance


def test_mock_llm_client_accurate_mode():
    client = MockLLMClient(mode=MockMode.ACCURATE)
    resp = client.complete(prompt="Investigate incident INC-001", json_mode=True)
    assert resp.prompt_tokens > 0
    assert resp.completion_tokens > 0
    assert resp.total_tokens == resp.prompt_tokens + resp.completion_tokens
    assert "slow_database_query" in resp.content
    assert "EV-SPAN-0001" in resp.content


def test_mock_llm_client_hallucinated_mode():
    client = MockLLMClient(mode=MockMode.HALLUCINATED)
    resp = client.complete(prompt="Investigate incident INC-001")
    assert "memory_leak" in resp.content
    assert "EV-FAKE-9999" in resp.content


def test_mock_llm_client_partial_mode():
    client = MockLLMClient(mode=MockMode.PARTIAL)
    resp = client.complete(prompt="Investigate incident INC-001")
    assert "slow_database_query" in resp.content
    assert '"introduced_by": "unknown"' in resp.content


def test_mock_llm_client_invalid_json_mode():
    client = MockLLMClient(mode=MockMode.INVALID_JSON)
    resp = client.complete(prompt="Investigate incident INC-001")
    assert not resp.content.strip().startswith("{")


def test_baseline_prompt_builder():
    timeline = Timeline()
    timeline.add_event(Event(
        event_id="EVT-001",
        timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
        type=EventType.DEPLOYMENT_COMPLETE,
        service="checkout-api",
        summary="Deployed v4.2.1",
    ))

    items = [
        EvidenceItem(
            evidence_id="EV-DEP-0001",
            timestamp=datetime(2026, 9, 25, 2, 0, 0, tzinfo=timezone.utc),
            source=EvidenceSourceType.GITHUB,
            type=EvidenceType.DEPLOYMENT,
            service="checkout-api",
            content="Deployed v4.2.1",
            provenance=EvidenceProvenance(
                source_type=EvidenceSourceType.GITHUB,
                source_uri="github://releases",
                extracted_at=datetime.now(timezone.utc),
                extraction_method="test",
            ),
        )
    ]

    prompt = BaselinePromptBuilder.build_user_prompt(
        incident_id="INC-001",
        alert_description="Latency SLA breach",
        evidence_items=items,
        timeline=timeline,
    )

    assert "INC-001" in prompt
    assert "Latency SLA breach" in prompt
    assert "EV-DEP-0001" in prompt
    assert "Deployed v4.2.1" in prompt


def test_calculate_cost():
    cost_mini = calculate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost_mini == 0.75  # 0.15 + 0.60
    cost_mock = calculate_cost("mock", 100, 100)
    assert cost_mock == 0.0
