"""Persistence helpers for payments and webhook events (Phase 6)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.db.models import Payment, WebhookEvent


def create_payment(db: Session, data: dict) -> Payment:
    payment = Payment(**data)
    db.add(payment)
    db.flush()
    return payment


def get_by_transaction(db: Session, transaction_id: int) -> Payment | None:
    return db.scalar(select(Payment).where(Payment.transaction_id == transaction_id))


def get_by_order(db: Session, razorpay_order_id: str) -> Payment | None:
    return db.scalar(select(Payment).where(Payment.razorpay_order_id == razorpay_order_id))


def list_recent(db: Session, limit: int = 100) -> list[Payment]:
    return list(db.scalars(select(Payment).order_by(Payment.created_at.desc()).limit(limit)))


def webhook_event_seen(db: Session, event_id: str) -> WebhookEvent | None:
    return db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == event_id))


def record_webhook_event(db: Session, data: dict) -> WebhookEvent:
    event = WebhookEvent(**data)
    db.add(event)
    db.flush()
    return event