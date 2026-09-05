"""Structured investigation coordination without invented facts."""

from typing import Any, Mapping


def run_investigation_agent(ml_assessment: Mapping[str, Any], behavioral_findings: Mapping[str, Any]) -> dict[str, Any]:
    findings = list(behavioral_findings.get("findings", []))
    key_findings = [finding["signal"] for finding in findings]
    if not key_findings:
        summary = "No elevated behavioral findings were supplied; ML assessment was reviewed."
    else:
        summary = "Transaction shows multiple independent indicators of elevated risk."
    confidence = min(0.99, 0.55 + 0.08 * len(key_findings) + (0.1 if ml_assessment.get("risk_level") in {"HIGH", "CRITICAL"} else 0))
    return {
        "agent": "investigation_agent",
        "status": "completed",
        "summary": summary,
        "key_findings": key_findings,
        "confidence": round(confidence, 2),
        "missing_information": [finding["signal"] for finding in findings if finding.get("value") == "unavailable"],
    }
