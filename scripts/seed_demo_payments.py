#!/usr/bin/env python
"""Phase 6 — Seed synthetic Razorpay Test Mode demo payments.

Creates one Payment + linked Transaction for each scenario (LOW / HIGH /
CRITICAL) plus a MEDIUM scenario using slightly elevated risk context.
All data is clearly labeled synthetic test data.  The actual risk level,
policy decision, and audit trail are always produced by the real
ML/risk/agent/policy pipeline — they are never hardcoded here.

Run after `alembic upgrade head` and `python scripts/seed_database.py`.

Usage:
    python scripts/seed_demo_payments.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://riskora:riskora@localhost:5433/riskora")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("RAZORPAY_DEMO_SECRET", "riskora-local-demo-secret")

from apps.api.app.core.config import settings
from apps.api.app.db.session import make_session_factory
from apps.api.app.repositories import payment_repository
from apps.api.app.schemas.payment import PaymentOrderRequest
from apps.api.app.services.payment_service import create_test_order
from apps.api.app.services.razorpay_service import compute_payment_signature

# ── Synthetic demo payments ───────────────────────────────────────────────────
# Amounts in paise (INR smallest unit).  The amounts are chosen to drive the
# ML model into different risk bands given the seeded risk context.

DEMO_PAYMENTS: list[dict] = [
    {
        "amount": 150_00,      # ₹150  — normal grocery purchase
        "currency": "INR",
        "scenario": "LOW",
        "label": "Normal grocery purchase — LOW risk demo",
    },
    {
        "amount": 48_500_00,   # ₹48 500 — suspicious velocity + new device
        "currency": "INR",
        "scenario": "HIGH",
        "label": "High-velocity, new device — HIGH risk demo",
    },
    {
        "amount": 2_00_000_00, # ₹2 00 000 — fraud indicators + impossible travel
        "currency": "INR",
        "scenario": "CRITICAL",
        "label": "Multiple fraud indicators — CRITICAL risk demo",
    },
]


def _already_seeded(db, scenario: str) -> bool:
    """True when a demo payment for this scenario already exists."""
    from sqlalchemy import select, text
    from apps.api.app.db.models import Payment
    row = db.execute(
        select(Payment).where(
            Payment.scenario == scenario,
            Payment.mode == "local-demo",
        )
    ).first()
    return row is not None


def main() -> None:
    db = make_session_factory(settings.database_url)()
    try:
        created = 0
        skipped = 0
        for demo in DEMO_PAYMENTS:
            scenario = demo["scenario"]
            if _already_seeded(db, scenario):
                print(f"  [skip] {scenario} payment already exists")
                skipped += 1
                continue

            req = PaymentOrderRequest(
                amount=demo["amount"],
                currency=demo["currency"],
                scenario=scenario,  # type: ignore[arg-type]
            )
            payment = create_test_order(db, req)

            # For the local-demo pipeline, simulate a verified checkout so
            # risk assessment runs automatically.  We generate a valid
            # local-demo HMAC signature to exercise the same verification
            # code path as a real Razorpay checkout.
            fake_payment_id = f"pay_demo_{scenario.lower()}_{payment.id:04d}"
            sig = compute_payment_signature(payment.razorpay_order_id, fake_payment_id)

            from apps.api.app.schemas.payment import PaymentVerifyRequest
            from apps.api.app.services.payment_service import verify_payment
            verify_req = PaymentVerifyRequest(
                razorpay_order_id=payment.razorpay_order_id,
                razorpay_payment_id=fake_payment_id,
                razorpay_signature=sig,
            )
            payment, triggered = verify_payment(db, verify_req)

            print(
                f"  [OK]  {scenario:8s}  order={payment.razorpay_order_id}"
                f"  tx_id={payment.transaction_id}"
                f"  payment_status={payment.payment_status}"
                f"  risk_status={payment.risk_status}"
                f"  decision={payment.decision}"
                f"  pipeline={'triggered' if triggered else 'skipped (already run)'}"
            )
            print(f"         ↳ {demo['label']}")
            created += 1

        print(
            f"\nDemo payments: {created} created, {skipped} skipped."
            "\n[SYNTHETIC TEST DATA — not real fraud]"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
