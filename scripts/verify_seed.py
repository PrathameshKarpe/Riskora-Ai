#!/usr/bin/env python
"""Verify seed data is present in PostgreSQL."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy import text

url = os.environ.get("DATABASE_URL", "postgresql+psycopg://riskora:riskora@localhost:5433/riskora")
engine = sa.create_engine(url)

with engine.connect() as conn:
    users = conn.execute(text("SELECT id, email, role FROM users ORDER BY id")).fetchall()
    txs   = conn.execute(text("SELECT id, external_id, amount, status FROM transactions ORDER BY id")).fetchall()

engine.dispose()

print("=== Users ===")
for u in users:
    print(f"  id={u[0]}  email={u[1]}  role={u[2]}")

print(f"\n=== Transactions ({len(txs)}) ===")
for t in txs:
    print(f"  id={t[0]}  external_id={t[1]}  amount={t[2]}  status={t[3]}")

ok = len(users) >= 1 and len(txs) >= 3
print(f"\nSeed verification: {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
