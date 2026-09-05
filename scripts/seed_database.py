"""Seed deterministic synthetic transactions into configured database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.app.core.config import settings
from apps.api.app.db.session import make_session_factory
from apps.api.app.db.models import Transaction, User
from apps.api.app.schemas.transaction import TransactionCreate
from apps.api.app.services.transaction_service import create_transaction
from risk_engine.demo_transactions import demo_transactions


def main():
    db = make_session_factory(settings.database_url)()
    try:
        user = db.query(User).filter_by(email="demo@riskora.local").first()
        if not user:
            user = User(email="demo@riskora.local", role="ADMIN")
            db.add(user); db.commit(); db.refresh(user)
        for scenario, transaction in demo_transactions().items():
            external_id = transaction["transaction_id"]
            if not db.query(Transaction).filter_by(external_id=external_id).first():
                context = {key: value for key, value in transaction.items() if key not in {"transaction_id", "amount", "currency", "payment_method"}}
                create_transaction(db, TransactionCreate(external_id=external_id, amount=transaction["amount"], currency=transaction["currency"], merchant=f"Synthetic {scenario}", payment_method=transaction["payment_method"], device_id=f"demo-device-{scenario}", location="Demo City", risk_context=context))
        print("Seeded deterministic synthetic demo transactions.")
    finally:
        db.close()

if __name__ == "__main__": main()
