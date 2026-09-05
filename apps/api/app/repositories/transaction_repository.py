from sqlalchemy import select
from sqlalchemy.orm import Session
from apps.api.app.db.models import Transaction


def create(db: Session, data: dict) -> Transaction:
    item = Transaction(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get(db: Session, transaction_id: int) -> Transaction | None:
    return db.get(Transaction, transaction_id)


def list_recent(db: Session, limit: int = 100) -> list[Transaction]:
    return list(db.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(limit)))
