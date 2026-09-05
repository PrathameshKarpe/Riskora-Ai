from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_version: str
    fraud_probability: float
    ml_risk_score: float
    behavioral_risk: str
    final_risk_score: float
    risk_level: str
    created_at: datetime
