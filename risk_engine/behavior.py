"""Deterministic behavioral risk signals from available transaction context."""

from __future__ import annotations

from typing import Any, Mapping


SEVERITY_SCORE = {"LOW": 10, "MEDIUM": 40, "HIGH": 75, "CRITICAL": 100}


def _signal(name: str, severity: str, value: Any, explanation: str, source: str = "dataset-derived") -> dict[str, Any]:
    return {
        "signal": name,
        "severity": severity,
        "value": value,
        "explanation": explanation,
        "source": source,
        "score": SEVERITY_SCORE[severity],
    }


def _unavailable(name: str, explanation: str) -> dict[str, Any]:
    return _signal(name, "LOW", "unavailable", explanation, "future-production-signal")


class BehaviorEngine:
    """Calculate explainable behavioral signals without an LLM or external state."""

    def analyze(self, transaction: Mapping[str, Any]) -> dict[str, Any]:
        signals: list[dict[str, Any]] = []
        amount = transaction.get("amount")
        average = transaction.get("avg_historical_amount")
        ratio = None
        if amount is not None and average is not None and float(average) > 0:
            ratio = float(amount) / float(average)
            severity = "LOW" if ratio < 1.5 else "MEDIUM" if ratio < 3 else "HIGH"
            signals.append(_signal(
                "amount_anomaly", severity, f"{ratio:.1f}x normal amount",
                "Transaction amount is significantly above the customer's historical average." if severity == "HIGH" else "Transaction amount is within or moderately above the customer's historical range.",
            ))
            signals.append(_signal(
                "historical_amount_deviation", severity, round(ratio, 2),
                "Historical deviation is calculated as amount divided by the supplied average historical amount.",
            ))
        else:
            signals.extend([
                _unavailable("amount_anomaly", "Amount and historical average are required for this signal."),
                _unavailable("historical_amount_deviation", "Historical average amount is unavailable."),
            ])

        velocity = transaction.get("transactions_last_5m")
        if velocity is None:
            signals.append(_unavailable("transaction_velocity", "Recent transaction velocity is unavailable."))
        else:
            velocity = int(velocity)
            severity = "HIGH" if velocity >= 4 else "MEDIUM" if velocity >= 2 else "LOW"
            signals.append(_signal(
                "transaction_velocity", severity, f"{velocity} transactions in 5 minutes",
                "Recent transaction velocity is unusually high." if severity != "LOW" else "Recent transaction velocity is within the demo baseline.",
            ))

        new_device = transaction.get("new_device")
        if new_device is None:
            signals.append(_unavailable("new_device", "Device history is unavailable in this transaction."))
        else:
            severity = "HIGH" if bool(new_device) else "LOW"
            signals.append(_signal(
                "new_device", severity, "new device" if bool(new_device) else "known device",
                "The transaction uses a device not previously associated with the customer." if bool(new_device) else "The device is known for this customer.",
            ))

        country_change = transaction.get("country_change")
        if country_change is None:
            signals.append(_unavailable("new_location", "Location history is unavailable in this transaction."))
        else:
            severity = "HIGH" if bool(country_change) else "LOW"
            signals.append(_signal(
                "new_location", severity, "new location" if bool(country_change) else "known location",
                "The transaction location differs from the customer's known location." if bool(country_change) else "The location is known for this customer.",
            ))

        hour = transaction.get("transaction_hour")
        if hour is None:
            signals.append(_unavailable("unusual_transaction_time", "Transaction time is unavailable."))
        else:
            hour = int(hour)
            severity = "MEDIUM" if hour < 5 or hour >= 23 else "LOW"
            signals.append(_signal(
                "unusual_transaction_time", severity, f"hour {hour:02d}:00",
                "The transaction occurred during an unusual overnight hour." if severity == "MEDIUM" else "The transaction time is within the normal demo window.",
            ))

        failed = transaction.get("failed_transaction_count")
        if failed is None:
            signals.append(_unavailable("failed_payment_attempts", "Failed payment history is unavailable."))
        else:
            failed = int(failed)
            severity = "HIGH" if failed >= 3 else "MEDIUM" if failed >= 1 else "LOW"
            signals.append(_signal(
                "failed_payment_attempts", severity, f"{failed} failed attempts",
                "Multiple failed payment attempts preceded this transaction." if severity == "HIGH" else "Failed payment activity is limited or absent.",
            ))

        previous_fraud = transaction.get("previous_fraud_history")
        if previous_fraud is None:
            signals.append(_unavailable("previous_fraud_association", "Historical fraud association is unavailable."))
        else:
            severity = "CRITICAL" if bool(previous_fraud) else "LOW"
            signals.append(_signal(
                "previous_fraud_association", severity, "associated" if bool(previous_fraud) else "none detected",
                "The account has a previous fraud association." if bool(previous_fraud) else "No previous fraud association is present in the supplied data.",
            ))

        impossible_travel = transaction.get("impossible_travel")
        if impossible_travel is None:
            signals.append(_unavailable("impossible_travel", "Sufficient location and timestamp history is unavailable."))
        else:
            severity = "CRITICAL" if bool(impossible_travel) else "LOW"
            signals.append(_signal(
                "impossible_travel", severity, "detected" if bool(impossible_travel) else "not detected",
                "Locations and timestamps imply impossible travel." if bool(impossible_travel) else "No impossible-travel indicator is present in the supplied demo data.",
            ))

        available = [signal for signal in signals if signal["source"] == "dataset-derived"]
        behavior_score = max((signal["score"] for signal in available), default=0)
        return {
            "behavioral_risk": risk_level(behavior_score),
            "behavioral_score": behavior_score,
            "signals": signals,
            "available_signal_count": len(available),
        }


def risk_level(score: float) -> str:
    if score < 30:
        return "LOW"
    if score < 60:
        return "MEDIUM"
    if score < 85:
        return "HIGH"
    return "CRITICAL"
