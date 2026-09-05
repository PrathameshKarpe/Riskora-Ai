#!/usr/bin/env python
"""Quick PostgreSQL connectivity check used during Phase 4 verification."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy import text

url = os.environ.get("DATABASE_URL", "postgresql+psycopg://riskora:riskora@localhost:5433/riskora")
try:
    engine = sa.create_engine(url)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
    engine.dispose()
    print(f"[PASS] Connected to PostgreSQL: {version}")
    sys.exit(0)
except Exception as exc:
    print(f"[FAIL] Cannot connect to PostgreSQL at {url}: {exc}")
    sys.exit(1)
