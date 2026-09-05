"""Normalized persistence models for transactions and investigations."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base

JsonType = JSON().with_variant(JSONB, "postgresql")


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="RISK_ANALYST")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8))
    merchant: Mapped[str] = mapped_column(String(255))
    payment_method: Mapped[str] = mapped_column(String(32))
    device_id: Mapped[str | None] = mapped_column(String(128))
    location: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="RECEIVED", index=True)
    risk_context: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    user: Mapped[User | None] = relationship(back_populates="transactions")
    assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")
    investigations: Mapped[list["Investigation"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")
    policy_decisions: Mapped[list["PolicyDecision"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")
    reviews: Mapped[list["HumanReview"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    model_version: Mapped[str] = mapped_column(String(64))
    fraud_probability: Mapped[float] = mapped_column(Float)
    ml_risk_score: Mapped[float] = mapped_column(Float)
    behavioral_risk: Mapped[str] = mapped_column(String(16))
    final_risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    transaction: Mapped[Transaction] = relationship(back_populates="assessments")


class Investigation(Base):
    __tablename__ = "investigations"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    transaction: Mapped[Transaction] = relationship(back_populates="investigations")
    findings: Mapped[list["AgentFinding"]] = relationship(cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship(cascade="all, delete-orphan")


class AgentFinding(Base):
    __tablename__ = "agent_findings"
    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    finding: Mapped[dict[str, Any]] = mapped_column(JsonType)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    source: Mapped[str] = mapped_column(String(255))
    section: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    relevance_score: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    policy_version: Mapped[str] = mapped_column(String(64))
    ai_recommendation: Mapped[str] = mapped_column(String(32))
    policy_action: Mapped[str] = mapped_column(String(32))
    requires_human_review: Mapped[bool]
    reason_codes: Mapped[list[str]] = mapped_column(JsonType)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    transaction: Mapped[Transaction] = relationship(back_populates="policy_decisions")


class HumanReview(Base):
    __tablename__ = "human_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    transaction: Mapped[Transaction] = relationship(back_populates="reviews")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    transaction: Mapped[Transaction] = relationship(back_populates="audit_events")


class Payment(Base):
    """Razorpay Test Mode payment linked to a Riskora transaction.

    Payment status, risk status, and the risk decision are intentionally
    separate state machines (Phase 6 Step 14): an AUTHORIZED payment can be
    HIGH risk with a HUMAN_REVIEW decision, and none of these overwrite
    each other.
    """
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), unique=True, index=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), index=True)
    # Amount in the smallest currency unit (paise for INR), per Razorpay.
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8))
    # Payment lifecycle: CREATED -> AUTHORIZED -> CAPTURED | FAILED
    payment_status: Mapped[str] = mapped_column(String(16), default="CREATED", index=True)
    # Risk lifecycle: UNASSESSED -> LOW | MEDIUM | HIGH | CRITICAL
    risk_status: Mapped[str] = mapped_column(String(16), default="UNASSESSED", index=True)
    # Decision lifecycle: None -> APPROVE | REVIEW | HOLD | BLOCK
    decision: Mapped[str | None] = mapped_column(String(16))
    # Demo scenario label (LOW/HIGH/CRITICAL) for synthetic Buildathon data.
    scenario: Mapped[str | None] = mapped_column(String(16))
    # Provider integration mode: "razorpay-test" or "local-demo".
    mode: Mapped[str] = mapped_column(String(16), default="local-demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    transaction: Mapped[Transaction] = relationship()


class WebhookEvent(Base):
    """Received Razorpay webhook events, stored for idempotency and audit.

    The provider event id is unique: duplicate deliveries are detected and
    acknowledged without reprocessing.
    """
    __tablename__ = "webhook_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    signature_valid: Mapped[bool]
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


Index("ix_transactions_status_created", Transaction.status, Transaction.created_at)
