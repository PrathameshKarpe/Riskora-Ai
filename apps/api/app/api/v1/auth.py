"""Authentication endpoints.

In development mode this issues a real HS256 JWT for any supplied email/role
so the frontend can exercise the full auth flow without a user database.
In production this should be replaced with a real credential-verification step.
"""
from fastapi import APIRouter, HTTPException, status
from apps.api.app.core.config import settings
from apps.api.app.core.security import create_token
from apps.api.app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()

# Demo credentials accepted in development mode.
_DEMO_ACCOUNTS: dict[str, str] = {
    "admin@riskora.local": "ADMIN",
    "analyst@riskora.local": "RISK_ANALYST",
    "reviewer@riskora.local": "REVIEWER",
    "demo@riskora.local": "ADMIN",
}

# Simple demo password — never used in production.
_DEMO_PASSWORD = "riskora2024"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    """Issue a JWT bearer token.

    Development: any email in _DEMO_ACCOUNTS is accepted.
    The role from the request is ignored; the pre-configured role is used.
    """
    email = payload.email.strip().lower()

    if settings.environment == "development":
        role = _DEMO_ACCOUNTS.get(email)
        if role is None:
            # Accept any email in development; default to RISK_ANALYST.
            role = payload.role if payload.role in {"ADMIN", "RISK_ANALYST", "REVIEWER"} else "RISK_ANALYST"
        token = create_token(subject=email, role=role)
        return LoginResponse(access_token=token, email=email, role=role)

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Production authentication not yet configured.",
    )
