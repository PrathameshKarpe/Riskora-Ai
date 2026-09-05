import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from apps.api.app.api.v1.router import router
from apps.api.app.core.config import settings
from apps.api.app.db.session import make_session_factory

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Riskora AI API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/health")
def health(): return {"status": "ok", "service": "riskora-api"}

@app.get("/health/db")
def database_health():
    try:
        db = make_session_factory(settings.database_url)()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        return {"status": "ok", "service": "riskora-api", "database": "ok"}
    except Exception as exc:
        return {"status": "degraded", "service": "riskora-api", "database": "unavailable", "detail": str(exc)}
