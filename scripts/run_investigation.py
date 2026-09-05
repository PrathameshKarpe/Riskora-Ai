"""Run the three synthetic Riskora investigation scenarios."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.predict import TransactionPredictor
from risk_engine.demo_transactions import demo_transactions
from agents.graph.workflow import run_investigation


def main() -> None:
    predictor = TransactionPredictor()
    for name, transaction in demo_transactions().items():
        result = run_investigation(transaction, predictor, audit_path=f"audit/{name}.json")
        print(f"\n{name.upper()} ({transaction['transaction_id']})")
        for label in ["TRANSACTION_RECEIVED", "ML_RISK_CALCULATED", "BEHAVIOR_ANALYSIS_COMPLETED", "INVESTIGATION_STARTED", "EVIDENCE_RETRIEVED", "DECISION_GENERATED", "POLICY_EVALUATED", "AUDIT_RECORDED"]:
            print(f"[{'x' if any(event['event'] == label for event in result['audit_events']) else ' '}] {label}")
        policy = result.get("policy_result", {})
        print(f"Final: Risk Score {policy.get('risk_level')} / {result.get('ml_assessment', {}).get('risk_score')} -> {policy.get('recommended_action')} / {policy.get('policy_action')}")


if __name__ == "__main__":
    main()
