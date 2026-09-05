from sqlalchemy.orm import Session
from apps.api.app.db.models import HumanReview, Transaction
from apps.api.app.repositories.audit_repository import add as add_audit


def submit_review(db: Session, transaction: Transaction, reviewer_id: int | None, decision: str, reason: str):
    review = HumanReview(transaction_id=transaction.id, reviewer_id=reviewer_id, decision=decision, reason=reason)
    db.add(review)
    transaction.status = decision
    add_audit(db, transaction.id, "HUMAN_REVIEW_STARTED", "reviewer", {"decision": decision})
    add_audit(db, transaction.id, "REVIEWER_DECISION", "reviewer", {"decision": decision, "reason": reason})
    add_audit(db, transaction.id, "FINAL_ACTION", "policy_engine", {"action": decision})
    add_audit(db, transaction.id, "AUDIT_RECORDED", "audit_agent", {"decision": decision})
    db.commit()
    db.refresh(review)
    return review
