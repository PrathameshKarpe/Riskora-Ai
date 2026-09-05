from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app.db.database import Base, make_engine
from apps.api.app.db.session import get_db, make_session_factory
from apps.api.app.main import app
from ml.training.train import train


@pytest.fixture
def client(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'api.db'}"
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    factory = make_session_factory(database_url)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    train(artifact_dir=Path("ml/models"))
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def transaction_payload():
    return {
        "external_id": "API-DEMO-001",
        "amount": 48500,
        "currency": "INR",
        "merchant": "Synthetic Demo Merchant",
        "payment_method": "UPI",
        "device_id": "new-device",
        "location": "Pune",
        "risk_context": {
            "merchant_category": "retail",
            "transaction_hour": 14,
            "transaction_day": 2,
            "transactions_last_5m": 5,
            "transactions_last_hour": 9,
            "transactions_last_24h": 12,
            "avg_historical_amount": 1500,
            "failed_transaction_count": 3,
            "account_age_days": 700,
            "previous_fraud_history": 0,
            "new_device": 1,
            "device_change_frequency": 2,
            "device_risk": 0.8,
            "country_change": 1,
            "impossible_travel": 0,
        },
    }


def test_health_and_transaction_endpoints(client):
    assert client.get("/health").json() == {"status": "ok", "service": "riskora-api"}
    response = client.post("/api/v1/transactions", json=transaction_payload())
    assert response.status_code == 201
    transaction_id = response.json()["id"]
    assert client.get(f"/api/v1/transactions/{transaction_id}").status_code == 200
    assert len(client.get("/api/v1/transactions").json()) == 1
    assert client.get("/api/v1/transactions/999").status_code == 404


def test_end_to_end_investigation_review_audit_and_dashboard(client):
    transaction_id = client.post("/api/v1/transactions", json=transaction_payload()).json()["id"]
    investigation = client.post(f"/api/v1/transactions/{transaction_id}/investigate")
    assert investigation.status_code == 200
    body = investigation.json()
    assert body["status"] == "COMPLETED"
    assert body["risk"]["risk_level"] in {"HIGH", "CRITICAL"}
    assert body["behavioral_signals"]
    assert body["evidence"]
    assert body["decision"]["policy_action"] in {"HUMAN_REVIEW", "BLOCK"}

    audit = client.get(f"/api/v1/audit/{transaction_id}")
    assert audit.status_code == 200
    events = audit.json()
    assert any(event["event_type"] == "ML_RISK_CALCULATED" for event in events)
    assert [event["timestamp"] for event in events] == sorted(event["timestamp"] for event in events)

    review = client.post(f"/api/v1/reviews/{transaction_id}/hold", json={"reason": "Synthetic verification pending."})
    assert review.status_code == 200
    assert review.json()["decision"] == "HOLD"
    reviewed_events = client.get(f"/api/v1/audit/{transaction_id}").json()
    assert reviewed_events[-1]["event_type"] == "AUDIT_RECORDED"
    assert client.get("/api/v1/dashboard/metrics").json()["total_transactions"] == 1
    assert client.get("/api/v1/dashboard/risk-distribution").status_code == 200


def test_review_requires_reason(client):
    transaction_id = client.post("/api/v1/transactions", json=transaction_payload()).json()["id"]
    response = client.post(f"/api/v1/reviews/{transaction_id}/approve", json={})
    assert response.status_code == 422
