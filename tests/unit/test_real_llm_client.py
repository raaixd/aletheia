"""Unit tests for OpenAILLMClient, real LLM client abstractions, and API failure/timeout handling."""

import json
import os
import httpx
import pytest

from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.llm.client import (
    LLMAPIError,
    LLMTimeoutError,
    OpenAILLMClient,
)
from aletheia.evidence.schema import EvidenceItem, EvidenceType, EvidenceSourceType, EvidenceProvenance
from datetime import datetime, timezone


def test_openai_llm_client_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-env-key-xyz")
    client = OpenAILLMClient()
    assert client.api_key == "test-env-key-xyz"


def test_openai_llm_client_successful_completion():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == "Bearer my-secret-key"
        body = json.loads(request.content)
        assert body["model"] == "gpt-4o-mini"
        assert len(body["messages"]) == 2

        response_json = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"incident_id": "INC-001", "root_cause": "unindexed sort"}),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 45,
                "total_tokens": 165,
            },
        }
        return httpx.Response(200, json=response_json)

    transport = httpx.MockTransport(mock_handler)
    client = OpenAILLMClient(api_key="my-secret-key", transport=transport)
    resp = client.complete(prompt="Analyze incident", system_prompt="You are an SRE")

    assert resp.model == "gpt-4o-mini"
    assert resp.prompt_tokens == 120
    assert resp.completion_tokens == 45
    assert resp.total_tokens == 165
    assert "unindexed sort" in resp.content


def test_openai_llm_client_timeout_handling():
    def mock_timeout_handler(request: httpx.Request):
        raise httpx.TimeoutException("Read timed out")

    transport = httpx.MockTransport(mock_timeout_handler)
    client = OpenAILLMClient(api_key="test-key", transport=transport)

    with pytest.raises(LLMTimeoutError) as exc_info:
        client.complete(prompt="Analyze incident")
    assert "timed out" in str(exc_info.value).lower()


def test_openai_llm_client_api_error_handling():
    def mock_error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "Rate limit exceeded"}})

    transport = httpx.MockTransport(mock_error_handler)
    client = OpenAILLMClient(api_key="test-key", transport=transport)

    with pytest.raises(LLMAPIError) as exc_info:
        client.complete(prompt="Analyze incident")
    assert "429" in str(exc_info.value)
    assert "Rate limit exceeded" in str(exc_info.value)


def test_single_llm_baseline_graceful_api_failure():
    def mock_error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(mock_error_handler)
    client = OpenAILLMClient(api_key="test-key", transport=transport)
    baseline = SingleLLMBaseline(name="Test-Baseline-Error", llm_client=client)

    item = EvidenceItem(
        evidence_id="EV-TEST-1",
        timestamp=datetime.now(timezone.utc),
        source=EvidenceSourceType.APPLICATION_LOG,
        type=EvidenceType.LOG,
        service="checkout-api",
        content="Test log",
        provenance=EvidenceProvenance(
            source_type=EvidenceSourceType.APPLICATION_LOG,
            source_uri="test",
            extracted_at=datetime.now(timezone.utc),
            extraction_method="test",
        ),
    )

    diagnosis = baseline.diagnose(
        incident_id="INC-001",
        alert_description="Latency spike",
        evidence_items=[item],
    )

    assert diagnosis.confidence == 0.0
    assert "LLM API failure" in diagnosis.root_cause
    assert diagnosis.cited_evidence_ids == []
