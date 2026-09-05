#!/usr/bin/env python
"""
Phase 4 test runner.
Runs all test suites in order and prints a summary.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
PYTEST = [str(PYTHON), "-m", "pytest"]

os.environ["DATABASE_URL"] = "postgresql+psycopg://riskora:riskora@localhost:5433/riskora"
os.environ.setdefault("ENVIRONMENT", "development")

def run(label, args, cwd=ROOT):
    print(f"\n{'='*64}")
    print(f"  {label}")
    print(f"{'='*64}")
    result = subprocess.run(
        PYTEST + args + ["-v", "--tb=short", "--no-header"],
        cwd=cwd,
    )
    return result.returncode

results = {}

results["Unit — features"]      = run("UNIT: test_features",      ["tests/test_features.py"])
results["Unit — inference"]      = run("UNIT: test_inference",     ["tests/test_inference.py"])
results["Unit — risk_engine"]    = run("UNIT: test_risk_engine",   ["tests/test_risk_engine.py"])
results["Unit — rag"]            = run("UNIT: test_rag",           ["tests/test_rag.py"])
results["Unit — agents"]         = run("UNIT: test_agents",        ["tests/test_agents.py"])
results["Unit — workflow"]       = run("UNIT: test_workflow",      ["tests/test_workflow.py"])
results["Unit — demo_scenarios"] = run("UNIT: test_demo_scenarios",["tests/test_demo_scenarios.py"])
results["API (SQLite)"]          = run("API TESTS (SQLite TestClient)", ["apps/api/tests/test_api.py"])
results["PG integration"]        = run("POSTGRESQL INTEGRATION",   ["tests/test_pg_integration.py"])

print(f"\n{'='*64}")
print("  FINAL RESULTS")
print(f"{'='*64}")
passed = failed = 0
for suite, code in results.items():
    status = "PASS" if code == 0 else "FAIL"
    mark   = "✓" if code == 0 else "✗"
    print(f"  [{mark}] {suite}: {status}")
    if code == 0:
        passed += 1
    else:
        failed += 1

print(f"\n  Suites passed: {passed}  |  Suites failed: {failed}")
sys.exit(0 if failed == 0 else 1)
