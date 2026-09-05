#!/usr/bin/env python
"""Verify PostgreSQL connectivity using the project DATABASE_URL (host port 5433)."""
import os
import sys
import time

import sqlalchemy as sa
from sqlalchemy import text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://riskora:riskora@localhost:5433/riskora",
)

print(f"Testing connection to: {DATABASE_URL}")
for i in range(30):
    try:
        engine = sa.create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        print("PostgreSQL connection: PASS")
        sys.exit(0)
    except Exception as exc:
        if i < 29:
            print(f"Attempt {i + 1}/30: {exc}", file=sys.stderr)
            time.sleep(1)
        else:
            print(f"PostgreSQL connection: FAIL — {exc}", file=sys.stderr)
            sys.exit(1)
