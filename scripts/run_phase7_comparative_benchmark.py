"""Execute the full Phase 7 Comparative Evaluation benchmark across all 20 incidents.

Compares:
1. Baseline A: Single LLM
2. Baseline B: 2-Agent (Investigator + Analyst)
3. Aletheia: 3-Agent (Investigator -> Analyst -> Verifier)
"""

import json
from pathlib import Path

from aletheia.agents.orchestrator import AletheiaMultiAgentSystem
from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.baselines.two_agent import TwoAgentBaseline
from aletheia.evaluation.harness import EvaluationHarness


def main():
    harness = EvaluationHarness()
    all_incidents = [f"INC-{i:03d}" for i in range(1, 21)]

    systems = {
        "Baseline-A (Single-LLM)": SingleLLMBaseline(name="Baseline-A (Single-LLM)"),
        "Baseline-B (2-Agent)": TwoAgentBaseline(name="Baseline-B (2-Agent)"),
        "Aletheia (3-Agent)": AletheiaMultiAgentSystem(name="Aletheia (3-Agent)"),
    }

    print("========================================================================")
    print(f"STARTING PHASE 7 BENCHMARK: {len(all_incidents)} INCIDENTS x {len(systems)} SYSTEMS")
    print("========================================================================")

    report = harness.evaluate_comparative_benchmark(incident_ids=all_incidents, systems=systems)

    print("\n" + report.format_markdown_table())
    print("\n" + report.comparative_summary)

    # Save to eval_results
    eval_dir = Path(__file__).resolve().parent.parent / "eval_results"
    eval_dir.mkdir(parents=True, exist_ok=True)
    summary_path = eval_dir / "phase7_comparative_benchmark.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    print(f"\n[Saved benchmark results to {summary_path}]")


if __name__ == "__main__":
    main()
