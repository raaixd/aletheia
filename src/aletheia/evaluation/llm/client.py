"""LLM Client abstractions supporting Mock, OpenAI-compatible, and configurable providers."""

import json
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from aletheia.config.settings import get_settings

logger = logging.getLogger("aletheia.eval.llm")


class LLMCompletionResponse(BaseModel):
    """Normalized response payload from an LLM completion call."""
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_seconds: float = 0.0
    model: str = "mock"


class MockMode(str, Enum):
    """Simulation modes for MockLLMClient."""
    ACCURATE = "accurate"
    HALLUCINATED = "hallucinated"
    PARTIAL = "partial"
    INVALID_JSON = "invalid_json"


class BaseLLMClient(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
    ) -> LLMCompletionResponse:
        """Execute a text/chat completion."""
        pass


class MockLLMClient(BaseLLMClient):
    """Deterministic mock client for hermetic unit testing and evaluation harness validation."""

    def __init__(
        self,
        mode: MockMode = MockMode.ACCURATE,
        custom_response: Optional[str] = None,
        model_name: str = "mock-eval-model",
    ):
        self.mode = mode
        self.custom_response = custom_response
        self.model_name = model_name

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
    ) -> LLMCompletionResponse:
        start_time = time.perf_counter()

        if self.custom_response is not None:
            content = self.custom_response
        elif self.mode == MockMode.ACCURATE:
            content = json.dumps({
                "incident_id": "INC-001",
                "root_cause": "Database query performance regression due to unindexed sort on the orders table introduced in release v4.2.1",
                "root_cause_category": "slow_database_query",
                "suspected_component": "postgresql",
                "introduced_by": "commit abc12348f9 (deployment v4.2.1)",
                "affected_service": "checkout-api",
                "explanation": (
                    "Deployment v4.2.1 introduced commit abc12348f9 which modified the orders lookup "
                    "query in checkout-api to sort by updated_at without an index. This caused PostgreSQL "
                    "to perform a full sequential scan on the orders table, driving query duration to ~1500ms "
                    "and causing GET /api/orders latency to breach the SLA."
                ),
                "cited_evidence_ids": [
                    "EV-DEP-0001",
                    "EV-GIT-0001",
                    "EV-SPAN-0001",
                    "EV-METRIC-0002",
                ],
                "confidence": 0.95,
                "recommended_fix": (
                    "Add an index on orders(created_at, user_id) or rollback deployment v4.2.1 "
                    "(commit abc12348f9) immediately."
                ),
            }, indent=2)
        elif self.mode == MockMode.HALLUCINATED:
            content = json.dumps({
                "incident_id": "INC-001",
                "root_cause": "JVM garbage collection pause and memory leak in the checkout worker thread pool",
                "root_cause_category": "memory_leak",
                "suspected_component": "jvm_heap",
                "introduced_by": "commit 0000deadbeef",
                "affected_service": "billing-service",
                "explanation": (
                    "A memory leak in the JVM metaspace caused long Stop-the-World GC pauses exceeding "
                    "15 seconds, preventing checkout-api from receiving heartbeats."
                ),
                "cited_evidence_ids": [
                    "EV-FAKE-9999",
                    "EV-JVM-0001",
                ],
                "confidence": 0.99,
                "recommended_fix": "Increase JVM Xmx heap size to 16GB and restart the pod cluster.",
            }, indent=2)
        elif self.mode == MockMode.PARTIAL:
            content = json.dumps({
                "incident_id": "INC-001",
                "root_cause": "High database query latency on orders table causing checkout API response degradation",
                "root_cause_category": "slow_database_query",
                "suspected_component": "postgresql",
                "introduced_by": "unknown",
                "affected_service": "checkout-api",
                "explanation": (
                    "Traces and metrics reveal that database query execution latency spiked to 1500ms, "
                    "which caused downstream latency spikes on the /api/orders endpoint. Cause of the query "
                    "slowdown is undetermined from the immediate logs."
                ),
                "cited_evidence_ids": [
                    "EV-SPAN-0001",
                    "EV-METRIC-0002",
                ],
                "confidence": 0.70,
                "recommended_fix": "Investigate database connection pool and query execution plans.",
            }, indent=2)
        elif self.mode == MockMode.INVALID_JSON:
            content = "Sorry, I am an AI and I think the database might be running slow but I cannot produce JSON."
        else:
            raise ValueError(f"Unsupported mock mode: {self.mode}")

        latency = time.perf_counter() - start_time
        prompt_tokens = max(10, len(prompt.split()))
        completion_tokens = max(10, len(content.split()))
        total_tokens = prompt_tokens + completion_tokens

        try:
            import uuid
            from aletheia.reliability.traces import LLMCallTrace, get_trace_recorder
            get_trace_recorder().record_trace(
                LLMCallTrace(
                    trace_id=f"trace-mock-{uuid.uuid4().hex[:8]}",
                    agent_name="MockLLMClient",
                    model=self.model_name,
                    latency_ms=round(latency * 1000, 2),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    status="success",
                )
            )
        except Exception:
            pass

        return LLMCompletionResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_seconds=round(latency, 4),
            model=self.model_name,
        )


