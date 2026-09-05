from typing import Any

from rag.retrieval.tfidf_store import TfidfEvidenceStore


def search_risk_evidence(query: str, store: TfidfEvidenceStore | None = None, top_k: int = 3) -> list[dict[str, Any]]:
    return (store or TfidfEvidenceStore()).search(query, top_k=top_k)
