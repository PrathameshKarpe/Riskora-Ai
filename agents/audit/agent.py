"""Local append-only JSON audit writer for the Phase 3 prototype."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def make_event(event: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"event": event, "timestamp": datetime.now(timezone.utc).isoformat(), "details": details}


def run_audit_agent(state: dict[str, Any], output_path: str | Path = "audit/investigation.json") -> dict[str, Any]:
    events = list(state.get("audit_events", []))
    events.append(make_event("AUDIT_RECORDED", {"transaction_id": state["transaction"].get("transaction_id", "unknown")}))
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"transaction_id": state["transaction"].get("transaction_id"), "events": events}, indent=2), encoding="utf-8")
    return {"audit_events": events, "audit_path": str(path)}
