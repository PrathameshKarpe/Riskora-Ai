from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from agents.graph.workflow import run_investigation
from ml.inference.predict import TransactionPredictor
from apps.api.app.db.models import AgentFinding, AuditEvent, Evidence, Investigation, PolicyDecision, RiskAssessment
from apps.api.app.repositories.audit_repository import add as add_audit


def _model_transaction(transaction):
    context = dict(transaction.risk_context or {})
    context.update({
        "transaction_id": transaction.external_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "payment_method": transaction.payment_method.lower(),
        "merchant_category": context.get("merchant_category", "retail"),
    })
    return context


def run_and_persist(db: Session, transaction, predictor=None) -> Investigation:
    investigation = Investigation(transaction_id=transaction.id, status="RUNNING", started_at=datetime.now(timezone.utc))
    db.add(investigation)
    transaction.status = "INVESTIGATING"
    db.flush()
    add_audit(db, transaction.id, "INVESTIGATION_STARTED", "system", {"status": "RUNNING"})
    try:
        result = run_investigation(
            _model_transaction(transaction),
            predictor or TransactionPredictor(),
            audit_path=f"audit/api-{transaction.id}.json",
        )
        ml = result["ml_assessment"]
        behavior = result["behavioral_findings"]
        investigation.status = "COMPLETED" if not result.get("errors") else "FAILED"
        investigation.summary = result.get("investigation_findings", {}).get("summary")
        investigation.confidence = result.get("investigation_findings", {}).get("confidence")
        investigation.completed_at = datetime.now(timezone.utc)
        db.add(RiskAssessment(transaction_id=transaction.id, model_version=ml["model_version"], fraud_probability=ml["fraud_probability"], ml_risk_score=ml["risk_score"], behavioral_risk=behavior.get("behavioral_risk", "UNKNOWN"), final_risk_score=result.get("final_risk_score", ml["risk_score"]), risk_level=result["policy_result"]["risk_level"]))
        for finding in behavior.get("findings", []):
            db.add(AgentFinding(investigation_id=investigation.id, agent_name="behavior_agent", status="completed", finding=finding, confidence=None))
        for event in result.get("audit_events", []):
            add_audit(db, transaction.id, event["event"], "investigation_workflow", event.get("details", {}))
        for item in result.get("evidence", []):
            db.add(Evidence(investigation_id=investigation.id, source=item["source"], section=item["section"], content=item["content"], relevance_score=item["relevance_score"], metadata_json=item["metadata"]))
        decision = result.get("decision_recommendation", {})
        policy = result["policy_result"]
        db.add(PolicyDecision(transaction_id=transaction.id, policy_version=policy["policy_version"], ai_recommendation=decision.get("recommendation", "HUMAN_REVIEW"), policy_action=policy["policy_action"], requires_human_review=policy["requires_human_review"], reason_codes=policy["reason_codes"], explanation=policy["explanation"]))
        transaction.status = "PENDING_REVIEW" if policy["requires_human_review"] else policy["policy_action"]
        add_audit(db, transaction.id, "POLICY_EVALUATED", "policy_engine", policy)
        db.commit()
        db.refresh(investigation)
        return investigation
    except Exception:
        investigation.status = "FAILED"
        investigation.completed_at = datetime.now(timezone.utc)
        transaction.status = "INVESTIGATION_FAILED"
        db.commit()
        raise
