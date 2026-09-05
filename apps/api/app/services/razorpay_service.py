"""Razorpay Test Mode client service (Phase 6).

Server-side only. Responsibilities:
- create Razorpay Test Mode orders (REST API, basic auth)
- verify payment checkout signatures (HMAC-SHA256, per Razorpay spec)
- verify webhook signatures (HMAC-SHA256 over the raw body)
- return typed results and translate provider errors into safe exceptions

Secrets (key secret / webhook secret) never leave this module's call
boundary and are never included in error messages or logs.

When Razorpay Test Mode credentials are not configured, the service runs
in clearly-labeled "local-demo" mode: orders are generated locally with
the same identifier format and signatures use the same HMAC-SHA256 scheme
with a local demo secret, so the verification code path is identical.
This mode exists so the Buildathon demo works offline with synthetic
data; it never contacts Razorpay and never fabricates provider responses
when real credentials are available.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any

import httpx

from apps.api.app.core.config import settings

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
_TIMEOUT_SECONDS = 15.0


class RazorpayError(Exception):
    """Safe Razorpay integration error. Never contains secrets."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RazorpayUnavailableError(RazorpayError):
    """The Razorpay API could not be reached."""


@dataclass(frozen=True)
class RazorpayOrder:
    order_id: str
    amount: int
    currency: str
    status: str
    mode: str  # "razorpay-test" | "local-demo"
    raw: dict[str, Any] | None = None


def is_test_mode_configured() -> bool:
    """True when real Razorpay Test Mode credentials are present."""
    return bool(settings.razorpay_key_id and settings.razorpay_key_secret)


def is_webhook_configured() -> bool:
    return bool(settings.razorpay_webhook_secret)


def public_key_id() -> str | None:
    """The public Key ID is the only credential safe for the frontend."""
    return settings.razorpay_key_id or None


def _signing_secret() -> str:
    """Secret used for payment signature verification.

    Real Test Mode uses the key secret; local demo mode uses the demo
    secret. Both flow through the identical verification code path.
    """
    if is_test_mode_configured():
        return settings.razorpay_key_secret
    return settings.razorpay_demo_secret


def compute_payment_signature(order_id: str, payment_id: str) -> str:
    """HMAC-SHA256 hex digest of ``order_id|payment_id`` (Razorpay spec).

    Used to sign local-demo payments and to verify real ones.
    """
    message = f"{order_id}|{payment_id}".encode()
    return hmac.new(_signing_secret().encode(), message, hashlib.sha256).hexdigest()


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Constant-time comparison of the expected vs supplied signature."""
    expected = compute_payment_signature(order_id, payment_id)
    return hmac.compare_digest(expected, (signature or "").strip())


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """HMAC-SHA256 over the exact raw request body (Razorpay webhook spec).

    The body must not be parsed before this check.
    """
    secret = settings.razorpay_webhook_secret or settings.razorpay_demo_secret
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, (signature or "").strip())


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/json"}


def _auth() -> tuple[str, str]:
    return (settings.razorpay_key_id, settings.razorpay_key_secret)


def create_order(amount_minor: int, currency: str, receipt: str, notes: dict[str, str] | None = None) -> RazorpayOrder:
    """Create a Razorpay Test Mode order.

    ``amount_minor`` is in the smallest currency unit (paise for INR).
    Raises RazorpayUnavailableError when the API cannot be reached and
    RazorpayError for provider-rejected requests.
    """
    if not is_test_mode_configured():
        # Local demo mode: same identifier format, no provider call.
        order_id = f"order_demo{secrets.token_hex(8)}"
        return RazorpayOrder(
            order_id=order_id,
            amount=amount_minor,
            currency=currency,
            status="created",
            mode="local-demo",
            raw={"id": order_id, "amount": amount_minor, "currency": currency, "receipt": receipt, "status": "created"},
        )

    payload: dict[str, Any] = {
        "amount": amount_minor,
        "currency": currency,
        "receipt": receipt,
        "notes": notes or {},
    }
    try:
        response = httpx.post(
            f"{RAZORPAY_API_BASE}/orders",
            json=payload,
            auth=_auth(),
            headers=_headers(),
            timeout=_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError:
        raise RazorpayUnavailableError("Payment provider is unavailable. The payment was not created.")

    if response.status_code >= 400:
        # Surface only a safe, generic provider error (no secrets, no raw body).
        raise RazorpayError(
            "Payment provider rejected the order request.",
            status_code=response.status_code,
        )

    data = response.json()
    return RazorpayOrder(
        order_id=str(data["id"]),
        amount=int(data["amount"]),
        currency=str(data["currency"]),
        status=str(data.get("status", "created")),
        mode="razorpay-test",
        raw=data,
    )


def fetch_order(order_id: str) -> dict[str, Any]:
    """Fetch order details from Razorpay. Used for reconciliation."""
    if not is_test_mode_configured():
        raise RazorpayError("Razorpay credentials are not configured.", status_code=503)
    try:
        response = httpx.get(
            f"{RAZORPAY_API_BASE}/orders/{order_id}",
            auth=_auth(),
            headers=_headers(),
            timeout=_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError:
        raise RazorpayUnavailableError("Payment provider is unavailable.")
    if response.status_code >= 400:
        raise RazorpayError("Payment provider rejected the order lookup.", status_code=response.status_code)
    return response.json()