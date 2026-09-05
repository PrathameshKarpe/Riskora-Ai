from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AgentResponse(BaseModel):
    agent_name: str
    status: str
    finding: dict[str, Any]
    confidence: float | None


class EvidenceResponse(BaseModel):
    source: str
    section: str
    content: str
    relevance_score: float
    metadata: dict[str, Any]


class DecisionResponse(BaseModel):
    recommendation: str
    policy_action: str
    requires_human_review: bool
    reason_codes: list[str]
    explanation: str


class InvestigationResponse(BaseModel):
    investigation_id: int
    transaction_id: int
    status: str
    summary: str | None
    confidence: float | None
    started_at: datetime
    completed_at: datetime | None
    risk: dict[str, Any] | None
    behavioral_signals: list[dict[str, Any]]
    agents: list[AgentResponse]
    evidence: list[EvidenceResponse]
    decision: DecisionResponse | None
