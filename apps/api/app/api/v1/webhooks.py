"""Phase 6 Razorpay webhook endpoint.

Security model: the HMAC signature over the raw body IS the
authentication. There is deliberately no JWT dependency here — Razorpay
cannot obtain one. The raw request body is verified BEFORE parsing, and
duplicate deliveries are acknowledged idempotently.
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.schemas.payment import WebhookAck
from apps.api.app.services.payment_service import (
    WebhookVerificationError,
    handle_webhook,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/razorpay", response_model=WebhookAck)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Receive Razorpay Test Mode webhook events.

    - Reads the exact raw body (required for signature verification).
    - Verifies X-Razorpay-Signature before any parsing.
    - Deduplicates by the provider event id.
    - Returns quickly with an acknowledgment.
    """
    raw_body = await request.body()

    try:
        accepted, duplicate, event_id = handle_webhook(db, raw_body, x_razorpay_signature)
    except WebhookVerificationError as exc:
        # 400 tells Razorpay the delivery was rejected; do not leak details.
        raise HTTPException(status_code=400, detail={
            "code": "WEBHOOK_VERIFICATION_FAILED",
            "message": str(exc),
        })

    return WebhookAck(received=accepted, duplicate=duplicate, event_id=event_id)