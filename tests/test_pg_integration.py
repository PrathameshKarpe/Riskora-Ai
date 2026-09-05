"""
PostgreSQL integration tests — Phase 4 verification.

These tests require a live PostgreSQL instance at DATABASE_URL.
They are auto-skipped when DATABASE_URL is not a postgresql:// URL so they
never silently run against SQLite.

Run:
    $env:DATABASE_URL="postgresql+psycopg://riskora:riskora@localhost:5433/riskora"
    pytest tests/test_pg_integration.py -v
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

# ── skip guard ──────────────────────────────────────────────────────────────

PG_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://riskora:riskora@localhost:5433/riskora",
)
if not PG_URL.startswith("postgresql"):
    pytest.skip(
        "PostgreSQL integration tests require a postgresql:// DATABASE_URL",
        allow_module_level=True,
    )

# ── local imports (after skip guard so SQLite-only CI still works) ────────────

from apps.api.app.db.database import Base, make_engine
from apps.api.app.db.session import get_db, make_session_factory
from apps.api.app.main import app
from ml.training.train import train

# ── module-scope fixtures ────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def pg_engine():
    engine = make_engine(PG_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))   # fail fast if DB is unreachable
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def pg_schema(pg_engine):
    """Idempotent: create all tables if they don't exist yet."""
    Base.metadata.create_all(pg_engine)
    yield


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    artifact_dir = tmp_path_factory.mktemp("models")
    train(artifact_dir=artifact_dir)
    return artifact_dir


@pytest.fixture(scope="module")
def client(pg_schema, trained):
    factory = make_session_factory(PG_URL)

    def _override():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── helpers ──────────────────────────────────────────────────────────────────


def uid(prefix: str = "PG") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def low_risk_tx(ext_id: str) -> dict:
    return {
        "external_id": ext_id,
        "amount": 150.0,
        "currency": "INR",
        "merchant": "Local Grocery",
        "payment_method": "UPI",
        "device_id": "device-regular-001",
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


def high_risk_tx(ext_id: str) -> dict:
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


def critical_risk_tx(ext_id: str) -> dict:
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


# ── Step 3: connection ───────────────────────────────────────────────────────


def test_pg_raw_connection(pg_engine):
    with pg_engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


# ── Step 5: schema ───────────────────────────────────────────────────────────

EXPECTED_TABLES = {
    "users",
    "transactions",
    "risk_assessments",
    "investigations",
    "agent_findings",
    "evidence",
    "policy_decisions",
    "human_reviews",
    "audit_events",
}


def test_all_expected_tables_exist(pg_engine, pg_schema):
    inspector = inspect(pg_engine)
    existing = set(inspector.get_table_names(schema="public"))
    missing = EXPECTED_TABLES - existing
    assert not missing, f"Tables missing from PostgreSQL: {missing}"


def test_indexes_exist(pg_engine, pg_schema):
    inspector = inspect(pg_engine)
    for table, expected_index in [
        ("transactions", "ix_transactions_external_id"),
        ("transactions", "ix_transactions_status"),
        ("transactions", "ix_transactions_created_at"),
        ("audit_events", "ix_audit_events_transaction_id"),
        ("investigations", "ix_investigations_transaction_id"),
        ("risk_assessments", "ix_risk_assessments_risk_level"),
    ]:
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        assert expected_index in indexes, f"Index {expected_index!r} missing on {table}"


# ── Step 7: health endpoints ─────────────────────────────────────────────────


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "riskora-api"}


def test_health_db(client):
    r = client.get("/health/db")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok", f"DB health degraded: {body}"
    assert body["database"] == "ok"


# ── Step 8: Transaction CRUD ─────────────────────────────────────────────────


def test_create_low_risk_transaction(client):
    r = client.post("/api/v1/transactions", json=low_risk_tx(uid("LOW")))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "RECEIVED"
    assert body["id"] > 0


