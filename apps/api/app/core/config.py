import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./riskora_dev.db")
    environment: str = os.getenv("ENVIRONMENT", "development")
    cors_origins: tuple[str, ...] = tuple(filter(None, os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")))
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-me")
    llm_model: str = os.getenv("LLM_MODEL", "")
    # Razorpay TEST MODE credentials. Server-side only: never expose the
    # key secret or webhook secret to the browser/frontend.
    razorpay_key_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    razorpay_webhook_secret: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    # Local demo signing secret used ONLY when Razorpay Test Mode
    # credentials are absent, so the demo can exercise the identical
    # HMAC verification code path offline with synthetic data.
    razorpay_demo_secret: str = os.getenv("RAZORPAY_DEMO_SECRET", "riskora-local-demo-secret")


settings = Settings()
