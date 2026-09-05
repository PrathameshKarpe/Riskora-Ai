"""Load the trained artifact and score one payment transaction."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

from ml.features.pipeline import validate_frame


class TransactionPredictor:
    def __init__(self, artifact_path: str | Path = "ml/models/risk_model.joblib") -> None:
        artifact = joblib.load(artifact_path)
        self._model = artifact["model"]
        self.metadata = artifact["metadata"]

    def predict_transaction(self, transaction: Mapping[str, Any]) -> dict[str, Any]:
        frame = pd.DataFrame([dict(transaction)])
        validate_frame(frame, require_target=False)
        probability = float(self._model.predict_proba(frame)[:, 1].item())
        risk_score = round(probability * 100, 2)
        return {
            "fraud_probability": round(probability, 6),
            "risk_score": risk_score,
            "risk_level": risk_level(risk_score),
            "model_version": self.metadata["model_version"],
        }


def risk_level(risk_score: float) -> str:
    if risk_score < 30:
        return "LOW"
    if risk_score < 60:
        return "MEDIUM"
    if risk_score < 85:
        return "HIGH"
    return "CRITICAL"


def predict_transaction(transaction: Mapping[str, Any], artifact_path: str | Path = "ml/models/risk_model.joblib") -> dict[str, Any]:
    return TransactionPredictor(artifact_path).predict_transaction(transaction)
