import json
import urllib.request

def test_integration():
    print("Testing Backend direct /health...")
    with urllib.request.urlopen("http://127.0.0.1:8000/health") as res:
        health = json.loads(res.read().decode())
        print(f"  Health response: {health}")
        assert health.get("status") == "healthy"

    print("Testing Backend direct /api/v1/investigation/incidents...")
    with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/investigation/incidents") as res:
        incidents = json.loads(res.read().decode())
        print(f"  Loaded {len(incidents)} incidents from backend.")
        assert len(incidents) >= 20

    print("Testing Next.js proxy /api/backend/api/v1/investigation/incidents...")
    with urllib.request.urlopen("http://127.0.0.1:3000/api/backend/api/v1/investigation/incidents") as res:
        incidents_proxy = json.loads(res.read().decode())
        print(f"  Proxy loaded {len(incidents_proxy)} incidents successfully.")
        assert len(incidents_proxy) == len(incidents)

    print("Testing Next.js proxy POST /api/backend/api/v1/investigation/diagnose/INC-001...")
    req = urllib.request.Request(
        "http://127.0.0.1:3000/api/backend/api/v1/investigation/diagnose/INC-001?system=aletheia-3agent",
        method="POST"
    )
    with urllib.request.urlopen(req) as res:
        diag_res = json.loads(res.read().decode())
        print("  Diagnose response received:")
        print(f"    Root Cause: {diag_res['diagnosis']['root_cause']}")
        print(f"    Confidence: {diag_res['diagnosis']['confidence']}")
        print(f"    Cited Evidence: {diag_res['diagnosis']['cited_evidence_ids']}")
        print(f"    Timeline Events: {len(diag_res.get('timeline_events', []))}")
        print(f"    Hypotheses Count: {len(diag_res['agent_steps']['analyst']['hypotheses'])}")
        print(f"    Challenges Count: {len(diag_res['agent_steps']['verifier']['challenges'])}")
        assert diag_res["diagnosis"]["incident_id"] == "INC-001"
        assert len(diag_res["agent_steps"]["verifier"]["challenges"]) > 0

    print("Testing Next.js frontend root HTML...")
    with urllib.request.urlopen("http://127.0.0.1:3000/") as res:
        html = res.read().decode()
        print(f"  HTML length: {len(html)} bytes")
        assert "Aletheia" in html
        print("  Aletheia root HTML validated.")

    print("\nALL FRONTEND-BACKEND INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_integration()
