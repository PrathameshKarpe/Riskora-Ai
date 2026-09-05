"""Verify the Phase 5 auth + role flow through the Next.js proxy (port 3000).

Read-only checks plus clearly-labeled test actions on demo data.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://localhost:3000"


def post(path: str, payload: dict | None, token: str | None = None):
    body = json.dumps(payload).encode() if payload is not None else b""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", data=body, method="POST", headers=headers)
    try:
        res = urllib.request.urlopen(req)
        return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def get(path: str, token: str | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    try:
        res = urllib.request.urlopen(req)
        return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main() -> None:
    results: list[tuple[str, str]] = []

    # 1. Login for all three roles
    tokens: dict[str, str] = {}
    for email, expected_role in [
        ("admin@riskora.local", "ADMIN"),
        ("analyst@riskora.local", "RISK_ANALYST"),
        ("reviewer@riskora.local", "REVIEWER"),
    ]:
        status, data = post("/api/v1/auth/login", {"email": email})
        ok = status == 200 and isinstance(data, dict) and data.get("role") == expected_role and "access_token" in data
        results.append((f"login {email}", "PASS" if ok else f"FAIL {status} {data}"))
        if ok:
            tokens[email] = data["access_token"]

    # 2. Invalid login (empty email) -> 422 validation error
    status, data = post("/api/v1/auth/login", {"email": ""})
    results.append(("invalid login (empty email) -> 422", "PASS" if status == 422 else f"FAIL {status} {data}"))

    # 3. Invalid token -> 401
    status, data = get("/api/v1/reviews", token="invalid.token.here")
    results.append(("invalid token -> 401", "PASS" if status == 401 else f"FAIL {status} {data}"))

    # 4. RISK_ANALYST cannot approve (403) — backend authorization authoritative
    analyst = tokens.get("analyst@riskora.local")
    status, data = post("/api/v1/reviews/3/approve", {"reason": "role test"}, token=analyst)
    results.append(("RISK_ANALYST approve -> 403", "PASS" if status == 403 else f"FAIL {status} {data}"))

    # 5. REVIEWER can approve (200) — transaction 3 (DEMO-CRITICAL, RECEIVED)
    reviewer = tokens.get("reviewer@riskora.local")
    status, data = post("/api/v1/reviews/3/approve", {"reason": "Verified legitimate corporate transfer"}, token=reviewer)
    ok = status == 200 and isinstance(data, dict) and data.get("decision") == "APPROVE"
    results.append(("REVIEWER approve -> 200 APPROVE", "PASS" if ok else f"FAIL {status} {data}"))

    # 6. Transaction 3 status updated to APPROVE
    status, data = get("/api/v1/transactions/3", token=reviewer)
    ok = status == 200 and isinstance(data, dict) and data.get("status") == "APPROVE"
    results.append(("transaction 3 status == APPROVE", "PASS" if ok else f"FAIL {status} {data}"))

    # 7. Audit trail includes the reviewer decision
    status, data = get("/api/v1/audit/3", token=reviewer)
    types = [e.get("event_type") for e in data] if isinstance(data, list) else []
    ok = status == 200 and "REVIEWER_DECISION" in types and "FINAL_ACTION" in types
    results.append(("audit trail has REVIEWER_DECISION + FINAL_ACTION", "PASS" if ok else f"FAIL {status} {types}"))

    # 8. Transaction not found -> 404
    status, data = get("/api/v1/transactions/9999", token=reviewer)
    results.append(("transaction 9999 -> 404", "PASS" if status == 404 else f"FAIL {status} {data}"))

    # 9. Dashboard metrics + risk distribution
    status, metrics = get("/api/v1/dashboard/metrics", token=reviewer)
    ok = status == 200 and isinstance(metrics, dict) and "total_transactions" in metrics
    results.append(("dashboard metrics", "PASS" if ok else f"FAIL {status} {metrics}"))
    status, dist = get("/api/v1/dashboard/risk-distribution", token=reviewer)
    ok = status == 200 and isinstance(dist, dict)
    results.append(("risk distribution", "PASS" if ok else f"FAIL {status} {dist}"))

    # 10. Pending reviews list
    status, reviews = get("/api/v1/reviews", token=reviewer)
    ok = status == 200 and isinstance(reviews, list)
    results.append(("reviews list", "PASS" if ok else f"FAIL {status} {reviews}"))

    print("\n=== AUTH FLOW VERIFICATION ===")
    failures = 0
    for name, result in results:
        print(f"{result:5}  {name}")
        if result != "PASS":
            failures += 1
    print(f"\n{len(results) - failures}/{len(results)} checks passed")


if __name__ == "__main__":
    main()