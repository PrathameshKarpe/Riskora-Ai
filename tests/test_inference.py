from ml.data.generate_demo import generate_demo_transactions
from ml.inference.predict import risk_level
from ml.training.train import train


def test_risk_level_thresholds():
    assert risk_level(29.99) == "LOW"
    assert risk_level(30) == "MEDIUM"
    assert risk_level(60) == "HIGH"
    assert risk_level(85) == "CRITICAL"


def test_trained_inference_returns_contract(tmp_path):
    input_path = tmp_path / "transactions.csv"
    generate_demo_transactions(220).to_csv(input_path, index=False)
    artifact_dir = tmp_path / "models"
    train(input_path, artifact_dir)

    from ml.inference.predict import TransactionPredictor

    transaction = generate_demo_transactions(20).drop(columns=["is_fraud"]).iloc[0].to_dict()
    result = TransactionPredictor(artifact_dir / "risk_model.joblib").predict_transaction(transaction)
    assert set(result) == {"fraud_probability", "risk_score", "risk_level", "model_version"}
    assert 0 <= result["fraud_probability"] <= 1
    assert 0 <= result["risk_score"] <= 100
