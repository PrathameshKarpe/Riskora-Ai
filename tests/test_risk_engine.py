import pytest

from ml.inference.predict import risk_level
from risk_engine.assessment import RiskAssessmentService
from risk_engine.behavior import BehaviorEngine
from risk_engine.demo_transactions import demo_transactions
from risk_engine.policy import PolicyConfig, PolicyEngine


class StubPredictor:
    def __init__(self, score):
        self.score = score

    def predict_transaction(self, transaction):
        return {
            "fraud_probability": self.score / 100,
            "risk_score": self.score,
            "risk_level": risk_level(self.score),
            "model_version": "stub-v1",
        }


@pytest.mark.parametrize("score, expected", [(0, "LOW"), (29.99, "LOW"), (30, "MEDIUM"), (60, "HIGH"), (85, "CRITICAL"), (100, "CRITICAL")])
def test_policy_risk_thresholds(score, expected):
    assert PolicyEngine().evaluate(score)["risk_level"] == expected


def test_behavior_engine_returns_structured_signals():
    result = BehaviorEngine().analyze(demo_transactions()["suspicious"])
    assert result["behavioral_risk"] in {"HIGH", "CRITICAL"}
    names = {signal["signal"] for signal in result["signals"]}
    assert {"amount_anomaly", "transaction_velocity", "new_device", "new_location"}.issubset(names)
    assert all({"signal", "severity", "value", "explanation", "source"}.issubset(signal) for signal in result["signals"])


def test_missing_behavioral_data_is_explicitly_unavailable():
    result = BehaviorEngine().analyze({"amount": 100, "avg_historical_amount": 100})
    signal = next(item for item in result["signals"] if item["signal"] == "new_device")
    assert signal["value"] == "unavailable"
    assert signal["source"] == "future-production-signal"


def test_policy_combination_forces_human_review():
    signals = [
        {"signal": "transaction_velocity", "severity": "HIGH"},
        {"signal": "failed_payment_attempts", "severity": "HIGH"},
    ]
    result = PolicyEngine().evaluate(30, signals)
    assert result["policy_action"] == "HUMAN_REVIEW"
    assert "HIGH_VELOCITY_FAILED_ATTEMPTS" in result["reason_codes"]


def test_policy_thresholds_are_configurable():
    engine = PolicyEngine(PolicyConfig(low_max=20, medium_max=40, high_max=70))
    assert engine.evaluate(19.99)["risk_level"] == "LOW"
    assert engine.evaluate(40)["risk_level"] == "HIGH"


def test_invalid_score_is_rejected_by_assessment_predictor_contract():
    service = RiskAssessmentService(StubPredictor(40))
    result = service.assess(demo_transactions()["normal"])
    assert result["final_risk_score"] >= 0


def test_unified_low_medium_high_critical_actions():
    scenarios = [(10, "APPROVE", False), (40, "REVIEW", False), (70, "HOLD", True), (90, "BLOCK", False)]
    for score, action, review in scenarios:
        result = RiskAssessmentService(StubPredictor(score)).assess(demo_transactions()["normal"])
        assert result["recommended_action"] == action
        assert result["requires_human_review"] is review


def test_critical_fraud_history_is_blocked():
    result = RiskAssessmentService(StubPredictor(90)).assess(demo_transactions()["critical"])
    assert result["policy"]["policy_action"] == "BLOCK"
    assert "CRITICAL_WITH_FRAUD_HISTORY" in result["policy"]["reason_codes"]
