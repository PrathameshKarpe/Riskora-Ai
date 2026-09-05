"""Validated feature schema and sklearn preprocessing for payment transactions."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET_COLUMN = "is_fraud"
ID_COLUMNS = ["transaction_id"]
CATEGORICAL_FEATURES = ["currency", "payment_method", "merchant_category"]
NUMERIC_FEATURES = [
    "amount", "transaction_hour", "transaction_day", "transactions_last_5m",
    "transactions_last_hour", "transactions_last_24h", "avg_historical_amount",
    "failed_transaction_count", "account_age_days", "previous_fraud_history",
    "new_device", "device_change_frequency", "device_risk", "country_change",
    "impossible_travel",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def validate_frame(frame: pd.DataFrame, require_target: bool = True) -> None:
    required = set(FEATURE_COLUMNS)
    if require_target:
        required.add(TARGET_COLUMN)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required transaction columns: {', '.join(missing)}")
    if frame[FEATURE_COLUMNS].isnull().any().any():
        raise ValueError("Transaction features must not contain null values")
    if require_target and not set(frame[TARGET_COLUMN].unique()).issubset({0, 1}):
        raise ValueError("is_fraud must contain only 0 or 1")


def clean_frame(frame: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    """Normalize types and remove duplicate transaction records.

    Invalid or incomplete rows are rejected rather than silently imputed.
    """
    cleaned = frame.copy()
    validate_frame(cleaned, require_target=require_target)
    if "transaction_id" in cleaned:
        cleaned = cleaned.drop_duplicates(subset=["transaction_id"], keep="first")
    for column in NUMERIC_FEATURES + ([TARGET_COLUMN] if require_target else []):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    for column in CATEGORICAL_FEATURES:
        cleaned[column] = cleaned[column].astype("string").str.strip()
    validate_frame(cleaned, require_target=require_target)
    return cleaned


def split_features_target(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    cleaned = clean_frame(frame)
    return cleaned[FEATURE_COLUMNS].copy(), cleaned[TARGET_COLUMN].astype(int).copy()


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ],
        remainder="drop",
    )


def build_model_pipeline(estimator) -> Pipeline:
    return Pipeline([("features", build_preprocessor()), ("model", estimator)])
