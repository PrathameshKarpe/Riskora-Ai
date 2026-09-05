from typing import Any, Mapping


def get_transaction_details(transaction: Mapping[str, Any]) -> dict[str, Any]:
    return {"transaction": dict(transaction), "source": "transaction-input"}
