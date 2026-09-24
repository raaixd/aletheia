"""Unit tests for the failure injection manager and ground truth schemas."""

import json
from pathlib import Path
import pytest

from aletheia.models.incident import IncidentGroundTruth
from simulator.failure_injection.manager import FailureInjectionManager


@pytest.fixture(autouse=True)
def clean_manager():
    """Ensure clean manager state for each test."""
    manager = FailureInjectionManager()
    manager.reset()
    yield manager
    manager.reset()


@pytest.mark.unit
def test_ground_truth_json_schema_validation():
    """Verify inc_001_ground_truth.json validates cleanly against IncidentGroundTruth schema."""
    ground_truth_path = Path("incidents/ground_truth/inc_001_ground_truth.json")
    assert ground_truth_path.exists(), "Ground truth file for INC-001 must exist"

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    gt = IncidentGroundTruth(**raw_data)
    assert gt.incident_id == "INC-001"
    assert gt.root_cause == "slow_database_query"
    assert gt.affected_service == "checkout-api"
    assert "increased_db_latency" in gt.expected_evidence
    assert gt.ground_truth_details["baseline_latency_ms"] == 5.0
    assert gt.ground_truth_details["regressed_latency_ms"] == 1500.0


@pytest.mark.unit
def test_failure_manager_inject_and_load_scenario_defaults(clean_manager):
    """Verify failure manager injects INC-001 and loads default parameters from scenario file."""
    record = clean_manager.inject("INC-001")
    assert clean_manager.is_active("INC-001")
    assert record["status"] == "ACTIVE"
    assert record["incident_id"] == "INC-001"

    # Default latency from scenario should be loaded
    params = clean_manager.get_parameters("INC-001")
    assert params.get("latency_ms") == 1500.0


@pytest.mark.unit
def test_failure_manager_parameter_override(clean_manager):
    """Verify runtime parameter overrides take precedence over scenario defaults."""
    clean_manager.inject("INC-001", {"latency_ms": 250.0, "custom_tag": "test-run"})
    params = clean_manager.get_parameters("INC-001")
    assert params["latency_ms"] == 250.0
    assert params["custom_tag"] == "test-run"


@pytest.mark.unit
def test_failure_manager_reset(clean_manager):
    """Verify resetting an individual incident and clearing all incidents."""
    clean_manager.inject("INC-001")
    clean_manager.inject("INC-002")
    assert len(clean_manager.get_all_active()) == 2

    # Reset single
    clean_manager.reset("INC-001")
    assert not clean_manager.is_active("INC-001")
    assert clean_manager.is_active("INC-002")

    # Reset all
    clean_manager.reset()
    assert len(clean_manager.get_all_active()) == 0
