"""Typed state shared by the Phase 3 investigation graph."""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, NotRequired, TypedDict


class AgentFinding(TypedDict):
    signal: str
    severity: str
    explanation: str
    value: NotRequired[Any]
    source: NotRequired[str]


class AgentResult(TypedDict):
    agent: str
    status: str
    summary: str
    findings: NotRequired[list[AgentFinding]]
    key_findings: NotRequired[list[str]]
    confidence: NotRequired[float]
    error: NotRequired[str]


class EvidenceItem(TypedDict):
    source: str
    section: str
    relevance_score: float
    content: str
    metadata: dict[str, Any]
    finding_supported: bool
    explanation: str


class AuditEvent(TypedDict):
    event: str
    timestamp: str
    details: dict[str, Any]


class InvestigationState(TypedDict):
    transaction: dict[str, Any]
    ml_assessment: NotRequired[dict[str, Any]]
    behavioral_findings: NotRequired[AgentResult]
    investigation_findings: NotRequired[AgentResult]
    evidence: NotRequired[list[EvidenceItem]]
    evidence_status: NotRequired[str]
    decision_recommendation: NotRequired[dict[str, Any]]
    policy_result: NotRequired[dict[str, Any]]
    audit_events: Annotated[list[AuditEvent], add]
    errors: Annotated[list[dict[str, str]], add]
    decision_status: NotRequired[str]
