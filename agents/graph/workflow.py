"""LangGraph investigation workflow with bounded, recoverable nodes."""

from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from agents.audit.agent import make_event, run_audit_agent
from agents.behavior.agent import run_behavior_agent
from agents.decision.agent import run_decision_agent
from agents.evidence.agent import run_evidence_agent
from agents.investigation.agent import run_investigation_agent
from agents.state import InvestigationState
from rag.retrieval.tfidf_store import TfidfEvidenceStore
from risk_engine.policy import PolicyEngine


def _node(name: str, function: Callable[[], dict[str, Any]], state: InvestigationState) -> dict[str, Any]:
    try:
        result = function()
        return {
            **result,
            "audit_events": result.get("audit_events", []) + [
                make_event(name, {"status": result.get("status", "completed")})
            ],
        }
    except Exception as exc:
        error = {"agent": name, "error": str(exc)}
        return {"errors": [error], "audit_events": [make_event(name, {"status": "FAILED", "error": str(exc)})]}


def build_workflow(
    predictor,
    policy_engine: PolicyEngine | None = None,
    evidence_store: TfidfEvidenceStore | None = None,
    audit_path: str = "audit/investigation.json",
    llm_available: bool = True,
):
    policy = policy_engine or PolicyEngine()

    def validate(state):
        transaction = state.get("transaction", {})
        if not transaction.get("transaction_id"):
            raise ValueError("transaction_id is required")
        return {"audit_events": [make_event("TRANSACTION_RECEIVED", {"transaction_id": transaction["transaction_id"]})]}

    def ml(state):
        result = predictor.predict_transaction(state["transaction"])
        return {"ml_assessment": result, "audit_events": [make_event("ML_RISK_CALCULATED", result)]}

    def behavior(state):
        result = run_behavior_agent(state["transaction"])
        return {"behavioral_findings": result, "audit_events": [make_event("BEHAVIOR_ANALYSIS_COMPLETED", result)]}

    def investigation(state):
        result = run_investigation_agent(state["ml_assessment"], state["behavioral_findings"])
        return {"investigation_findings": result, "audit_events": [make_event("INVESTIGATION_STARTED", result)]}

    def evidence(state):
        result = run_evidence_agent(state["investigation_findings"], evidence_store)
        return {**result, "audit_events": [make_event("EVIDENCE_RETRIEVED", {"count": len(result.get("evidence", [])), "status": result["evidence_status"]})]}

    def decision(state):
        result = run_decision_agent(state["ml_assessment"], state["behavioral_findings"], state["investigation_findings"], state.get("evidence", []), llm_available)
        return {"decision_recommendation": result, "decision_status": result.get("decision_status", "COMPLETED"), "audit_events": [make_event("DECISION_GENERATED", result)]}

    def policy_node(state):
        ml = state["ml_assessment"]
        result = policy.evaluate(ml["risk_score"], state["behavioral_findings"].get("findings", []), state["decision_recommendation"].get("recommendation"), bool(state.get("evidence")))
        return {"policy_result": result, "audit_events": [make_event("POLICY_EVALUATED", result)]}

    def audit(state):
        return run_audit_agent(state, audit_path)

    graph = StateGraph(InvestigationState)
    graph.add_node("validate", lambda s: _node("VALIDATION", lambda: validate(s), s))
    graph.add_node("ml", lambda s: _node("ML", lambda: ml(s), s))
    graph.add_node("behavior", lambda s: _node("BEHAVIOR_AGENT", lambda: behavior(s), s))
    graph.add_node("investigation", lambda s: _node("INVESTIGATION_AGENT", lambda: investigation(s), s))
    graph.add_node("evidence", lambda s: _node("EVIDENCE_AGENT", lambda: evidence(s), s))
    graph.add_node("decision", lambda s: _node("DECISION_AGENT", lambda: decision(s), s))
    graph.add_node("policy", lambda s: _node("POLICY_ENGINE", lambda: policy_node(s), s))
    graph.add_node("audit", lambda s: _node("AUDIT_AGENT", lambda: audit(s), s))
    graph.add_edge(START, "validate")
    graph.add_edge("validate", "ml")
    graph.add_edge("ml", "behavior")
    graph.add_edge("behavior", "investigation")
    graph.add_edge("investigation", "evidence")
    graph.add_edge("evidence", "decision")
    graph.add_edge("decision", "policy")
    graph.add_edge("policy", "audit")
    graph.add_edge("audit", END)
    return graph.compile()


def run_investigation(transaction: dict[str, Any], predictor, **kwargs) -> InvestigationState:
    initial: InvestigationState = {"transaction": transaction, "audit_events": [], "errors": []}
    return build_workflow(predictor, **kwargs).invoke(initial)
