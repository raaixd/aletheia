"""Integration tests for the Aletheia Platform API."""

import pytest


@pytest.mark.integration
def test_aletheia_health_endpoint(aletheia_client):
    """Verify Aletheia platform API health check."""
    response = aletheia_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Aletheia Investigation Platform"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