class LLMError(Exception):
    """Base exception for LLM operations."""
    pass


class LLMAPIError(LLMError):
    """Raised when an LLM API returns an error status or malformed response."""
    pass


class LLMTimeoutError(LLMAPIError):
    """Raised when an LLM API request times out."""
    pass


class OpenAILLMClient(BaseLLMClient):
    """Direct HTTP client for OpenAI-compatible Chat Completion APIs (OpenAI, Gemini, Ollama, etc.)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        timeout: float = 60.0,
        transport: Optional[Any] = None,
    ):
        import os
        settings = get_settings()
        self.api_key = api_key or settings.llm_api_key or os.environ.get("OPENAI_API_KEY") or ""
        self.base_url = (base_url or settings.llm_base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model or settings.llm_model or "gpt-4o-mini"
        self.temperature = temperature
        self.timeout = timeout
        self.transport = transport

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
    ) -> LLMCompletionResponse:
        import httpx

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = f"{self.base_url}/chat/completions"
        start_time = time.perf_counter()
        retries_tracker = {"count": 0}

        def _do_post():
            try:
                with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    return resp.json()
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(f"LLM API request timed out after {self.timeout}s: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                raise LLMAPIError(f"LLM API HTTP error {exc.response.status_code}: {exc.response.text}") from exc
            except (httpx.RequestError, json.JSONDecodeError, KeyError) as exc:
                raise LLMAPIError(f"LLM API request/parsing error: {exc}") from exc

        def _on_retry(attempt, exc, backoff):
            retries_tracker["count"] = attempt

        import uuid
        trace_id = f"trace-openai-{uuid.uuid4().hex[:8]}"

        try:
            from aletheia.reliability.resilience import execute_with_retry
            data = execute_with_retry(
                _do_post,
                max_retries=3,
                initial_backoff=0.05,
                retry_hook=_on_retry,
            )
        except Exception as exc:
            lat_ms = (time.perf_counter() - start_time) * 1000
            try:
                from aletheia.reliability.traces import LLMCallTrace, get_trace_recorder
                get_trace_recorder().record_trace(
                    LLMCallTrace(
                        trace_id=trace_id,
                        agent_name="OpenAILLMClient",
                        model=self.model,
                        latency_ms=round(lat_ms, 2),
                        status="error",
                        retries_attempted=retries_tracker["count"],
                        error_message=str(exc),
                    )
                )
            except Exception:
                pass
            raise

        latency = time.perf_counter() - start_time
        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", len(prompt.split()))
        completion_tokens = usage.get("completion_tokens", len(content.split()))
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        rates = {"gpt-4o-mini": (0.15, 0.60), "gpt-4o": (2.50, 10.00)}.get(self.model, (0.15, 0.60))
        cost = round((prompt_tokens / 1_000_000 * rates[0]) + (completion_tokens / 1_000_000 * rates[1]), 6)

        try:
            from aletheia.reliability.traces import LLMCallTrace, get_trace_recorder
            get_trace_recorder().record_trace(
                LLMCallTrace(
                    trace_id=trace_id,
                    agent_name="OpenAILLMClient",
                    model=data.get("model", self.model),
                    latency_ms=round(latency * 1000, 2),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=cost,
                    status="retried" if retries_tracker["count"] > 0 else "success",
                    retries_attempted=retries_tracker["count"],
                )
            )
        except Exception:
            pass

        return LLMCompletionResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_seconds=round(latency, 4),
            model=data.get("model", self.model),
        )


def get_llm_client(
    provider: Optional[str] = None,
    mock_mode: Optional[str] = None,
    **kwargs,
) -> BaseLLMClient:
    """Factory helper to obtain the configured LLM client."""
    settings = get_settings()
    chosen_provider = (provider or settings.llm_provider).lower()

    if chosen_provider in ("mock", "test"):
        mode_str = mock_mode or settings.llm_mock_mode
        try:
            mode_enum = MockMode(mode_str.lower())
        except ValueError:
            mode_enum = MockMode.ACCURATE
        return MockLLMClient(mode=mode_enum, **kwargs)
    elif chosen_provider in ("openai", "openai-compatible"):
        return OpenAILLMClient(**kwargs)
    else:
        logger.warning(f"Unknown LLM provider '{chosen_provider}', defaulting to MockLLMClient.")
        return MockLLMClient(mode=MockMode.ACCURATE)
