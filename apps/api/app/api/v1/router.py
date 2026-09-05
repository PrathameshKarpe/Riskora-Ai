from fastapi import APIRouter
from . import auth, transactions, investigations, reviews, audit, dashboard, payments, webhooks

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
router.include_router(investigations.router, tags=["investigations"])
router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(payments.router, prefix="/payments", tags=["payments"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
