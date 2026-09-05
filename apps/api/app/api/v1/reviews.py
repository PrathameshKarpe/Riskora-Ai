from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from apps.api.app.core.security import Principal, require_roles
from apps.api.app.db.models import HumanReview, User
from apps.api.app.db.session import get_db
from apps.api.app.repositories.transaction_repository import get as get_transaction
from apps.api.app.schemas.review import ReviewRequest, ReviewResponse
from apps.api.app.services.review_service import submit_review

router = APIRouter()

def _submit(transaction_id: int, decision: str, payload: ReviewRequest, db: Session, principal: Principal):
    transaction = get_transaction(db, transaction_id)
    if not transaction:
        raise HTTPException(404, "Transaction does not exist")
    reviewer_id = int(principal.subject) if principal.subject.isdigit() else None
    if reviewer_id is None:
        reviewer = db.scalar(select(User).where(User.email == principal.subject))
        if reviewer is None:
            reviewer = User(email=principal.subject, role=principal.role)
            db.add(reviewer)
            db.flush()
        reviewer_id = reviewer.id
    return submit_review(db, transaction, reviewer_id, decision, payload.reason)

@router.post("/{transaction_id}/approve", response_model=ReviewResponse, dependencies=[Depends(require_roles("ADMIN", "REVIEWER"))])
def approve(transaction_id: int, payload: ReviewRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_roles("ADMIN", "REVIEWER"))): return _submit(transaction_id, "APPROVE", payload, db, principal)

@router.post("/{transaction_id}/block", response_model=ReviewResponse, dependencies=[Depends(require_roles("ADMIN", "REVIEWER"))])
def block(transaction_id: int, payload: ReviewRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_roles("ADMIN", "REVIEWER"))): return _submit(transaction_id, "BLOCK", payload, db, principal)

@router.post("/{transaction_id}/hold", response_model=ReviewResponse, dependencies=[Depends(require_roles("ADMIN", "REVIEWER"))])
def hold(transaction_id: int, payload: ReviewRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_roles("ADMIN", "REVIEWER"))): return _submit(transaction_id, "HOLD", payload, db, principal)

@router.get("", response_model=list[ReviewResponse], dependencies=[Depends(require_roles("ADMIN", "REVIEWER", "RISK_ANALYST"))])
def list_reviews(db: Session = Depends(get_db)): return list(db.scalars(select(HumanReview).order_by(HumanReview.created_at.desc())))

@router.get("/{transaction_id}", response_model=list[ReviewResponse], dependencies=[Depends(require_roles("ADMIN", "REVIEWER", "RISK_ANALYST"))])
def transaction_reviews(transaction_id: int, db: Session = Depends(get_db)): return list(db.scalars(select(HumanReview).where(HumanReview.transaction_id == transaction_id).order_by(HumanReview.created_at.desc())))
