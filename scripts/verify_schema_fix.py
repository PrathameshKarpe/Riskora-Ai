#!/usr/bin/env python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.app.schemas.payment import PaymentResponse
from apps.api.app.db.models import Payment
from datetime import datetime, timezone

now = datetime.now(timezone.utc)

# ORM object
p = Payment()
p.id = 1; p.transaction_id = 1; p.razorpay_order_id = "order_test"
p.razorpay_payment_id = None; p.amount_minor = 4_850_000; p.currency = "INR"
p.payment_status = "CREATED"; p.risk_status = "UNASSESSED"; p.decision = None
p.scenario = "LOW"; p.mode = "local-demo"; p.created_at = now; p.updated_at = now

r = PaymentResponse.model_validate(p)
assert r.amount == 4_850_000, f"Expected 4850000, got {r.amount}"

# Dict with amount_minor key
r2 = PaymentResponse.model_validate({
    "id": 2, "transaction_id": 1, "razorpay_order_id": "order_x",
    "razorpay_payment_id": None, "amount_minor": 10_000, "currency": "INR",
    "payment_status": "CREATED", "risk_status": "UNASSESSED", "decision": None,
    "scenario": "HIGH", "mode": "local-demo", "created_at": now, "updated_at": now,
})
assert r2.amount == 10_000

# Serialisation exposes 'amount', not 'amount_minor'
j = r.model_dump(by_alias=False)
assert "amount" in j, f"'amount' missing from output: {list(j.keys())}"
assert "amount_minor" not in j, "'amount_minor' must not appear in API output"

print("PaymentResponse schema fix: PASS")
print(f"  ORM(amount_minor=4850000) -> JSON amount={r.amount}")
print(f"  Fields: {list(j.keys())}")
