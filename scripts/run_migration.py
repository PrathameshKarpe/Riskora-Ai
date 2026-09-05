#!/usr/bin/env python
"""Run Alembic upgrade head and verify the Phase 6 tables exist."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://riskora:riskora@localhost:5433/riskora")

result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    capture_output=True, text=True,
    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
if result.returncode not in (0, 1):   # alembic writes INFO to stderr → non-zero on Windows
    sys.exit(result.returncode)

# Verify tables
import sqlalchemy as sa
from sqlalchemy import text, inspect

engine = sa.create_engine(os.environ["DATABASE_URL"])
insp = inspect(engine)
tables = set(insp.get_table_names(schema="public"))
required = {"payments", "webhook_events", "transactions", "investigations", "audit_events"}
missing = required - tables
if missing:
    print(f"MISSING tables: {missing}")
    sys.exit(1)

# Check alembic_version
with engine.connect() as conn:
    ver = conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num")).fetchall()
    print("Applied migrations:", [r[0] for r in ver])

engine.dispose()
print("Migration verification: PASS")
