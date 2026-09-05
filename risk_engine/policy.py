"""Configurable, deterministic policy decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ml.inference.predict import risk_level


@dataclass(frozen=True)
class PolicyConfig:
    low_max: float = 30.0
    medium_max: float = 60.0
    high_max: float = 85.0
    policy_version: str = "policy-v1"


class PolicyEngine:
    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()

    def evaluate(
        self,
        risk_score: float,
        behavioral_signals: Iterable[Mapping[str, Any]] = (),
        recommendation: str | None = None,
        evidence_available: bool = True,
    ) -> dict[str, Any]:
        level = self._risk_level(risk_score)
        signals = list(behavioral_signals)
        names = {signal.get("signal") for signal in signals}
        reason_codes: list[str] = []
        explanation_parts: list[str] = []

        new_device_signal = next((signal for signal in signals if signal.get("signal") == "new_device"), {})
        amount_signal = next((signal for signal in signals if signal.get("signal") == "amount_anomaly"), {})
        if new_device_signal.get("severity") in {"HIGH", "CRITICAL"} and amount_signal.get("severity") in {"HIGH", "CRITICAL"}:
            reason_codes.append("NEW_DEVICE_HIGH_AMOUNT")
            explanation_parts.append("New device combined with an elevated amount requires additional control.")
        if "transaction_velocity" in names and "failed_payment_attempts" in names:
            velocity = next((signal for signal in signals if signal.get("signal") == "transaction_velocity"), {})
            failed = next((signal for signal in signals if signal.get("signal") == "failed_payment_attempts"), {})
            if velocity.get("severity") in {"HIGH", "CRITICAL"} and failed.get("severity") in {"HIGH", "CRITICAL"}:
                level = max_level(level, "HIGH")
                reason_codes.append("HIGH_VELOCITY_FAILED_ATTEMPTS")
                explanation_parts.append("High velocity combined with failed attempts forces human review.")
        fraud_history = next((signal for signal in signals if signal.get("signal") == "previous_fraud_association"), {})
        if level == "CRITICAL" and fraud_history.get("severity") in {"HIGH", "CRITICAL"}:
            reason_codes.append("CRITICAL_WITH_FRAUD_HISTORY")
            explanation_parts.append("Critical risk with a previous fraud association is blocked.")

        actions = {"LOW": "APPROVE", "MEDIUM": "REVIEW", "HIGH": "HUMAN_REVIEW", "CRITICAL": "BLOCK"}
        recommended_actions = {"LOW": "APPROVE", "MEDIUM": "REVIEW", "HIGH": "HOLD", "CRITICAL": "BLOCK"}
        policy_action = actions[level]
        if not evidence_available and level in {"MEDIUM", "HIGH"}:
            policy_action = "HUMAN_REVIEW"
            reason_codes.append("EVIDENCE_UNAVAILABLE")
            explanation_parts.append("Evidence is unavailable, so human review is required.")
        if recommendation and recommendation.upper() != recommended_actions[level]:
            policy_action = "HUMAN_REVIEW"
            reason_codes.append("RECOMMENDATION_CONFLICT")
            explanation_parts.append("The external recommendation conflicts with the deterministic policy result.")

        if not explanation_parts:
            explanation_parts.append(f"Risk score {risk_score:.2f} falls in the {level} policy band.")
        return {
            "risk_level": level,
            "recommended_action": recommended_actions[level],
            "policy_action": policy_action,
            "policy_version": self.config.policy_version,
            "reason_codes": reason_codes,
            "explanation": " ".join(explanation_parts),
            "requires_human_review": policy_action == "HUMAN_REVIEW",
        }

    def _risk_level(self, score: float) -> str:
        if score < self.config.low_max:
            return "LOW"
        if score < self.config.medium_max:
            return "MEDIUM"
        if score < self.config.high_max:
            return "HIGH"
        return "CRITICAL"


def max_level(current: str, candidate: str) -> str:
    order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    return candidate if order[candidate] > order[current] else current
