from sqlalchemy import select
from sqlalchemy.orm import Session
from apps.api.app.db.models import AuditEvent


def add(db: Session, transaction_id: int, event_type: str, actor: str, payload: dict) -> AuditEvent:
    event = AuditEvent(transaction_id=transaction_id, event_type=event_type, actor=actor, payload=payload)
    db.add(event)
    db.flush()
    return event


def list_for_transaction(db: Session, transaction_id: int) -> list[AuditEvent]:
    return list(db.scalars(select(AuditEvent).where(AuditEvent.transaction_id == transaction_id).order_by(AuditEvent.timestamp, AuditEvent.id)))
