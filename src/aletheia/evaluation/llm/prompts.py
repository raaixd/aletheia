"""Prompt builder and templates for the Single-LLM Baseline (Baseline A)."""

import json
from typing import List, Optional

from aletheia.evidence.events import Timeline
from aletheia.evidence.schema import EvidenceItem


class BaselinePromptBuilder:
    """Builds structured investigation prompts for single-LLM incident diagnosis."""

    SYSTEM_PROMPT = """You are Aletheia-Baseline, an expert site reliability and root-cause analysis AI.
You are tasked with diagnosing a production software incident based EXCLUSIVELY on observable telemetry.

CRITICAL RULES:
1. Ground every conclusion strictly in the provided evidence items and timeline.
2. Only cite Evidence IDs (e.g. EV-DEP-0001, EV-SPAN-0001) that explicitly exist in the evidence catalog below.
3. NEVER invent, hallucinate, or fabricate evidence IDs or system events.
4. If a fact cannot be proven from the evidence, state that it is unknown.
5. You must respond ONLY with a valid JSON object matching the requested schema. No conversational markdown outside the JSON."""

    SCHEMA_INSTRUCTIONS = """
Your response must be a single valid JSON object formatted exactly as:
{
  "incident_id": "<string>",
  "root_cause": "<concise summary of verified root cause>",
  "root_cause_category": "slow_database_query | memory_leak | network_failure | config_error | deployment_bug | unknown",
  "suspected_component": "<database/subsystem/service component at fault>",
  "introduced_by": "<commit SHA or deployment version that introduced the change, or 'unknown'>",
  "affected_service": "<primary affected service>",
  "explanation": "<step-by-step causal explanation connecting deployment/commit -> telemetry -> impact>",
  "cited_evidence_ids": ["<ID_1>", "<ID_2>", ...],
  "confidence": <float between 0.0 and 1.0>,
  "recommended_fix": "<concrete rollback or code fix recommendation>"
}"""

    @classmethod
    def build_user_prompt(
        cls,
        incident_id: str,
        alert_description: str,
        evidence_items: List[EvidenceItem],
        timeline: Optional[Timeline] = None,
    ) -> str:
        """Construct the unified investigation prompt dumping all available telemetry."""
        sections = []

        # 1. Incident Alert
        sections.append("=== 1. INCIDENT ALERT & REPORT ===")
        sections.append(f"Incident Identifier: {incident_id}")
        sections.append(f"Alert Details      : {alert_description}")

        # 2. Chronological Timeline
        if timeline and timeline.get_events():
            sections.append("\n=== 2. OBSERVED CHRONOLOGICAL TIMELINE ===")
            sections.append(timeline.format_ascii())

        # 3. Available Evidence Catalog
        sections.append(f"\n=== 3. AVAILABLE EVIDENCE CATALOG ({len(evidence_items)} Items) ===")
        sections.append("Examine each item carefully and cite relevant IDs:")

        for item in sorted(evidence_items, key=lambda x: x.timestamp):
            data_preview = json.dumps(item.data, default=str) if item.data else "{}"
            sections.append(
                f"- [{item.evidence_id}] [{item.type.value}] ({item.timestamp.isoformat()}) "
                f"Service: {item.service} | Content: {item.content} | Data: {data_preview}"
            )

        # 4. Instructions
        sections.append("\n=== 4. INVESTIGATION TASK ===")
        sections.append("Analyze the telemetry above to determine:")
        sections.append("1. What is the verified root cause?")
        sections.append("2. What commit, release, or action introduced this failure?")
        sections.append("3. Which specific evidence items (by ID) prove this diagnosis?")
        sections.append("4. How should the incident be resolved?")
        sections.append(cls.SCHEMA_INSTRUCTIONS)

        return "\n".join(sections)
