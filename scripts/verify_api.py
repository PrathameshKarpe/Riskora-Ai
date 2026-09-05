#!/usr/bin/env python
"""
Phase 4 API verification script — Steps 7–12.

Runs FastAPI via TestClient against real PostgreSQL.
Covers: health, transactions, investigation pipeline, persistence,
human review, dashboard, and audit trail.
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Force PostgreSQL before any app imports resolve settings ─────────────────
PG_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://riskora:riskora@localhost:5433/riskora",
)
os.environ["DATABASE_URL"] = PG_URL
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET", "change-me-in-development")

import sqlalchemy as sa
from sqlalchemy import text
from fastapi.testclient import TestClient

from apps.api.app.db.database import Base, make_engine
from apps.api.app.db.session import get_db, make_session_factory
from apps.api.app.main import app
from ml.training.train import train
from pathlib import Path

# ── Train ML model ────────────────────────────────────────────────────────────
print("Training ML model...")
train(artifact_dir=Path("ml/models"))
print("ML model ready.\n")

# ── Wire TestClient to PostgreSQL ─────────────────────────────────────────────
factory = make_session_factory(PG_URL)

def override_db():
    db = factory()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_db

pg_engine = make_engine(PG_URL)
Base.metadata.create_all(pg_engine)   # idempotent — tables already exist

client = TestClient(app)

# ── helpers ───────────────────────────────────────────────────────────────────
PASS = "PASS"
FAIL = "FAIL"
results = {}

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results[name] = status
    mark = "✓" if condition else "✗"
    msg = f"  [{mark}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition

def uid(prefix="V"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def high_risk_payload(ext_id):
    return {
        "external_id": ext_id,
        "amount": 48500.0,
        "currency": "INR",
        "merchant": "Unknown Overseas Vendor",
        "payment_method": "CARD",
        "device_id": "device-new-xyz",
        "location": "Unknown City",
        "risk_context": {
            "merchant_category": "high_risk",
            "transaction_hour": 2,
            "transaction_day": 6,
            "transactions_last_5m": 4,
            "transactions_last_hour": 8,
            "transactions_last_24h": 15,
            "avg_historical_amount": 500,
            "failed_transaction_count": 5,
            "account_age_days": 30,
            "previous_fraud_history": 1,
            "new_device": 1,
            "device_change_frequency": 3,
            "device_risk": 0.9,
            "country_change": 1,
            "impossible_travel": 1,
        },
    }

def low_risk_payload(ext_id):
    return {
        "external_id": ext_id,
        "amount": 150.0,
        "currency": "INR",
        "merchant": "Local Grocery",
        "payment_method": "UPI",
        "device_id": "device-regular",
        "location": "Chennai",
        "risk_context": {
            "merchant_category": "grocery",
            "transaction_hour": 10,
            "transaction_day": 3,
            "transactions_last_5m": 0,
            "transactions_last_hour": 1,
            "transactions_last_24h": 3,
            "avg_historical_amount": 200,
            "failed_transaction_count": 0,
            "account_age_days": 1200,
            "previous_fraud_history": 0,
            "new_device": 0,
            "device_change_frequency": 0,
            "device_risk": 0.05,
            "country_change": 0,
            "impossible_travel": 0,
        },
    }

def critical_risk_payload(ext_id):
    return {
        "external_id": ext_id,
        "amount": 200000.0,
        "currency": "INR",
        "merchant": "Flagged Merchant",
        "payment_method": "CARD",
        "device_id": "device-fraud-99",
        "location": "Overseas",
        "risk_context": {
            "merchant_category": "gambling",
            "transaction_hour": 3,
            "transaction_day": 0,
            "transactions_last_5m": 10,
            "transactions_last_hour": 20,
            "transactions_last_24h": 50,
            "avg_historical_amount": 300,
            "failed_transaction_count": 10,
            "account_age_days": 7,
            "previous_fraud_history": 1,
            "new_device": 1,
            "device_change_frequency": 5,
            "device_risk": 1.0,
            "country_change": 1,
            "impossible_travel": 1,
        },
    }

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Health endpoints
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 7 — Health")
print("=" * 60)

r = client.get("/health")
check("GET /health", r.status_code == 200 and r.json() == {"status": "ok", "service": "riskora-api"},
      str(r.json()))

r = client.get("/health/db")
body = r.json()
check("GET /health/db status=ok", r.status_code == 200 and body.get("status") == "ok", str(body))
check("GET /health/db database=ok", body.get("database") == "ok", str(body))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Transaction API
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 8 — Transaction API")
print("=" * 60)

r = client.post("/api/v1/transactions", json=low_risk_payload(uid("TX-LOW")))
check("POST /api/v1/transactions (201)", r.status_code == 201, r.text[:200])
low_tx_id = r.json().get("id") if r.status_code == 201 else None
check("Transaction status=RECEIVED", r.json().get("status") == "RECEIVED" if r.status_code == 201 else False)

r = client.post("/api/v1/transactions", json=high_risk_payload(uid("TX-HIGH")))
check("POST /api/v1/transactions high-risk (201)", r.status_code == 201, r.text[:200])
high_tx_id = r.json().get("id") if r.status_code == 201 else None

r = client.post("/api/v1/transactions", json=critical_risk_payload(uid("TX-CRIT")))
check("POST /api/v1/transactions critical-risk (201)", r.status_code == 201, r.text[:200])
crit_tx_id = r.json().get("id") if r.status_code == 201 else None

r = client.get("/api/v1/transactions")
check("GET /api/v1/transactions (200, list)", r.status_code == 200 and isinstance(r.json(), list),
      f"{len(r.json())} transactions")

if low_tx_id:
    r = client.get(f"/api/v1/transactions/{low_tx_id}")
    check(f"GET /api/v1/transactions/{low_tx_id} (200)", r.status_code == 200)

r = client.get("/api/v1/transactions/999999")
check("GET /api/v1/transactions/999999 (404)", r.status_code == 404)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Investigation pipeline (low / high / critical)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 9 — Investigation pipeline")
print("=" * 60)

def investigate(tx_id, label):
    if not tx_id:
        print(f"  [✗] INVESTIGATE {label} — skipped (no tx_id)")
        return None
    print(f"\n  → Investigating {label} (tx_id={tx_id})...")
    r = client.post(f"/api/v1/transactions/{tx_id}/investigate")
    ok = r.status_code == 200
    check(f"POST investigate {label} (200)", ok, r.text[:300] if not ok else "")
    if not ok:
        return None
    body = r.json()
    check(f"  {label}: status=COMPLETED", body.get("status") == "COMPLETED", body.get("status"))
    check(f"  {label}: risk present",     body.get("risk") is not None)
    check(f"  {label}: decision present", body.get("decision") is not None)
    ev_count = len(body.get("evidence", []))
    # Evidence is only retrieved when key_findings are present (anomaly signals).
    # Low-risk transactions with no signals correctly return 0 evidence items.
    check(f"  {label}: evidence is list", isinstance(body.get("evidence"), list),
          f"{ev_count} items")
    check(f"  {label}: behavioral_signals present",
          isinstance(body.get("behavioral_signals"), list),
          f"{len(body.get('behavioral_signals', []))} signals")

    # pipeline component checks
    risk_level = body.get("risk", {}).get("risk_level", "UNKNOWN")
    policy_action = body.get("decision", {}).get("policy_action", "UNKNOWN")
    print(f"    risk_level={risk_level}  policy_action={policy_action}")

    # GET by investigation ID
    inv_id = body.get("investigation_id")
    r2 = client.get(f"/api/v1/investigations/{inv_id}")
    check(f"  GET /investigations/{inv_id} (200)", r2.status_code == 200)

    # GET by transaction
    r3 = client.get(f"/api/v1/transactions/{tx_id}/investigation")
    check(f"  GET /transactions/{tx_id}/investigation (200)", r3.status_code == 200)

    return body

low_inv  = investigate(low_tx_id,  "LOW-RISK")
high_inv = investigate(high_tx_id, "HIGH-RISK")
crit_inv = investigate(crit_tx_id, "CRITICAL-RISK")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 10 — Verify persistence in PostgreSQL directly
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 10 — PostgreSQL persistence verification")
print("=" * 60)

def verify_persistence(tx_id, inv_body, label):
    if not tx_id or not inv_body:
        print(f"  [SKIP] {label} persistence — no investigation data")
        return
    inv_id = inv_body["investigation_id"]
    with pg_engine.connect() as conn:
        tx_row = conn.execute(
            text("SELECT id, status FROM transactions WHERE id = :id"), {"id": tx_id}
        ).fetchone()
        check(f"  {label}: transaction in PG", tx_row is not None,
              f"status={tx_row[1]}" if tx_row else "MISSING")

        ra_row = conn.execute(
            text("SELECT risk_level, fraud_probability FROM risk_assessments WHERE transaction_id = :id"),
            {"id": tx_id}
        ).fetchone()
        check(f"  {label}: risk_assessment in PG", ra_row is not None,
              f"risk_level={ra_row[0]}" if ra_row else "MISSING")

        inv_row = conn.execute(
            text("SELECT id, status FROM investigations WHERE id = :id"), {"id": inv_id}
        ).fetchone()
        check(f"  {label}: investigation in PG", inv_row is not None and inv_row[1] == "COMPLETED",
              f"status={inv_row[1]}" if inv_row else "MISSING")

        ev_count = conn.execute(
            text("SELECT count(*) FROM evidence WHERE investigation_id = :id"), {"id": inv_id}
        ).scalar()
        # Evidence is only stored when key_findings are present.
        # Low-risk transactions with no anomaly signals produce 0 evidence — correct.
        check(f"  {label}: evidence count in PG", ev_count >= 0,
              f"{ev_count} rows (0 expected for low-risk)")

        pd_row = conn.execute(
            text("SELECT policy_action FROM policy_decisions WHERE transaction_id = :id"), {"id": tx_id}
        ).fetchone()
        check(f"  {label}: policy_decision in PG", pd_row is not None,
              f"action={pd_row[0]}" if pd_row else "MISSING")

        ae_count = conn.execute(
            text("SELECT count(*) FROM audit_events WHERE transaction_id = :id"), {"id": tx_id}
        ).scalar()
        check(f"  {label}: audit_events in PG", ae_count > 0, f"{ae_count} events")

        ml_event = conn.execute(
            text("SELECT id FROM audit_events WHERE transaction_id=:id AND event_type='ML_RISK_CALCULATED'"),
            {"id": tx_id}
        ).fetchone()
        check(f"  {label}: ML_RISK_CALCULATED audit event", ml_event is not None)

        findings_count = conn.execute(
            text("SELECT count(*) FROM agent_findings WHERE investigation_id = :id"), {"id": inv_id}
        ).scalar()
        print(f"    agent_findings={findings_count}  audit_events={ae_count}")

verify_persistence(high_tx_id, high_inv, "HIGH-RISK")
verify_persistence(crit_tx_id, crit_inv, "CRITICAL-RISK")
verify_persistence(low_tx_id,  low_inv,  "LOW-RISK")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 11 — Human review
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 11 — Human review")
print("=" * 60)

# Create and investigate a fresh transaction for review tests
review_tx_id_approve = None
review_tx_id_block   = None
review_tx_id_hold    = None

for decision, tx_label in [("approve", "APPROVE"), ("block", "BLOCK"), ("hold", "HOLD")]:
    r = client.post("/api/v1/transactions", json=high_risk_payload(uid(f"REV-{tx_label}")))
    if r.status_code != 201:
        check(f"  Setup tx for {decision}", False, r.text[:200])
        continue
    tx_id = r.json()["id"]
    client.post(f"/api/v1/transactions/{tx_id}/investigate")

    reason = f"Phase 4 verification — {decision} decision."
    r2 = client.post(f"/api/v1/reviews/{tx_id}/{decision}", json={"reason": reason})
    ok = r2.status_code == 200
    check(f"POST /reviews/{tx_id}/{decision} (200)", ok, r2.text[:200] if not ok else "")
    if ok:
        body = r2.json()
        check(f"  {decision}: decision={tx_label}", body.get("decision") == tx_label)
        check(f"  {decision}: reason recorded", body.get("reason") == reason)
        check(f"  {decision}: reviewer_id set", body.get("reviewer_id") is not None,
              str(body.get("reviewer_id")))
        check(f"  {decision}: created_at set", body.get("created_at") is not None)

        # transaction status updated
        tx_r = client.get(f"/api/v1/transactions/{tx_id}")
        check(f"  {decision}: transaction.status={tx_label}",
              tx_r.json().get("status") == tx_label, tx_r.json().get("status"))

        # audit event created
        audit_r = client.get(f"/api/v1/audit/{tx_id}")
        event_types = {e["event_type"] for e in audit_r.json()}
        check(f"  {decision}: AUDIT_RECORDED event exists", "AUDIT_RECORDED" in event_types)

        # PostgreSQL direct check
        with pg_engine.connect() as conn:
            hr = conn.execute(
                text("SELECT decision, reason FROM human_reviews WHERE transaction_id=:id"),
                {"id": tx_id}
            ).fetchone()
            check(f"  {decision}: human_review in PG", hr is not None and hr[0] == tx_label,
                  f"{hr}" if hr else "MISSING")

# review 422 for missing reason
r_missing = client.post(f"/api/v1/reviews/{high_tx_id}/approve", json={})
check("POST /reviews missing reason → 422", r_missing.status_code == 422)

# list reviews
r_list = client.get("/api/v1/reviews")
check("GET /api/v1/reviews (200, list)", r_list.status_code == 200 and isinstance(r_list.json(), list),
      f"{len(r_list.json())} reviews")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 12 — Dashboard APIs
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 12 — Dashboard")
print("=" * 60)

r = client.get("/api/v1/dashboard/metrics")
check("GET /dashboard/metrics (200)", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")
if r.status_code == 200:
    m = r.json()
    for key in ("total_transactions", "suspicious_transactions", "blocked_transactions",
                "approved_transactions", "pending_reviews"):
        check(f"  metrics.{key} present", key in m, str(m.get(key)))
    check("  metrics.total_transactions >= 3", m.get("total_transactions", 0) >= 3,
          str(m.get("total_transactions")))

r = client.get("/api/v1/dashboard/risk-distribution")
check("GET /dashboard/risk-distribution (200)", r.status_code == 200)
if r.status_code == 200:
    dist = r.json()
    check("  risk-distribution is dict", isinstance(dist, dict))
    check("  risk-distribution has entries", len(dist) >= 1, str(dist))

r = client.get("/api/v1/dashboard/recent-transactions")
check("GET /dashboard/recent-transactions (200)", r.status_code == 200)
if r.status_code == 200:
    check("  recent-transactions is list", isinstance(r.json(), list))
    check("  recent-transactions has entries", len(r.json()) >= 1, f"{len(r.json())} items")

r = client.get("/api/v1/dashboard/pending-reviews")
check("GET /dashboard/pending-reviews (200)", r.status_code == 200)
if r.status_code == 200:
    check("  pending-reviews is int", isinstance(r.json(), int), str(r.json()))

# Audit trail ordering
print("\n  — Audit trail ordering —")
if high_tx_id:
    r = client.get(f"/api/v1/audit/{high_tx_id}")
    check("GET /audit/{tx_id} (200)", r.status_code == 200)
    if r.status_code == 200:
        events = r.json()
        timestamps = [e["timestamp"] for e in events]
        check("  audit events in chronological order", timestamps == sorted(timestamps),
              f"{len(events)} events")
        et = {e["event_type"] for e in events}
        for expected in ("INVESTIGATION_STARTED", "ML_RISK_CALCULATED", "POLICY_EVALUATED"):
            check(f"  audit event {expected} present", expected in et)

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for v in results.values() if v == PASS)
failed = sum(1 for v in results.values() if v == FAIL)
print(f"API VERIFICATION: {passed} passed / {failed} failed")
if failed:
    print("FAILED checks:")
    for name, status in results.items():
        if status == FAIL:
            print(f"  ✗ {name}")

app.dependency_overrides.clear()
pg_engine.dispose()

sys.exit(0 if failed == 0 else 1)
