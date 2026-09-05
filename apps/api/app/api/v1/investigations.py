from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.api.app.core.security import require_roles
from apps.api.app.db.session import get_db
from apps.api.app.repositories.investigation_repository import get, get_latest
from apps.api.app.repositories.transaction_repository import get as get_transaction
from apps.api.app.schemas.investigation import InvestigationResponse
from apps.api.app.services.investigation_service import run_and_persist

router = APIRouter()

def _response(item):
    risk = item.transaction.assessments[-1] if item.transaction.assessments else None
    policy = item.transaction.policy_decisions[-1] if item.transaction.policy_decisions else None
    return {"investigation_id": item.id, "transaction_id": item.transaction_id, "status": item.status, "summary": item.summary, "confidence": item.confidence, "started_at": item.started_at, "completed_at": item.completed_at, "risk": {"model_version": risk.model_version, "ml_score": risk.ml_risk_score, "final_score": risk.final_risk_score, "risk_level": risk.risk_level, "behavioral_risk": risk.behavioral_risk} if risk else None, "behavioral_signals": [finding.finding for finding in item.findings if finding.agent_name == "behavior_agent"], "agents": [{"agent_name": finding.agent_name, "status": finding.status, "finding": finding.finding, "confidence": finding.confidence} for finding in item.findings], "evidence": [{"source": evidence.source, "section": evidence.section, "content": evidence.content, "relevance_score": evidence.relevance_score, "metadata": evidence.metadata_json} for evidence in item.evidence], "decision": {"recommendation": policy.ai_recommendation, "policy_action": policy.policy_action, "requires_human_review": policy.requires_human_review, "reason_codes": policy.reason_codes, "explanation": policy.explanation} if policy else None}

@router.post("/transactions/{transaction_id}/investigate", response_model=InvestigationResponse, dependencies=[Depends(require_roles("ADMIN", "RISK_ANALYST"))])
def investigate(transaction_id: int, db: Session = Depends(get_db)):
    transaction = get_transaction(db, transaction_id)
    if not transaction:
        raise HTTPException(404, "Transaction does not exist")
    return _response(run_and_persist(db, transaction))

@router.get("/investigations/{investigation_id}", response_model=InvestigationResponse, dependencies=[Depends(require_roles("ADMIN", "RISK_ANALYST", "REVIEWER"))])
def get_investigation(investigation_id: int, db: Session = Depends(get_db)):
    item = get(db, investigation_id)
    if not item:
        raise HTTPException(404, "Investigation does not exist")
    return _response(item)

@router.get("/transactions/{transaction_id}/investigation", response_model=InvestigationResponse, dependencies=[Depends(require_roles("ADMIN", "RISK_ANALYST", "REVIEWER"))])
def get_transaction_investigation(transaction_id: int, db: Session = Depends(get_db)):
    item = get_latest(db, transaction_id)
    if not item:
        raise HTTPException(404, "Investigation does not exist")
    return _response(item)
