import pandas as pd
import pytest

from ml.data.generate_demo import generate_demo_transactions
from ml.features.pipeline import FEATURE_COLUMNS, clean_frame, split_features_target, validate_frame


def test_demo_data_is_reproducible_and_has_both_classes():
    first = generate_demo_transactions(200, seed=7)
    second = generate_demo_transactions(200, seed=7)
    pd.testing.assert_frame_equal(first, second)
    assert set(first["is_fraud"]) == {0, 1}


def test_feature_split_excludes_identifier_and_target():
    features, target = split_features_target(generate_demo_transactions(100))
    assert list(features.columns) == FEATURE_COLUMNS
    assert "transaction_id" not in features
    assert target.name == "is_fraud"


def test_validation_rejects_missing_columns():
    frame = generate_demo_transactions(100).drop(columns=["device_risk"])
    with pytest.raises(ValueError, match="device_risk"):
        validate_frame(frame)


def test_cleaning_drops_duplicate_transaction_ids():
    frame = pd.concat([generate_demo_transactions(20), generate_demo_transactions(20)], ignore_index=True)
    cleaned = clean_frame(frame)
    assert len(cleaned) == 20
