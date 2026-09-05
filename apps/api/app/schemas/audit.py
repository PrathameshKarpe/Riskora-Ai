from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AuditResponse(BaseModel):
    id: int
    transaction_id: int
    event_type: str
    actor: str
    payload: dict[str, Any]
    timestamp: datetime
