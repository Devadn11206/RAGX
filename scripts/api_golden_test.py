"""
RAGX API-Level Golden Test Validation Script
Run from: c:\\Users\\ddnan\\RAGX
Usage: python scripts/api_golden_test.py
"""
import io
import sys
# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import os
import requests
import json
import time
from datetime import timedelta

# Ensure RAGX root is on path (for local JWT generation)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.security.jwt import create_access_token  # noqa: E402

BASE_URL = "http://localhost:8000"

GOLDEN_TESTS = [
    {
        "id": "TC-API-01",
        "query": "What are the standard working hours?",
        "expected_facts": ["9:00 AM", "6:00 PM"],
        "expected_source": "company_policy.txt",
    },
    {
        "id": "TC-API-02",
        "query": "What is the company leave policy?",
        "expected_facts": ["24 days"],
        "expected_source": "leave_policy.txt",
    },
    {
        "id": "TC-API-03",
        "query": "What is the maximum upload size for a file?",
        "expected_facts": ["50 MB"],
        "expected_source": "technical_limits.txt",
    },
]


def get_auth_headers() -> dict:
    """Generate a short-lived JWT for alice/tenant_a."""
    token = create_access_token(
        {"sub": "alice", "tenant_id": "tenant_a", "roles": ["employee", "admin"]},
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def run_tests() -> None:
    print("=" * 60)
    print("RAGX API GOLDEN TEST SUITE")
    print("=" * 60)

    # Verify server is up
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Server health: {health.status_code} {health.json().get('status', '')}")
    except Exception as exc:
        print(f"ERROR: Cannot reach API server at {BASE_URL} — {exc}")
        sys.exit(1)

    headers = get_auth_headers()
    results = []

    for tc in GOLDEN_TESTS:
        print(f"\n--- {tc['id']}: {tc['query']} ---")
        t0 = time.time()
        try:
            resp = requests.post(
                f"{BASE_URL}/api/v1/query",
                headers=headers,
                json={"query": tc["query"], "mode": "hybrid", "top_k": 5},
                timeout=120,
            )
            latency_ms = (time.time() - t0) * 1000

            if resp.status_code != 200:
                print(f"  FAIL: HTTP {resp.status_code} — {resp.text[:300]}")
                results.append({"id": tc["id"], "pass": False, "error": f"HTTP {resp.status_code}"})
                continue

            data = resp.json()
            answer: str = data.get("answer", "")
            sources: list[str] = [s.get("filename", "") for s in data.get("sources", [])]

            facts_matched = [f for f in tc["expected_facts"] if f.lower() in answer.lower()]
            answer_ok = len(facts_matched) == len(tc["expected_facts"])
            citation_ok = any(tc["expected_source"] in s for s in sources)

            print(f"  Answer   : {answer[:160]}")
            print(f"  Sources  : {sources}")
            print(f"  Latency  : {latency_ms:.0f} ms")
            print(f"  Facts    : {facts_matched} / {tc['expected_facts']} -> {'PASS' if answer_ok else 'FAIL'}")
            print(f"  Citation : {'PASS' if citation_ok else 'WARN (source not in top results)'}")

            results.append({
                "id": tc["id"],
                "pass": answer_ok,
                "citation_ok": citation_ok,
                "latency_ms": round(latency_ms, 0),
            })

        except Exception as exc:
            print(f"  Exception: {exc}")
            results.append({"id": tc["id"], "pass": False, "error": str(exc)})

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_pass = all(r["pass"] for r in results)
    for r in results:
        status = "[PASS]" if r["pass"] else "[FAIL]"
        extra = f"  (error: {r['error']})" if "error" in r else f"  {r.get('latency_ms', '?')} ms"
        print(f"  {r['id']} {status}{extra}")

    print(f"\nFINAL: {'ALL PASSED' if all_pass else 'SOME FAILED'}")

    # Persist results
    os.makedirs("reports/evaluation", exist_ok=True)
    out_path = "reports/evaluation/api_golden_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "all_pass": all_pass}, f, indent=2)
    print(f"Results saved to: {out_path}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    run_tests()
