"""Investigation repository.

Eagerly loads every relationship that investigations.py's _response() helper
accesses, to prevent DetachedInstanceError after the session is closed.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.db.models import Investigation, Transaction


def _options():
    """selectinload chain for the full investigation graph."""
    return [
        selectinload(Investigation.findings),
        selectinload(Investigation.evidence),
        selectinload(Investigation.transaction).selectinload(Transaction.assessments),
        selectinload(Investigation.transaction).selectinload(Transaction.policy_decisions),
    ]


def get(db: Session, investigation_id: int) -> Investigation | None:
    return db.scalars(
        select(Investigation)
        .where(Investigation.id == investigation_id)
        .options(*_options())
    ).first()


def get_latest(db: Session, transaction_id: int) -> Investigation | None:
    return db.scalars(
        select(Investigation)
        .where(Investigation.transaction_id == transaction_id)
        .options(*_options())
        .order_by(Investigation.started_at.desc())
    ).first()
