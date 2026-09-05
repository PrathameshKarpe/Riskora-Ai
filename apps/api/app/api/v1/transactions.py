from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from apps.api.app.core.security import current_principal
from apps.api.app.db.session import get_db
from apps.api.app.repositories.transaction_repository import get, list_recent
from apps.api.app.schemas.transaction import TransactionCreate, TransactionResponse
from apps.api.app.services.transaction_service import create_transaction

router = APIRouter()

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(current_principal)])
def create(payload: TransactionCreate, db: Session = Depends(get_db)):
    return create_transaction(db, payload)

@router.get("", response_model=list[TransactionResponse], dependencies=[Depends(current_principal)])
def list_transactions(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return list_recent(db, limit)

@router.get("/{transaction_id}", response_model=TransactionResponse, dependencies=[Depends(current_principal)])
def get_one(transaction_id: int, db: Session = Depends(get_db)):
    item = get(db, transaction_id)
    if not item:
        raise HTTPException(status_code=404, detail={"code": "TRANSACTION_NOT_FOUND", "message": "Transaction does not exist."})
    return item
