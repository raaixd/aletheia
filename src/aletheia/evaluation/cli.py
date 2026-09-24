"""Command-line tool to run and inspect incident evaluations."""

import argparse
import json
import sys

from aletheia.evaluation.baselines.single_llm import SingleLLMBaseline
from aletheia.evaluation.harness import EvaluationHarness, get_evaluation_harness
from aletheia.evaluation.llm.client import MockLLMClient, MockMode, OpenAILLMClient


def main():
    parser = argparse.ArgumentParser(description="Aletheia Evaluation Harness & Baseline Benchmark")
    parser.add_argument(
        "--incident",
        type=str,
        default="INC-001",
        help="Incident ID to evaluate against (default: INC-001)",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="single-llm",
        choices=["single-llm"],
        help="Diagnostic baseline system to run (default: single-llm)",
    )
    parser.add_argument(
        "--mock",
        type=str,
        default="accurate",
        choices=["accurate", "hallucinated", "partial", "invalid_json"],
        help="Simulation mode for MockLLMClient (default: accurate)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real OpenAI-compatible endpoint with OPENAI_API_KEY instead of Mock",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model name (e.g. gpt-4o-mini)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print complete evaluation report in JSON format",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save report to eval_results directory",
    )

    args = parser.parse_args()

    # Configure client
    if args.live:
        client = OpenAILLMClient(model=args.model)
        system_name = f"Baseline-A-Single-LLM ({args.model or 'openai'})"
    else:
        mode = MockMode(args.mock)
        client = MockLLMClient(mode=mode, model_name=f"mock-{mode.value}")
        system_name = f"Baseline-A-Single-LLM (mock:{mode.value})"

    baseline_system = SingleLLMBaseline(name=system_name, llm_client=client)
    harness = get_evaluation_harness()

    try:
        report = harness.evaluate(baseline_system, incident_id=args.incident)
    except Exception as exc:
        print(f"Error executing evaluation: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.save:
        saved_path = harness.save_report(report)
        print(f"[Saved report to {saved_path}]")

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(report.format_ascii())


if __name__ == "__main__":
    main()
