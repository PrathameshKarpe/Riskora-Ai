"""Phase 6 payment orchestration (Razorpay Test Mode -> Riskora pipeline).

Responsibilities:
- create Test Mode orders and link them to Riskora transactions
- verify checkout signatures server-side (never trust the browser)
- process webhooks with signature verification and idempotency
- map payment events to a separate payment-status state machine
- trigger the EXISTING Riskora investigation pipeline (single source of
  truth: ML -> Behavior -> Investigation -> Evidence -> Decision -> Policy)

Payment status, risk status, and decision are separate state machines and
never overwrite each other (Phase 6 Step 14).
"""
from __future__ import annotations

import json
import logging
import secrets
from typing import Any

from sqlalchemy.orm import Session

from apps.api.app.core.config import settings
from apps.api.app.db.models import Payment, Transaction, WebhookEvent
from apps.api.app.repositories import payment_repository
from apps.api.app.repositories.audit_repository import add as add_audit
from apps.api.app.repositories.transaction_repository import create as create_transaction
from apps.api.app.schemas.payment import PaymentOrderRequest, PaymentVerifyRequest
from apps.api.app.services import razorpay_service
from apps.api.app.services.razorpay_service import RazorpayError
from apps.api.app.services.investigation_service import run_and_persist

logger = logging.getLogger(__name__)

# Payment lifecycle ranks. Only forward transitions are applied so an
# out-of-order or repeated webhook can never overwrite a newer state.
_PAYMENT_STATE_RANK = {"CREATED": 0, "AUTHORIZED": 1, "CAPTURED": 2}
_TERMINAL_PAYMENT_STATES = {"CAPTURED", "FAILED"}

# Supported Razorpay Test Mode webhook events (Phase 6 Step 9).
SUPPORTED_WEBHOOK_EVENTS = {
    "payment.authorized",
    "payment.captured",
    "payment.failed",
    "order.paid",
}


class PaymentVerificationError(Exception):
    """Raised when a checkout signature fails server-side verification."""


class WebhookVerificationError(Exception):
    """Raised when a webhook signature fails server-side verification."""


# ── Synthetic demo scenarios (Phase 6 Step 11) ───────────────────────────────
# Clearly labeled SYNTHETIC TEST DATA for the Buildathon demo. These context
# values seed the risk engine; the actual risk level, decision, and audit
# trail are always produced by the real ML/risk/agent/policy pipeline —
# never hardcoded.

_SCENARIO_CONTEXTS: dict[str, dict[str, Any]] = {
    "LOW": {
        "merchant_category": "retail",
        "transaction_hour": 14,
        "transaction_day": 2,
        "transactions_last_5m": 0,
        "transactions_last_hour": 1,
        "transactions_last_24h": 4,
        "avg_historical_amount": None,  # filled from order amount
        "failed_transaction_count": 0,
        "account_age_days": 700,
        "previous_fraud_history": 0,
        "new_device": 0,
        "device_change_frequency": 0,
        "device_risk": 0.1,
        "country_change": 0,
        "impossible_travel": 0,
    },
    "HIGH": {
        "merchant_category": "retail",
        "transaction_hour": 14,
        "transaction_day": 2,
        "transactions_last_5m": 5,
        "transactions_last_hour": 9,
        "transactions_last_24h": 4,
        "avg_historical_amount": None,
        "failed_transaction_count": 3,
        "account_age_days": 700,
        "previous_fraud_history": 0,
        "new_device": 1,
        "device_change_frequency": 0,
        "device_risk": 0.8,
        "country_change": 1,
        "impossible_travel": 0,
    },
    "CRITICAL": {
        "merchant_category": "retail",
        "transaction_hour": 2,
        "transaction_day": 2,
        "transactions_last_5m": 8,
        "transactions_last_hour": 15,
        "transactions_last_24h": 4,
        "avg_historical_amount": None,
        "failed_transaction_count": 5,
        "account_age_days": 700,
        "previous_fraud_history": 1,
        "new_device": 1,
        "device_change_frequency": 0,
        "device_risk": 0.95,
        "country_change": 1,
        "impossible_travel": 1,
    },
}

