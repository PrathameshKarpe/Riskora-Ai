from sqlalchemy import func, select
from sqlalchemy.orm import Session
from apps.api.app.db.models import HumanReview, RiskAssessment, Transaction


def metrics(db: Session) -> dict:
    total = db.scalar(select(func.count(Transaction.id))) or 0
    blocked = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "BLOCK")) or 0
    approved = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "APPROVE")) or 0
    pending = db.scalar(select(func.count(Transaction.id)).where(Transaction.status == "PENDING_REVIEW")) or 0
    suspicious = db.scalar(select(func.count(RiskAssessment.id)).where(RiskAssessment.risk_level.in_(["HIGH", "CRITICAL"]))) or 0
    return {"total_transactions": total, "suspicious_transactions": suspicious, "blocked_transactions": blocked, "approved_transactions": approved, "pending_reviews": pending, "fraud_detection_rate": None, "false_positive_rate": None, "estimated_prevented_loss": None}
