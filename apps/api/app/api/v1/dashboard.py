from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.app.core.security import current_principal
from apps.api.app.db.session import get_db
from apps.api.app.repositories.transaction_repository import list_recent
from apps.api.app.services.dashboard_service import metrics

router = APIRouter()

@router.get("/metrics", dependencies=[Depends(current_principal)])
def dashboard_metrics(db: Session = Depends(get_db)): return metrics(db)

@router.get("/risk-distribution", dependencies=[Depends(current_principal)])
def risk_distribution(db: Session = Depends(get_db)):
    from sqlalchemy import func, select
    from apps.api.app.db.models import RiskAssessment
    return {level: count for level, count in db.execute(select(RiskAssessment.risk_level, func.count()).group_by(RiskAssessment.risk_level))}

@router.get("/recent-transactions", dependencies=[Depends(current_principal)])
def recent_transactions(db: Session = Depends(get_db)): return list_recent(db, 20)

@router.get("/pending-reviews", dependencies=[Depends(current_principal)])
def pending_reviews(db: Session = Depends(get_db)): return metrics(db)["pending_reviews"]
