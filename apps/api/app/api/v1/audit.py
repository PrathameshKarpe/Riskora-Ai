from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.app.core.security import require_roles
from apps.api.app.db.session import get_db
from apps.api.app.repositories.audit_repository import list_for_transaction
from apps.api.app.schemas.audit import AuditResponse

router = APIRouter()

@router.get("/{transaction_id}", response_model=list[AuditResponse], dependencies=[Depends(require_roles("ADMIN", "RISK_ANALYST", "REVIEWER"))])
def audit(transaction_id: int, db: Session = Depends(get_db)): return list_for_transaction(db, transaction_id)
