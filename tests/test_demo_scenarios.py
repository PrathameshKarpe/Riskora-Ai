from pathlib import Path

from ml.inference.predict import TransactionPredictor
from ml.training.train import train
from risk_engine.assessment import RiskAssessmentService
from risk_engine.demo_transactions import demo_transactions


def test_demo_scenarios_use_real_model(tmp_path: Path):
    artifact_dir = tmp_path / "models"
    train(artifact_dir=artifact_dir)
    service = RiskAssessmentService(TransactionPredictor(artifact_dir / "risk_model.joblib"))
    results = {name: service.assess(transaction) for name, transaction in demo_transactions().items()}

    assert results["normal"]["risk_level"] == "LOW"
    assert results["normal"]["recommended_action"] == "APPROVE"
    assert results["suspicious"]["risk_level"] in {"HIGH", "CRITICAL"}
    assert results["suspicious"]["recommended_action"] in {"HOLD", "BLOCK"}
    assert results["critical"]["risk_level"] == "CRITICAL"
    assert results["critical"]["recommended_action"] == "BLOCK"
