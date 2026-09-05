from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=128)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=8)
    merchant: str = Field(min_length=1, max_length=255)
    payment_method: str = Field(min_length=1, max_length=32)
    device_id: str | None = Field(default=None, max_length=128)
    location: str | None = Field(default=None, max_length=128)
    risk_context: dict = Field(default_factory=dict)


class TransactionResponse(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime
