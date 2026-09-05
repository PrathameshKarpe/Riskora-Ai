"""Generate deterministic synthetic transactions for local demos and tests.

These rows are simulated and are not evidence of production model performance.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DATASET_COLUMNS = [
    "transaction_id",
    "amount",
    "currency",
    "payment_method",
    "merchant_category",
    "transaction_hour",
    "transaction_day",
    "transactions_last_5m",
    "transactions_last_hour",
    "transactions_last_24h",
    "avg_historical_amount",
    "failed_transaction_count",
    "account_age_days",
    "previous_fraud_history",
    "new_device",
    "device_change_frequency",
    "device_risk",
    "country_change",
    "impossible_travel",
    "is_fraud",
]


def generate_demo_transactions(rows: int = 2500, seed: int = 42) -> pd.DataFrame:
    """Return reproducible synthetic payment-risk data."""
    if rows < 20:
        raise ValueError("rows must be at least 20")

    rng = np.random.default_rng(seed)
    average = np.clip(rng.lognormal(mean=7.0, sigma=0.7, size=rows), 200, 50_000)
    amount = np.clip(average * rng.lognormal(mean=0.0, sigma=0.65, size=rows), 50, 250_000)
    new_device = rng.binomial(1, 0.12, rows)
    country_change = rng.binomial(1, 0.08, rows)
    impossible_travel = (country_change & (rng.random(rows) < 0.35)).astype(int)
    failed_attempts = rng.poisson(0.7, rows)
    velocity_5m = rng.poisson(1.0, rows)
    velocity_hour = velocity_5m + rng.poisson(2.0, rows)
    velocity_day = velocity_hour + rng.poisson(7.0, rows)
    previous_fraud = rng.binomial(1, 0.05, rows)
    device_risk = np.clip(0.15 * new_device + rng.normal(0.2, 0.12, rows), 0, 1)
    deviation = amount / average

    logit = (
        -4.2
        + 1.3 * (deviation > 3.0)
        + 1.0 * (deviation > 5.0)
        + 0.65 * (velocity_5m >= 4)
        + 0.45 * (velocity_hour >= 8)
        + 1.0 * new_device
        + 1.1 * impossible_travel
        + 0.55 * (failed_attempts >= 3)
        + 1.4 * previous_fraud
        + 0.8 * (device_risk > 0.65)
    )
    probability = 1 / (1 + np.exp(-logit))
    is_fraud = rng.binomial(1, probability)

    frame = pd.DataFrame(
        {
            "transaction_id": [f"demo-{index:06d}" for index in range(rows)],
            "amount": amount.round(2),
            "currency": rng.choice(["INR", "USD", "EUR"], rows, p=[0.75, 0.15, 0.10]),
            "payment_method": rng.choice(["card", "upi", "wallet", "netbanking"], rows),
            "merchant_category": rng.choice(["retail", "travel", "gaming", "utilities", "food"], rows),
            "transaction_hour": rng.integers(0, 24, rows),
            "transaction_day": rng.integers(0, 7, rows),
            "transactions_last_5m": velocity_5m,
            "transactions_last_hour": velocity_hour,
            "transactions_last_24h": velocity_day,
            "avg_historical_amount": average.round(2),
            "failed_transaction_count": failed_attempts,
            "account_age_days": rng.integers(1, 2_500, rows),
            "previous_fraud_history": previous_fraud,
            "new_device": new_device,
            "device_change_frequency": np.clip(rng.poisson(0.4, rows), 0, 8),
            "device_risk": device_risk.round(4),
            "country_change": country_change,
            "impossible_travel": impossible_travel,
            "is_fraud": is_fraud,
        }
    )
    return frame[DATASET_COLUMNS]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("ml/data/demo_transactions.csv"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generate_demo_transactions(args.rows, args.seed).to_csv(args.output, index=False)
    print(f"Wrote {args.rows} simulated transactions to {args.output}")


if __name__ == "__main__":
    main()
