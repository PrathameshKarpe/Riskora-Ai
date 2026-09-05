"""Phase 6 payment schemas (Razorpay Test Mode integration)."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Scenario = Literal["LOW", "HIGH", "CRITICAL"]


class PaymentOrderRequest(BaseModel):
    """Create a Razorpay Test Mode order for a synthetic demo payment.

    Amount is in the smallest currency unit (paise for INR), matching the
    Razorpay API convention.
    """

    amount: int = Field(gt=0, le=100_000_000, description="Amount in smallest currency unit (paise)")
    currency: str = Field(default="INR", min_length=3, max_length=8)
    scenario: Scenario = Field(
        default="LOW",
        description="Synthetic demo scenario (LOW/HIGH/CRITICAL) that seeds the risk context. "
        "Clearly labeled synthetic test data — not real fraud.",
    )


class PaymentOrderResponse(BaseModel):
    """Frontend-safe order details. Contains no secrets."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    razorpay_order_id: str
    amount: int
    currency: str
    key_id: str | None = Field(
        default=None,
        description="Public Razorpay Key ID for Checkout. None in local demo mode.",
    )
    mode: Literal["razorpay-test", "local-demo"]
    scenario: str | None = None


class PaymentVerifyRequest(BaseModel):
    """Checkout callback values. The browser response is never trusted:
    the backend verifies the HMAC signature server-side."""

    razorpay_order_id: str = Field(min_length=1, max_length=64)
    razorpay_payment_id: str = Field(min_length=1, max_length=64)
    razorpay_signature: str = Field(min_length=1, max_length=256)


class PaymentResponse(BaseModel):
    """Full payment + risk state. Payment status, risk status, and decision
    are separate state machines (Phase 6 Step 14).

    The ORM column is ``amount_minor``; we expose it as ``amount`` in the
    API because that is what the frontend and tests reference.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    transaction_id: int
    razorpay_order_id: str
    razorpay_payment_id: str | None
    # Exposed as "amount" — mapped from the ORM field "amount_minor".
    amount: int = Field(alias="amount_minor", serialization_alias="amount")
    currency: str
    payment_status: str
    risk_status: str
    decision: str | None
    scenario: str | None
    mode: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _normalise_amount(cls, data: Any) -> Any:
        """Accept both ``amount`` and ``amount_minor`` from any source.

        When built from an ORM model ``from_attributes=True`` already maps
        attribute names, so we only need to handle plain dict inputs where
        ``amount_minor`` might arrive under either name.
        """
        if isinstance(data, dict):
            if "amount_minor" in data and "amount" not in data:
                data = {**data, "amount": data["amount_minor"]}
        return data


class PaymentVerifyResponse(BaseModel):
    verified: bool
    payment: PaymentResponse
    investigation_triggered: bool


class WebhookAck(BaseModel):
    received: bool
    duplicate: bool = False
    event_id: str | None = None


class PaymentConfigResponse(BaseModel):
    """Public payment configuration. Only the public Key ID may be exposed."""

    mode: Literal["razorpay-test", "local-demo"]
    key_id: str | None = None
    webhook_configured: bool
