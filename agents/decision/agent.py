"""Bounded recommendation agent. It has no payment execution capability."""

from typing import Any, Mapping


def run_decision_agent(
    ml_assessment: Mapping[str, Any],
    behavioral_findings: Mapping[str, Any],
    investigation_findings: Mapping[str, Any],
    evidence: list[Mapping[str, Any]],
    llm_available: bool = True,
) -> dict[str, Any]:
    if not llm_available:
        return {
            "agent": "decision_agent", "status": "completed", "decision_status": "LLM_UNAVAILABLE",
            "recommendation": "HUMAN_REVIEW", "confidence": 0.0, "reason_codes": ["LLM_UNAVAILABLE"],
            "explanation": "Decision summarization is unavailable; deterministic policy evaluation must control the outcome.",
        }
    score = float(ml_assessment["risk_score"])
    severities = {finding.get("severity") for finding in behavioral_findings.get("findings", [])}
    recommendation = (
        "BLOCK" if score >= 85 or "CRITICAL" in severities
        else "HOLD" if score >= 60 or "HIGH" in severities
        else "REVIEW" if score >= 30 or "MEDIUM" in severities
        else "APPROVE"
    )
    reason_codes = [finding["signal"].upper() for finding in behavioral_findings.get("findings", []) if finding["severity"] in {"HIGH", "CRITICAL"}]
    confidence = min(0.99, 0.65 + 0.05 * len(evidence) + 0.03 * len(reason_codes))
    return {
        "agent": "decision_agent", "status": "completed", "decision_status": "COMPLETED",
        "recommendation": recommendation, "confidence": round(confidence, 2), "reason_codes": reason_codes,
        "explanation": "Recommendation is based on the ML assessment, structured behavioral findings, and retrieved evidence.",
    }