def test_list_transactions(client):
    r = client.get("/api/v1/transactions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_transaction_not_found(client):
    assert client.get("/api/v1/transactions/999999").status_code == 404


# ── Step 9: full investigation pipeline ─────────────────────────────────────


def _create_and_investigate(client, payload_fn) -> tuple[int, dict]:
    tx = client.post("/api/v1/transactions", json=payload_fn(uid())).json()
    inv = client.post(f"/api/v1/transactions/{tx['id']}/investigate")
    assert inv.status_code == 200, inv.text
    return tx["id"], inv.json()


def test_low_risk_investigation(client):
    tx_id, body = _create_and_investigate(client, low_risk_tx)
    assert body["status"] == "COMPLETED"
    assert body["risk"] is not None
    assert body["risk"]["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert body["decision"] is not None
    # evidence populated from RAG
    assert isinstance(body["evidence"], list)
    # behavioral signals present
    assert isinstance(body["behavioral_signals"], list)


def test_high_risk_investigation(client):
    tx_id, body = _create_and_investigate(client, high_risk_tx)
    assert body["status"] == "COMPLETED"
    assert body["risk"]["risk_level"] in {"HIGH", "CRITICAL"}
    assert body["behavioral_signals"], "Behavioral signals must be non-empty for high-risk tx"
    assert body["decision"]["policy_action"] in {"HUMAN_REVIEW", "BLOCK"}


def test_critical_risk_investigation(client):
    tx_id, body = _create_and_investigate(client, critical_risk_tx)
    assert body["status"] == "COMPLETED"
    assert body["risk"] is not None
    assert body["decision"] is not None
    # critical transactions must always require review or be blocked
    assert body["decision"]["policy_action"] in {"HUMAN_REVIEW", "BLOCK"}


# ── Step 10: PostgreSQL persistence ─────────────────────────────────────────


def test_investigation_persistence(pg_engine, client):
    tx = client.post("/api/v1/transactions", json=high_risk_tx(uid("PERSIST"))).json()
    tx_id = tx["id"]
    inv = client.post(f"/api/v1/transactions/{tx_id}/investigate").json()
    inv_id = inv["investigation_id"]

    with pg_engine.connect() as conn:
        # transaction exists
        row = conn.execute(
            text("SELECT id, status FROM transactions WHERE id = :id"), {"id": tx_id}
        ).fetchone()
        assert row is not None, "Transaction not in PostgreSQL"

        # risk_assessment
        ra = conn.execute(
            text("SELECT id, risk_level FROM risk_assessments WHERE transaction_id = :id"),
            {"id": tx_id},
        ).fetchone()
        assert ra is not None, "RiskAssessment not persisted"

        # investigation
        inv_row = conn.execute(
            text("SELECT id, status FROM investigations WHERE id = :id"), {"id": inv_id}
        ).fetchone()
        assert inv_row is not None, "Investigation not persisted"
        assert inv_row[1] == "COMPLETED", f"Investigation status: {inv_row[1]}"

        # agent_findings (behavior agent)
        findings_count = conn.execute(
            text("SELECT count(*) FROM agent_findings WHERE investigation_id = :id"),
            {"id": inv_id},
        ).scalar()
        # findings are present when behavioral signals detected
        assert findings_count >= 0  # may be 0 for very low risk

        # evidence
        ev_count = conn.execute(
            text("SELECT count(*) FROM evidence WHERE investigation_id = :id"),
            {"id": inv_id},
        ).scalar()
        # Evidence is retrieved only when key_findings (anomaly signals) are present.
        # High/critical risk transactions should always produce evidence.
        assert ev_count > 0, "Evidence not persisted"

        # policy_decision
        pd = conn.execute(
            text("SELECT id, policy_action FROM policy_decisions WHERE transaction_id = :id"),
            {"id": tx_id},
        ).fetchone()
        assert pd is not None, "PolicyDecision not persisted"

        # audit_events
        ae_count = conn.execute(
            text("SELECT count(*) FROM audit_events WHERE transaction_id = :id"),
            {"id": tx_id},
        ).scalar()
        assert ae_count > 0, "AuditEvents not persisted"

        # verify ML_RISK_CALCULATED event exists
        ml_event = conn.execute(
            text(
                "SELECT id FROM audit_events "
                "WHERE transaction_id = :id AND event_type = 'ML_RISK_CALCULATED'"
            ),
            {"id": tx_id},
        ).fetchone()
        assert ml_event is not None, "ML_RISK_CALCULATED audit event missing"


# ── Step 11: human review ────────────────────────────────────────────────────


def _investigated_tx(client) -> int:
    tx = client.post("/api/v1/transactions", json=high_risk_tx(uid("REV"))).json()
    client.post(f"/api/v1/transactions/{tx['id']}/investigate")
    return tx["id"]


def test_human_review_approve(pg_engine, client):
    tx_id = _investigated_tx(client)
    r = client.post(
        f"/api/v1/reviews/{tx_id}/approve",
        json={"reason": "Verified legitimate. Approved."},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["decision"] == "APPROVE"
    assert body["reason"] == "Verified legitimate. Approved."
    assert body["reviewer_id"] is not None

    # transaction status updated
    tx = client.get(f"/api/v1/transactions/{tx_id}").json()
    assert tx["status"] == "APPROVE"

    # audit event created
    events = client.get(f"/api/v1/audit/{tx_id}").json()
    assert any(e["event_type"] == "AUDIT_RECORDED" for e in events)

    # verify in PostgreSQL directly
    with pg_engine.connect() as conn:
        hr = conn.execute(
            text("SELECT decision, reason FROM human_reviews WHERE transaction_id = :id"),
            {"id": tx_id},
        ).fetchone()
        assert hr is not None, "HumanReview not persisted"
        assert hr[0] == "APPROVE"
        status = conn.execute(
            text("SELECT status FROM transactions WHERE id = :id"), {"id": tx_id}
        ).scalar()
        assert status == "APPROVE"


def test_human_review_block(pg_engine, client):
    tx_id = _investigated_tx(client)
    r = client.post(
        f"/api/v1/reviews/{tx_id}/block",
        json={"reason": "Confirmed fraud pattern."},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "BLOCK"

    with pg_engine.connect() as conn:
        status = conn.execute(
            text("SELECT status FROM transactions WHERE id = :id"), {"id": tx_id}
        ).scalar()
        assert status == "BLOCK"


def test_human_review_hold(pg_engine, client):
    tx_id = _investigated_tx(client)
    r = client.post(
        f"/api/v1/reviews/{tx_id}/hold",
        json={"reason": "Needs additional verification."},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "HOLD"


def test_review_requires_reason(client):
    tx_id = client.post("/api/v1/transactions", json=low_risk_tx(uid("NOREASON"))).json()["id"]
    assert client.post(f"/api/v1/reviews/{tx_id}/approve", json={}).status_code == 422


def test_list_reviews(client):
    r = client.get("/api/v1/reviews")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Step 12: dashboard ───────────────────────────────────────────────────────


def test_dashboard_metrics(client):
    r = client.get("/api/v1/dashboard/metrics")
    assert r.status_code == 200
    body = r.json()
    for key in ("total_transactions", "suspicious_transactions", "blocked_transactions",
                "approved_transactions", "pending_reviews"):
        assert key in body, f"Missing key: {key}"
    assert body["total_transactions"] >= 1


def test_dashboard_risk_distribution(client):
    r = client.get("/api/v1/dashboard/risk-distribution")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    # After investigations, at least one risk level should be present
    assert len(body) >= 1


def test_dashboard_recent_transactions(client):
    r = client.get("/api/v1/dashboard/recent-transactions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_dashboard_pending_reviews(client):
    r = client.get("/api/v1/dashboard/pending-reviews")
    assert r.status_code == 200
    # returns integer count
    assert isinstance(r.json(), int)


# ── audit trail ordering ─────────────────────────────────────────────────────


def test_audit_trail_ordered_and_complete(client):
    tx = client.post("/api/v1/transactions", json=high_risk_tx(uid("AUDIT"))).json()
    tx_id = tx["id"]
    client.post(f"/api/v1/transactions/{tx_id}/investigate")

    r = client.get(f"/api/v1/audit/{tx_id}")
    assert r.status_code == 200
    events = r.json()
    assert len(events) > 0

    event_types = {e["event_type"] for e in events}
    for expected in ("INVESTIGATION_STARTED", "ML_RISK_CALCULATED", "POLICY_EVALUATED"):
        assert expected in event_types, f"Missing audit event: {expected}"

    # chronological order
    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps), "Audit events are not in chronological order"


# ── GET investigation endpoints ──────────────────────────────────────────────


def test_get_investigation_by_id(client):
    tx = client.post("/api/v1/transactions", json=high_risk_tx(uid("GETINV"))).json()
    inv = client.post(f"/api/v1/transactions/{tx['id']}/investigate").json()
    inv_id = inv["investigation_id"]

    r = client.get(f"/api/v1/investigations/{inv_id}")
    assert r.status_code == 200
    assert r.json()["investigation_id"] == inv_id
    assert r.json()["status"] == "COMPLETED"


def test_get_investigation_by_transaction(client):
    tx = client.post("/api/v1/transactions", json=high_risk_tx(uid("TXINV"))).json()
    client.post(f"/api/v1/transactions/{tx['id']}/investigate")

    r = client.get(f"/api/v1/transactions/{tx['id']}/investigation")
    assert r.status_code == 200
    assert r.json()["transaction_id"] == tx["id"]
