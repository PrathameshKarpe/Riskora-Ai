from pathlib import Path

from agents.graph.workflow import run_investigation
from ml.inference.predict import TransactionPredictor
from ml.training.train import train
from risk_engine.demo_transactions import demo_transactions


def test_langgraph_workflow_completes_and_audits(tmp_path: Path):
    artifact_dir = tmp_path / "models"
    train(artifact_dir=artifact_dir)
    result = run_investigation(demo_transactions()["suspicious"], TransactionPredictor(artifact_dir / "risk_model.joblib"), audit_path=str(tmp_path / "audit.json"))
    events = {event["event"] for event in result["audit_events"]}
    assert result["evidence_status"] == "RETRIEVED"
    assert result["policy_result"]["policy_action"] == "HUMAN_REVIEW"
    assert {"TRANSACTION_RECEIVED", "ML_RISK_CALCULATED", "BEHAVIOR_ANALYSIS_COMPLETED", "EVIDENCE_RETRIEVED", "DECISION_GENERATED", "POLICY_EVALUATED", "AUDIT_RECORDED"}.issubset(events)
    assert (tmp_path / "audit.json").exists()


def test_workflow_handles_llm_unavailable(tmp_path: Path):
    artifact_dir = tmp_path / "models"
    train(artifact_dir=artifact_dir)
    result = run_investigation(demo_transactions()["normal"], TransactionPredictor(artifact_dir / "risk_model.joblib"), audit_path=str(tmp_path / "audit.json"), llm_available=False)
    assert result["decision_status"] == "LLM_UNAVAILABLE"
    assert result["policy_result"]["policy_action"] == "HUMAN_REVIEW"


def test_workflow_validation_failure_is_recorded(tmp_path: Path):
    artifact_dir = tmp_path / "models"
    train(artifact_dir=artifact_dir)
    result = run_investigation({}, TransactionPredictor(artifact_dir / "risk_model.joblib"), audit_path=str(tmp_path / "audit.json"))
    assert result["errors"]
    assert result["errors"][0]["agent"] == "VALIDATION"
