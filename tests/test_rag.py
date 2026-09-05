from rag.ingestion.loader import load_documents
from rag.retrieval.tfidf_store import TfidfEvidenceStore


def test_ingestion_and_retrieval_preserve_metadata():
    chunks = load_documents()
    assert len(chunks) >= 7
    results = TfidfEvidenceStore(chunks).search("new device and unusual amount", top_k=2)
    assert results
    assert {"source", "section", "relevance_score", "content", "metadata"}.issubset(results[0])
    assert results[0]["metadata"]["document_type"] == "demo-internal-policy"


def test_retrieval_returns_no_result_for_empty_or_unrelated_query():
    store = TfidfEvidenceStore()
    assert store.search("") == []
    assert store.search("quantum banana spaceship", minimum_score=0.5) == []
