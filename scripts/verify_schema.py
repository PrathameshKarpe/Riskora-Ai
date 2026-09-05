#!/usr/bin/env python
"""Verify PostgreSQL schema: tables, indexes, foreign keys."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy import inspect, text

url = os.environ.get("DATABASE_URL", "postgresql+psycopg://riskora:riskora@localhost:5433/riskora")
engine = sa.create_engine(url)
insp = inspect(engine)

EXPECTED_TABLES = [
    "users", "transactions", "risk_assessments", "investigations",
    "agent_findings", "evidence", "policy_decisions", "human_reviews", "audit_events",
]

all_pass = True

print("=== TABLE & INDEX VERIFICATION ===")
existing_tables = set(insp.get_table_names(schema="public"))
for table in EXPECTED_TABLES:
    if table in existing_tables:
        idxs = [i["name"] for i in insp.get_indexes(table)]
        fks  = [
            f"{fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
            for fk in insp.get_foreign_keys(table)
        ]
        print(f"  [OK] {table}")
        print(f"       indexes: {idxs}")
        if fks:
            print(f"       foreign_keys: {fks}")
    else:
        print(f"  [MISSING] {table}")
        all_pass = False

print()
print("=== COMPOSITE INDEX ===")
with engine.connect() as conn:
    row = conn.execute(text(
        "SELECT indexname FROM pg_indexes "
        "WHERE tablename='transactions' AND indexname='ix_transactions_status_created'"
    )).fetchone()
    status = "FOUND" if row else "MISSING"
    if not row:
        all_pass = False
    print(f"  ix_transactions_status_created: {status}")

print()
print("=== JSONB COLUMN CHECK ===")
with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT table_name, column_name, data_type "
        "FROM information_schema.columns "
        "WHERE data_type = 'jsonb' AND table_schema = 'public' "
        "ORDER BY table_name, column_name"
    )).fetchall()
    for r in rows:
        print(f"  [JSONB] {r[0]}.{r[1]}")
    if not rows:
        print("  [WARN] No JSONB columns found")

engine.dispose()
print()
if all_pass:
    print("Schema verification: PASS")
    sys.exit(0)
else:
    print("Schema verification: FAIL")
    sys.exit(1)
