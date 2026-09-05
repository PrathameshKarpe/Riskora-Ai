"""Synthetic Phase 2 scenarios used for demonstrations and tests only."""

from __future__ import annotations

from typing import Any


_BASE = {
    "currency": "INR",
    "payment_method": "upi",
    "merchant_category": "retail",
    "transaction_hour": 14,
    "transaction_day": 2,
    "transactions_last_5m": 0,
    "transactions_last_hour": 1,
    "transactions_last_24h": 4,
    "avg_historical_amount": 1500.0,
    "failed_transaction_count": 0,
    "account_age_days": 700,
    "previous_fraud_history": 0,
    "new_device": 0,
    "device_change_frequency": 0,
    "device_risk": 0.1,
    "country_change": 0,
    "impossible_travel": 0,
}


def demo_transactions() -> dict[str, dict[str, Any]]:
    normal = {**_BASE, "transaction_id": "DEMO-NORMAL", "amount": 1500.0}
    suspicious = {
        **_BASE, "transaction_id": "DEMO-SUSPICIOUS", "amount": 48500.0,
        "new_device": 1, "country_change": 1, "transactions_last_5m": 5,
        "transactions_last_hour": 9, "failed_transaction_count": 3,
        "device_risk": 0.8,
    }
    critical = {
        **_BASE, "transaction_id": "DEMO-CRITICAL", "amount": 125000.0,
        "new_device": 1, "country_change": 1, "impossible_travel": 1,
        "transactions_last_5m": 8, "transactions_last_hour": 15,
        "failed_transaction_count": 5, "previous_fraud_history": 1,
        "transaction_hour": 2, "device_risk": 0.95,
    }
    return {"normal": normal, "suspicious": suspicious, "critical": critical}
