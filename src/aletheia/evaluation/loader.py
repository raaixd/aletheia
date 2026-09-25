"""Telemetry and ground truth loaders with strict isolation guarantees."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from aletheia.evidence.events import Event, EventType, Timeline
from aletheia.evidence.schema import EvidenceItem
from aletheia.evidence.sources.local import LocalEvidenceSource
from aletheia.models.incident import IncidentGroundTruth


def get_ground_truth_path(incident_id: str) -> Path:
    """Resolve ground truth JSON file path."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    gt_dir = project_root / "incidents" / "ground_truth"

    candidate_names = [
        f"{incident_id.lower().replace('-', '_')}_ground_truth.json",
        f"{incident_id.lower()}_ground_truth.json",
        f"{incident_id}_ground_truth.json",
    ]

    for name in candidate_names:
        p = gt_dir / name
        if p.exists():
            return p

    raise FileNotFoundError(f"No ground truth specification found for incident '{incident_id}' in {gt_dir}")


def load_ground_truth(incident_id: str) -> IncidentGroundTruth:
    """Load isolated ground truth specification.

    CRITICAL RULE:
    This function must ONLY be called by the Evaluation Harness or test assertions.
    Diagnostic agents/baselines must NEVER call this or have access to ground truth.
    """
    path = get_ground_truth_path(incident_id)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return IncidentGroundTruth(**data)


def load_incident_telemetry(incident_id: str) -> Tuple[str, List[EvidenceItem], Timeline]:
    """Load observable telemetry and timeline for an incident without ground truth leakage.

    Returns:
        (alert_description, evidence_items, timeline)
    """
    from aletheia.evaluation.incident_telemetry import generate_telemetry_for_incident
    return generate_telemetry_for_incident(incident_id)

