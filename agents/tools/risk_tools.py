from typing import Any, Mapping


def get_ml_risk_assessment(assessment: Mapping[str, Any]) -> dict[str, Any]:
    return {"ml_assessment": dict(assessment), "source": "trained-model-artifact"}


def get_behavioral_signals(behavioral_findings: Mapping[str, Any]) -> dict[str, Any]:
    return {"behavioral_findings": dict(behavioral_findings), "source": "phase-2-behavior-engine"}
