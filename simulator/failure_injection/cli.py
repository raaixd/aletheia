"""CLI utility for injecting and resetting simulator failures."""

import argparse
import json
import sys
import httpx


def inject_failure(base_url: str, incident_id: str, latency_ms: float = None):
    """Call the simulator API to inject a failure."""
    params = {}
    if latency_ms is not None:
        params["latency_ms"] = latency_ms

    payload = {"incident_id": incident_id, "parameters": params}
    url = f"{base_url.rstrip('/')}/api/simulator/inject"
    try:
        res = httpx.post(url, json=payload, timeout=5.0)
        if res.status_code == 200:
            print(f"Successfully injected {incident_id}:")
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"Error ({res.status_code}): {res.text}", file=sys.stderr)
            sys.exit(1)
    except Exception as exc:
        print(f"Failed to connect to simulator service at {url}: {exc}", file=sys.stderr)
        sys.exit(1)


def reset_failure(base_url: str, incident_id: str = None):
    """Call the simulator API to reset active failures."""
    url = f"{base_url.rstrip('/')}/api/simulator/reset"
    params = {"incident_id": incident_id} if incident_id else {}
    try:
        res = httpx.post(url, params=params, timeout=5.0)
        if res.status_code == 200:
            print("Successfully reset failures:")
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"Error ({res.status_code}): {res.text}", file=sys.stderr)
            sys.exit(1)
    except Exception as exc:
        print(f"Failed to connect to simulator service at {url}: {exc}", file=sys.stderr)
        sys.exit(1)


def status_failures(base_url: str):
    """Query current failure injection status."""
    url = f"{base_url.rstrip('/')}/api/simulator/incidents"
    try:
        res = httpx.get(url, timeout=5.0)
        if res.status_code == 200:
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"Error ({res.status_code}): {res.text}", file=sys.stderr)
            sys.exit(1)
    except Exception as exc:
        print(f"Failed to connect to simulator service at {url}: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Aletheia Failure Injection Controller")
    parser.add_argument(
        "--target",
        default="http://localhost:8001",
        help="Target Checkout API URL (default: http://localhost:8001)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # inject command
    inject_parser = subparsers.add_parser("inject", help="Inject an incident failure")
    inject_parser.add_argument("incident_id", help="Incident ID to inject, e.g. INC-001")
    inject_parser.add_argument("--latency", type=float, default=None, help="Custom latency in milliseconds")

    # reset command
    reset_parser = subparsers.add_parser("reset", help="Reset active failures")
    reset_parser.add_argument("--incident_id", default=None, help="Specific incident ID to reset, or omit to reset all")

    # status command
    subparsers.add_parser("status", help="Get status of active failures")

    args = parser.parse_args()

    if args.command == "inject":
        inject_failure(args.target, args.incident_id, latency_ms=args.latency)
    elif args.command == "reset":
        reset_failure(args.target, incident_id=args.incident_id)
    elif args.command == "status":
        status_failures(args.target)


if __name__ == "__main__":
    main()