_SCENARIO_DEVICE = {
    "LOW": "demo-device-known",
    "HIGH": "demo-device-new",
    "CRITICAL": "demo-device-unknown",
}

_SCENARIO_LOCATION = {
    "LOW": "Home City",
    "HIGH": "Unrecognized City",
    "CRITICAL": "High-Risk Region",
}


def _scenario_context(scenario: str, amount_minor: int) -> dict[str, Any]:
    """Build the synthetic risk context for a demo scenario.

    The historical average is anchored so the amount anomaly ratio matches
    the scenario intent (LOW ~1x, HIGH ~32x, CRITICAL ~80x) while the real
    model and behavior engine still compute the outcome.
    """
    context = dict(_SCENARIO_CONTEXTS[scenario])
    amount = amount_minor / 100.0
    ratio = {"LOW": 1.0, "HIGH": 32.0, "CRITICAL": 80.0}[scenario]
    context["avg_historical_amount"] = max(round(amount / ratio, 2), 1.0)
    context["demo_scenario"] = scenario
    context["data_label"] = "synthetic-test-data"
    return context


# ── Order creation (Phase 6 Step 4) ──────────────────────────────────────────

def create_test_order(db: Session, payload: PaymentOrderRequest) -> Payment:
    """Create a Razorpay Test Mode order plus the linked Riskora transaction.

    The transaction enters the normal Riskora pipeline; nothing about the
    risk outcome is decided here.
    """
    scenario = payload.scenario
    order = razorpay_service.create_order(
        amount_minor=payload.amount,
        currency=payload.currency,
        receipt=f"riskora-{secrets.token_hex(6)}",
        notes={"source": "riskora-demo", "scenario": scenario},
    )

    transaction = create_transaction(db, {
        "external_id": order.order_id,
        "amount": payload.amount / 100.0,
        "currency": payload.currency,
        "merchant": "Razorpay Test Payment",
        "payment_method": "razorpay_test",
        "device_id": _SCENARIO_DEVICE[scenario],
        "location": _SCENARIO_LOCATION[scenario],
        "risk_context": _scenario_context(scenario, payload.amount),
    })

    payment = payment_repository.create_payment(db, {
        "transaction_id": transaction.id,
        "razorpay_order_id": order.order_id,
        "amount_minor": payload.amount,
        "currency": payload.currency,
        "payment_status": "CREATED",
        "risk_status": "UNASSESSED",
        "scenario": scenario,
        "mode": order.mode,
    })

    add_audit(db, transaction.id, "PAYMENT_ORDER_CREATED", "razorpay_integration", {
        "razorpay_order_id": order.order_id,
        "amount": payload.amount,
        "currency": payload.currency,
        "mode": order.mode,
        "scenario": scenario,
        "data_label": "synthetic-test-data",
    })
    db.commit()
    db.refresh(payment)
    return payment


# ── Checkout verification (Phase 6 Step 6) ───────────────────────────────────

def verify_payment(db: Session, payload: PaymentVerifyRequest) -> tuple[Payment, bool]:
    """Verify the checkout signature server-side and process the payment.

    Returns (payment, investigation_triggered). Raises
    PaymentVerificationError when the signature is invalid — the payment is
    then never marked verified and a security audit event is recorded.
    """
    payment = payment_repository.get_by_order(db, payload.razorpay_order_id)
    if not payment:
        raise PaymentVerificationError("Unknown payment order.")

    if not razorpay_service.verify_payment_signature(
        payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature
    ):
        add_audit(db, payment.transaction_id, "PAYMENT_VERIFICATION_FAILED", "razorpay_integration", {
            "razorpay_order_id": payload.razorpay_order_id,
            "reason": "invalid_signature",
        })
        db.commit()
        raise PaymentVerificationError("Payment signature verification failed.")

    payment.razorpay_payment_id = payload.razorpay_payment_id
    _advance_payment_status(db, payment, "AUTHORIZED", actor="razorpay_checkout")
    db.commit()
    db.refresh(payment)

    investigation_triggered = _trigger_riskora_if_needed(db, payment)
    return payment, investigation_triggered


