"""Unified ML, behavioral, and deterministic policy assessment."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from risk_engine.behavior import BehaviorEngine
from risk_engine.policy import PolicyEngine


class Predictor(Protocol):
    def predict_transaction(self, transaction: Mapping[str, Any]) -> dict[str, Any]: ...


class RiskAssessmentService:
    def __init__(
        self,
        predictor: Predictor,
        behavior_engine: BehaviorEngine | None = None,
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        self.predictor = predictor
        self.behavior_engine = behavior_engine or BehaviorEngine()
        self.policy_engine = policy_engine or PolicyEngine()

    def assess(self, transaction: Mapping[str, Any]) -> dict[str, Any]:
        ml_risk = self.predictor.predict_transaction(transaction)
        behavior = self.behavior_engine.analyze(transaction)
        final_score = max(ml_risk["risk_score"], behavior["behavioral_score"])
        policy = self.policy_engine.evaluate(final_score, behavior["signals"])
        risk_factors = [
            {
                "signal": signal["signal"],
                "severity": signal["severity"],
                "value": signal["value"],
                "explanation": signal["explanation"],
                "source": signal["source"],
            }
            for signal in behavior["signals"]
            if signal["severity"] in {"MEDIUM", "HIGH", "CRITICAL"}
        ]
        return {
            "transaction_id": transaction.get("transaction_id", "unknown"),
            "ml_risk": ml_risk,
            "ml_risk_score": ml_risk["risk_score"],
            "behavioral_risk": behavior["behavioral_risk"],
            "behavioral_score": behavior["behavioral_score"],
            "final_risk_score": final_score,
            "risk_level": policy["risk_level"],
            "recommended_action": policy["recommended_action"],
            "requires_human_review": policy["requires_human_review"],
            "risk_factors": risk_factors,
            "behavioral_analysis": behavior,
            "policy": policy,
            "explanation": f"ML risk {ml_risk['risk_score']:.2f} combined with behavioral risk {behavior['behavioral_score']:.2f}. {policy['explanation']}",
        }
