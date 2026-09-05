"""Evidence agent that retrieves, cites, and explains local policy chunks."""

from typing import Any, Mapping

from rag.retrieval.tfidf_store import TfidfEvidenceStore


def run_evidence_agent(
    investigation_findings: Mapping[str, Any],
    store: TfidfEvidenceStore | None = None,
) -> dict[str, Any]:
    repository = store or TfidfEvidenceStore()
    supported_signals = {
        "amount_anomaly": "unusual transaction amount historical average",
        "historical_amount_deviation": "amount deviation historical behavior",
        "transaction_velocity": "transaction velocity failed attempts",
        "new_device": "new device unusual amount",
        "new_location": "new location account takeover",
        "unusual_transaction_time": "unusual transaction time account takeover",
        "failed_payment_attempts": "failed payment attempts velocity",
        "previous_fraud_association": "previous fraud association escalation",
        "impossible_travel": "impossible travel location timestamp",
    }
    queries = [supported_signals[signal] for signal in investigation_findings.get("key_findings", []) if signal in supported_signals]
    evidence: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for query in queries:
        for result in repository.search(query, top_k=1):
            key = (result["source"], result["section"])
            if key in seen:
                continue
            seen.add(key)
            result["finding_supported"] = True
            result["explanation"] = f"The demo guideline addresses {query} as a relevant risk indicator."
            evidence.append(result)
    return {
        "agent": "evidence_agent",
        "status": "completed",
        "evidence": evidence,
        "evidence_status": "RETRIEVED" if evidence else "NO_RELEVANT_EVIDENCE",
    }
