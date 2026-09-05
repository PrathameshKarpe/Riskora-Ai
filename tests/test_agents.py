import json

from agents.audit.agent import run_audit_agent
from agents.behavior.agent import run_behavior_agent
from agents.decision.agent import run_decision_agent
from agents.evidence.agent import run_evidence_agent
from agents.investigation.agent import run_investigation_agent
from risk_engine.demo_transactions import demo_transactions


def test_agents_produce_structured_outputs(tmp_path):
    transaction = demo_transactions()["suspicious"]
    behavior = run_behavior_agent(transaction)
    ml = {"risk_score": 70, "risk_level": "HIGH", "model_version": "test"}
    investigation = run_investigation_agent(ml, behavior)
    evidence = run_evidence_agent(investigation)
    decision = run_decision_agent(ml, behavior, investigation, evidence["evidence"])
    audit = run_audit_agent({"transaction": transaction, "audit_events": []}, tmp_path / "audit.json")
    assert behavior["status"] == "completed"
    assert investigation["key_findings"]
    assert evidence["evidence_status"] == "RETRIEVED"
    assert decision["recommendation"] == "HOLD"
    assert "audit_events" in audit
    assert json.loads((tmp_path / "audit.json").read_text())["events"]


def test_decision_agent_failure_mode_is_bounded():
    result = run_decision_agent({}, {"findings": []}, {}, [], llm_available=False)
    assert result["decision_status"] == "LLM_UNAVAILABLE"
    assert result["recommendation"] == "HUMAN_REVIEW"
    assert "execute" not in result


def test_missing_evidence_is_not_fabricated():
    result = run_evidence_agent({"key_findings": ["not_a_real_signal"]})
    assert result["evidence_status"] == "NO_RELEVANT_EVIDENCE"
    assert result["evidence"] == []
