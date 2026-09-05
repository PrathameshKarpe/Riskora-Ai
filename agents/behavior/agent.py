"""Behavior agent backed entirely by the Phase 2 behavior engine."""

from typing import Any, Mapping

from risk_engine.behavior import BehaviorEngine


def run_behavior_agent(transaction: Mapping[str, Any], engine: BehaviorEngine | None = None) -> dict[str, Any]:
    analysis = (engine or BehaviorEngine()).analyze(transaction)
    findings = [
        {
            "signal": signal["signal"],
            "severity": signal["severity"],
            "value": signal["value"],
            "explanation": signal["explanation"],
            "source": signal["source"],
        }
        for signal in analysis["signals"]
        if signal["severity"] in {"MEDIUM", "HIGH", "CRITICAL"}
    ]
    summary = "Multiple behavioral anomalies were detected." if findings else "No elevated behavioral anomalies were detected."
    return {"agent": "behavior_agent", "status": "completed", "findings": findings, "summary": summary}
