"""Phase 6 payment endpoints (Razorpay Test Mode).

Responses never contain secrets. Only the public Key ID is exposed, and
only when real Test Mode credentials are configured.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.core.security import current_principal
from apps.api.app.db.session import get_db
from apps.api.app.repositories import payment_repository
from apps.api.app.schemas.payment import (
    PaymentConfigResponse,
    PaymentOrderRequest,
    PaymentOrderResponse,
    PaymentResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
)
from apps.api.app.services import razorpay_service
from apps.api.app.services.payment_service import (
    PaymentVerificationError,
    create_test_order,
    payment_config,
    verify_payment,
)
from apps.api.app.services.razorpay_service import RazorpayError

router = APIRouter()


@router.get("/config", response_model=PaymentConfigResponse)
def get_payment_config():
    """Public payment configuration. Exposes only the public Key ID."""
    return PaymentConfigResponse(**payment_config())


@router.post("/orders", response_model=PaymentOrderResponse, status_code=201, dependencies=[Depends(current_principal)])
def create_order(payload: PaymentOrderRequest, db: Session = Depends(get_db)):
    """Create a Razorpay Test Mode order linked to a Riskora transaction."""
    try:
        payment = create_test_order(db, payload)
    except RazorpayError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail={
            "code": "PAYMENT_PROVIDER_ERROR",
            "message": str(exc),
        })
    return PaymentOrderResponse(
        transaction_id=payment.transaction_id,
        razorpay_order_id=payment.razorpay_order_id,
        amount=payment.amount_minor,
        currency=payment.currency,
        key_id=razorpay_service.public_key_id() if payment.mode == "razorpay-test" else None,
        mode="razorpay-test" if payment.mode == "razorpay-test" else "local-demo",
        scenario=payment.scenario,
    )


@router.post("/verify", response_model=PaymentVerifyResponse, dependencies=[Depends(current_principal)])
def verify(payload: PaymentVerifyRequest, db: Session = Depends(get_db)):
    """Verify the checkout signature server-side, then run Riskora."""
    try:
        payment, investigation_triggered = verify_payment(db, payload)
    except PaymentVerificationError as exc:
        raise HTTPException(status_code=400, detail={
            "code": "PAYMENT_VERIFICATION_FAILED",
            "message": str(exc),
        })
    return PaymentVerifyResponse(
        verified=True,
        payment=PaymentResponse.model_validate(payment),
        investigation_triggered=investigation_triggered,
    )


class DemoVerifyRequest(BaseModel):
    """Used by the frontend local-demo flow. Generates a valid HMAC signature
    server-side and immediately verifies it. No Razorpay API call is made.
    Only available when Razorpay Test Mode credentials are NOT configured."""

    razorpay_order_id: str = Field(min_length=1, max_length=64)


@router.post("/demo-verify", response_model=PaymentVerifyResponse, dependencies=[Depends(current_principal)])
def demo_verify(payload: DemoVerifyRequest, db: Session = Depends(get_db)):
    """Local-demo verification shortcut for the frontend.

    Generates the correct HMAC signature using RAZORPAY_DEMO_SECRET, then
    calls the standard verify_payment path so the identical HMAC verification
    code runs. Only callable in local-demo mode (no real credentials).
    """
    if razorpay_service.is_test_mode_configured():
        raise HTTPException(status_code=400, detail={
            "code": "DEMO_VERIFY_UNAVAILABLE",
            "message": "Use /verify with real Razorpay credentials in Test Mode.",
        })

    payment_record = payment_repository.get_by_order(db, payload.razorpay_order_id)
    if not payment_record:
        raise HTTPException(status_code=404, detail={
            "code": "PAYMENT_NOT_FOUND",
            "message": "No payment exists for this order.",
        })

    import secrets as _secrets
    fake_payment_id = f"pay_demo_{_secrets.token_hex(6)}"
    sig = razorpay_service.compute_payment_signature(payload.razorpay_order_id, fake_payment_id)

    try:
        payment, investigation_triggered = verify_payment(db, PaymentVerifyRequest(
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=fake_payment_id,
            razorpay_signature=sig,
        ))
    except PaymentVerificationError as exc:
        raise HTTPException(status_code=400, detail={
            "code": "PAYMENT_VERIFICATION_FAILED",
            "message": str(exc),
        })
    return PaymentVerifyResponse(
        verified=True,
        payment=PaymentResponse.model_validate(payment),
        investigation_triggered=investigation_triggered,
    )


@router.get("", response_model=list[PaymentResponse], dependencies=[Depends(current_principal)])
def list_payments(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return [PaymentResponse.model_validate(p) for p in payment_repository.list_recent(db, limit)]


@router.get("/transaction/{transaction_id}", response_model=PaymentResponse, dependencies=[Depends(current_principal)])
def get_payment_for_transaction(transaction_id: int, db: Session = Depends(get_db)):
    payment = payment_repository.get_by_transaction(db, transaction_id)
    if not payment:
        raise HTTPException(status_code=404, detail={
            "code": "PAYMENT_NOT_FOUND",
            "message": "No payment exists for this transaction.",
        })
    return PaymentResponse.model_validate(payment)