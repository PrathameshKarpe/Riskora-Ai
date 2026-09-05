"""Train and evaluate Riskora transaction-fraud models.

Usage:
    python -m ml.training.train
    python -m ml.training.train --input path/to/transactions.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from ml.data.generate_demo import generate_demo_transactions
from ml.features.pipeline import build_model_pipeline, clean_frame, split_features_target

RANDOM_STATE = 42


def _evaluate(model, features: pd.DataFrame, target: pd.Series) -> dict[str, Any]:
    probabilities = model.predict_proba(features)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(target, predictions, labels=[0, 1]).ravel()
    fraud_count = int(target.sum())
    average_fraud_amount = float(features.loc[target == 1, "amount"].mean()) if fraud_count else 0.0
    return {
        "precision": float(precision_score(target, predictions, zero_division=0)),
        "recall": float(recall_score(target, predictions, zero_division=0)),
        "f1": float(f1_score(target, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(target, probabilities)),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "fraud_detection_rate": float(tp / fraud_count) if fraud_count else 0.0,
        "confusion_matrix": {"true_negative": int(tn), "false_positive": int(fp), "false_negative": int(fn), "true_positive": int(tp)},
        "business_metrics": {
            "false_positive_cost": float(fp * 2.0),
            "estimated_prevented_loss": float(tp * average_fraud_amount),
            "review_volume": int(predictions.sum()),
            "cost_of_missed_fraud": float(fn * average_fraud_amount),
            "assumptions": "FP cost=2.0 currency units; prevented/missed loss uses mean fraud amount in holdout.",
        },
    }


def train(input_path: Path | None = None, artifact_dir: Path = Path("ml/models")) -> dict[str, Any]:
    frame = pd.read_csv(input_path) if input_path else generate_demo_transactions()
    frame = clean_frame(frame)
    features, target = split_features_target(frame)
    train_features, holdout_features, train_target, holdout_target = train_test_split(
        features, target, test_size=0.4, stratify=target, random_state=RANDOM_STATE
    )
    validation_features, test_features, validation_target, test_target = train_test_split(
        holdout_features, holdout_target, test_size=0.5, stratify=holdout_target, random_state=RANDOM_STATE
    )

    logistic_pipeline = build_model_pipeline(
        LogisticRegression(max_iter=1_000, class_weight="balanced", random_state=RANDOM_STATE)
    )
    minimum_class_count = int(train_target.value_counts().min())
    logistic_model = (
        CalibratedClassifierCV(estimator=logistic_pipeline, method="sigmoid", cv=min(3, minimum_class_count))
        if minimum_class_count >= 2
        else logistic_pipeline
    )
    candidates = {
        "logistic-regression": logistic_model,
        "random-forest": build_model_pipeline(
            RandomForestClassifier(
                n_estimators=200, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
            )
        ),
    }
    evaluations: dict[str, Any] = {}
    for name, model in candidates.items():
        model.fit(train_features, train_target)
        evaluations[name] = {"validation": _evaluate(model, validation_features, validation_target)}

    selected_name = max(
        evaluations,
        key=lambda name: (evaluations[name]["validation"]["f1"], evaluations[name]["validation"]["roc_auc"]),
    )
    selected_model = candidates[selected_name]
    combined_features = pd.concat([train_features, validation_features])
    combined_target = pd.concat([train_target, validation_target])
    selected_model.fit(combined_features, combined_target)
    evaluations[selected_name]["test"] = _evaluate(selected_model, test_features, test_target)
    metadata = {
        "model_version": f"riskora-{selected_name}-v2",
        "selected_model": selected_name,
        "dataset": "synthetic-demo" if input_path is None else str(input_path),
        "random_state": RANDOM_STATE,
        "split": {"train": 0.6, "validation": 0.2, "test": 0.2},
        "dataset_shape": {"rows": int(frame.shape[0]), "columns": int(frame.shape[1])},
        "class_distribution": {"non_fraud": int((target == 0).sum()), "fraud": int((target == 1).sum())},
        "target": "is_fraud",
        "features": list(features.columns),
        "evaluations": evaluations,
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": selected_model, "metadata": metadata}, artifact_dir / "risk_model.joblib")
    (artifact_dir / "metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="CSV matching the documented transaction schema")
    parser.add_argument("--artifact-dir", type=Path, default=Path("ml/models"))
    args = parser.parse_args()
    metadata = train(args.input, args.artifact_dir)
    selected = metadata["evaluations"][metadata["selected_model"]]["test"]
    print(json.dumps({"selected_model": metadata["selected_model"], "metrics": selected}, indent=2))


if __name__ == "__main__":
    main()
