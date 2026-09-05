from datetime import datetime
from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    id: int
    transaction_id: int
    decision: str
    reason: str
    reviewer_id: int | None
    created_at: datetime
