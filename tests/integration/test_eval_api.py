"""Integration tests for Evaluation REST API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_get_evaluation_baselines(aletheia_client: TestClient):
    resp = aletheia_client.get("/api/v1/eval/baselines")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(b["id"] == "single-llm" for b in data)


def test_post_eval_run_accurate_mock(aletheia_client: TestClient):
    payload = {
        "incident_id": "INC-001",
        "baseline": "single-llm",
        "mock_mode": "accurate",
    }
    resp = aletheia_client.post("/api/v1/eval/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_id"] == "INC-001"
    assert data["overall_score"] >= 0.90
    assert data["root_cause_score"]["passed"] is True
    assert data["hallucination_score"]["passed"] is True

    # Test report retrieval
    report_id = data["report_id"]
    get_resp = aletheia_client.get(f"/api/v1/eval/reports/{report_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["report_id"] == report_id


def test_post_eval_run_hallucinated_mock(aletheia_client: TestClient):
    payload = {
        "incident_id": "INC-001",
        "baseline": "single-llm",
        "mock_mode": "hallucinated",
    }
    resp = aletheia_client.post("/api/v1/eval/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_score"] == 0.0
    assert data["root_cause_score"]["passed"] is False
    assert data["hallucination_score"]["passed"] is False
    assert data["hallucination_score"]["details"]["count"] >= 1


def test_list_eval_reports(aletheia_client: TestClient):
    resp = aletheia_client.get("/api/v1/eval/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_nonexistent_report_returns_404(aletheia_client: TestClient):
    resp = aletheia_client.get("/api/v1/eval/reports/EVAL-NONEXISTENT")
    assert resp.status_code == 404


def test_post_eval_run_invalid_mock_mode_returns_400(aletheia_client: TestClient):
    payload = {
        "incident_id": "INC-001",
        "baseline": "single-llm",
        "mock_mode": "nonexistent_mode",
    }
    resp = aletheia_client.post("/api/v1/eval/run", json=payload)
    assert resp.status_code == 400
