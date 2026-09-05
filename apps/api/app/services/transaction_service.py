from sqlalchemy.orm import Session
from apps.api.app.repositories import transaction_repository
from apps.api.app.schemas.transaction import TransactionCreate


def create_transaction(db: Session, payload: TransactionCreate):
    return transaction_repository.create(db, payload.model_dump())


def get_transaction(db: Session, transaction_id: int):
    return transaction_repository.get(db, transaction_id)
