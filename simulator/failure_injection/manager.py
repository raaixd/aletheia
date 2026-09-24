"""Failure injection manager coordinating reproducible simulated incidents."""

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("simulator.failure_injection")


class FailureInjectionManager:
    """Thread-safe manager for injecting, inspecting, and resetting simulated failures."""

    def __init__(self, scenarios_dir: Optional[str] = None):
        self._lock = threading.Lock()
        self._active_incidents: Dict[str, Dict[str, Any]] = {}

        # Resolve scenarios directory
        if scenarios_dir:
            self._scenarios_dir = Path(scenarios_dir)
        else:
            # Default to root/incidents/scenarios
            current_file = Path(__file__).resolve()
            # current_file is simulator/failure_injection/manager.py
            # root is 3 levels up: current_file.parents[2]
            self._scenarios_dir = current_file.parents[2] / "incidents" / "scenarios"

    def _load_scenario_defaults(self, incident_id: str) -> Dict[str, Any]:
        """Attempt to read default parameters from the scenarios directory."""
        if not self._scenarios_dir.exists():
            return {}

        # Map INC-001 -> inc_001*.json
        normalized_id = incident_id.lower().replace("-", "_")
        for file in self._scenarios_dir.glob("*.json"):
            if normalized_id in file.name.lower():
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data.get("default_parameters", {})
                except Exception as exc:
                    logger.warning(f"Failed to load scenario file {file}: {exc}")
        return {}

    def inject(self, incident_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Activate an incident with default or customized parameters."""
        incident_id = incident_id.upper().strip()
        merged_params = self._load_scenario_defaults(incident_id)
        if parameters:
            merged_params.update(parameters)

        record = {
            "incident_id": incident_id,
            "status": "ACTIVE",
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "parameters": merged_params,
        }

        with self._lock:
            self._active_incidents[incident_id] = record

        logger.warning(
            f"INJECTED FAILURE: {incident_id} activated with parameters: {merged_params}"
        )
        return record

    def reset(self, incident_id: Optional[str] = None) -> Dict[str, Any]:
        """Reset a specific incident or clear all active incidents."""
        with self._lock:
            if incident_id:
                incident_id = incident_id.upper().strip()
                removed = self._active_incidents.pop(incident_id, None)
                count = 1 if removed else 0
                logger.info(f"RESET FAILURE: {incident_id} cleared.")
            else:
                count = len(self._active_incidents)
                self._active_incidents.clear()
                logger.info("RESET FAILURE: All active incidents cleared.")

        return {"reset_count": count, "remaining_active": len(self._active_incidents)}

    def is_active(self, incident_id: str) -> bool:
        """Check whether a specific incident is currently active."""
        incident_id = incident_id.upper().strip()
        with self._lock:
            return incident_id in self._active_incidents

    def get_parameters(self, incident_id: str) -> Dict[str, Any]:
        """Retrieve runtime parameters for an active incident."""
        incident_id = incident_id.upper().strip()
        with self._lock:
            record = self._active_incidents.get(incident_id)
            return record.get("parameters", {}) if record else {}

    def get_all_active(self) -> Dict[str, Dict[str, Any]]:
        """Return a snapshot of all currently active incidents."""
        with self._lock:
            return {k: dict(v) for k, v in self._active_incidents.items()}


# Global singleton instance for the simulator process
failure_manager = FailureInjectionManager()