# ── Webhook processing (Phase 6 Steps 8-9) ───────────────────────────────────

def handle_webhook(db: Session, raw_body: bytes, signature: str) -> tuple[bool, bool, str | None]:
    """Process a Razorpay webhook delivery.

    Returns (accepted, duplicate, event_id). The raw body is verified
    BEFORE parsing. Duplicate event ids are acknowledged but not
    reprocessed. Unknown event types are stored and acknowledged so
    Razorpay does not retry forever.
    """
    # 1. Signature first — never parse an untrusted body.
    if not razorpay_service.verify_webhook_signature(raw_body, signature):
        logger.warning("Webhook rejected: invalid signature")
        raise WebhookVerificationError("Webhook signature verification failed.")

    # 2. Now safe to parse.
    try:
        event = json.loads(raw_body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        logger.warning("Webhook rejected: malformed JSON body")
        raise WebhookVerificationError("Webhook body is not valid JSON.")

    event_id = str(event.get("id") or "")
    event_type = str(event.get("event") or "")
    if not event_id:
        raise WebhookVerificationError("Webhook event is missing an event id.")

    # 3. Idempotency: duplicate deliveries are acknowledged, not reprocessed.
    if payment_repository.webhook_event_seen(db, event_id):
        return True, True, event_id

    # 4. Resolve the related payment (if any) and record the event.
    payment, transaction_id = _resolve_payment_from_event(db, event)
    webhook_event: WebhookEvent = payment_repository.record_webhook_event(db, {
        "event_id": event_id,
        "event_type": event_type,
        "signature_valid": True,
        "transaction_id": transaction_id,
        "payload": event,
    })

    if payment is None:
        # Unknown order (e.g. event for an order not created here): store and ack.
        db.commit()
        return True, False, event_id

    if event_type not in SUPPORTED_WEBHOOK_EVENTS:
        add_audit(db, payment.transaction_id, "WEBHOOK_EVENT_IGNORED", "razorpay_integration", {
            "event_id": event_id,
            "event_type": event_type,
        })
        db.commit()
        return True, False, event_id

    # 5. Map the event to a payment status (forward-only transitions).
    target_status = _event_to_status(event_type, event)
    if target_status:
        if event_type == "payment.failed":
            _mark_failed(db, payment, event, event_id)
        else:
            _advance_payment_status(db, payment, target_status, actor=f"razorpay_webhook:{event_type}",
                                    payment_id=_extract_payment_id(event))
            if payment.razorpay_payment_id is None:
                payment.razorpay_payment_id = _extract_payment_id(event)

    db.commit()
    db.refresh(payment)

    # 6. Trigger Riskora processing when the payment becomes authentic.
    if target_status in {"AUTHORIZED", "CAPTURED"}:
        _trigger_riskora_if_needed(db, payment)

    return True, False, event_id


def _event_to_status(event_type: str, event: dict[str, Any]) -> str | None:
    if event_type == "payment.authorized":
        return "AUTHORIZED"
    if event_type == "payment.captured":
        return "CAPTURED"
    if event_type == "order.paid":
        return "CAPTURED"
    if event_type == "payment.failed":
        return "FAILED"
    return None


def _extract_payment_id(event: dict[str, Any]) -> str | None:
    entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = entity.get("id")
    return str(payment_id) if payment_id else None


def _resolve_payment_from_event(db: Session, event: dict[str, Any]) -> tuple[Payment | None, int | None]:
    payload = event.get("payload", {})
    order_entity = payload.get("order", {}).get("entity", {})
    order_id = order_entity.get("id")
    if not order_id and event.get("event") == "order.paid":
        order_id = event.get("payload", {}).get("order", {}).get("entity", {}).get("id")
    if not order_id:
        # payment.* events always carry the order entity in practice; fall
        # back to the payment entity's order_id field.
        payment_entity = payload.get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
    if not order_id:
        return None, None
    payment = payment_repository.get_by_order(db, str(order_id))
    return (payment, payment.transaction_id) if payment else (None, None)


def _advance_payment_status(db: Session, payment: Payment, target: str, actor: str, payment_id: str | None = None) -> None:
    """Forward-only transition. Older or repeated events never regress state."""
    current_rank = _PAYMENT_STATE_RANK.get(payment.payment_status, 0)
    target_rank = _PAYMENT_STATE_RANK.get(target)
    if target_rank is None or payment.payment_status in _TERMINAL_PAYMENT_STATES:
        return
    if target_rank <= current_rank:
        return
    previous = payment.payment_status
    payment.payment_status = target
    if payment_id:
        payment.razorpay_payment_id = payment_id
    add_audit(db, payment.transaction_id, "PAYMENT_STATUS_UPDATED", actor, {
        "from": previous,
        "to": target,
        "razorpay_order_id": payment.razorpay_order_id,
    })


def _mark_failed(db: Session, payment: Payment, event: dict[str, Any], event_id: str) -> None:
    """payment.failed is terminal: never overwritten by later events."""
    if payment.payment_status in _TERMINAL_PAYMENT_STATES:
        return
    previous = payment.payment_status
    payment.payment_status = "FAILED"
    add_audit(db, payment.transaction_id, "PAYMENT_STATUS_UPDATED", "razorpay_webhook:payment.failed", {
        "from": previous,
        "to": "FAILED",
        "razorpay_order_id": payment.razorpay_order_id,
        "event_id": event_id,
    })


# ── Riskora pipeline trigger (Phase 6 Steps 7 & 10) ──────────────────────────

def _trigger_riskora_if_needed(db: Session, payment: Payment) -> bool:
    """Run the existing investigation pipeline once per payment.

    Reuses investigation_service.run_and_persist — the single source of
    truth for ML -> Behavior -> Investigation -> Evidence -> Decision ->
    Policy. Updates only the payment's risk_status/decision state machines.
    """
    if payment.risk_status != "UNASSESSED":
        return False

    transaction = payment.transaction
    add_audit(db, payment.transaction_id, "RISK_PIPELINE_TRIGGERED", "razorpay_integration", {
        "razorpay_order_id": payment.razorpay_order_id,
        "payment_status": payment.payment_status,
    })
    try:
        investigation = run_and_persist(db, transaction)
    except Exception:
        # Pipeline failure must not falsely mark the payment successful or
        # assessed; the payment keeps its authentic payment status.
        logger.exception("Riskora pipeline failed for transaction %s", transaction.id)
        add_audit(db, payment.transaction_id, "RISK_PIPELINE_FAILED", "razorpay_integration", {
            "razorpay_order_id": payment.razorpay_order_id,
        })
        db.commit()
        return False

    # Risk level comes from the RiskAssessment; the decision from the
    # deterministic PolicyDecision. Two separate state machines.
    payment.risk_status = _risk_level_from(transaction)
    policy = transaction.policy_decisions[-1] if transaction.policy_decisions else None
    if policy is not None:
        payment.decision = policy.policy_action
    add_audit(db, payment.transaction_id, "PAYMENT_RISK_ASSESSED", "razorpay_integration", {
        "razorpay_order_id": payment.razorpay_order_id,
        "risk_status": payment.risk_status,
        "decision": payment.decision,
        "investigation_id": investigation.id,
    })
    db.commit()
    db.refresh(payment)
    return True


def _risk_level_from(transaction: Transaction) -> str:
    assessment = transaction.assessments[-1] if transaction.assessments else None
    return assessment.risk_level if assessment else "UNASSESSED"


# ── Public config for the frontend (Phase 6 Step 5) ──────────────────────────

def payment_config() -> dict[str, Any]:
    """Only the public Key ID is exposed. Secrets never leave the backend."""
    test_mode = razorpay_service.is_test_mode_configured()
    return {
        "mode": "razorpay-test" if test_mode else "local-demo",
        "key_id": razorpay_service.public_key_id() if test_mode else None,
        "webhook_configured": razorpay_service.is_webhook_configured(),
    }