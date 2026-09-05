"""Small local TF-IDF vector store with source-preserving retrieval."""

from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag.ingestion.loader import DocumentChunk, load_documents


class TfidfEvidenceStore:
    def __init__(self, chunks: list[DocumentChunk] | None = None) -> None:
        self.chunks = chunks or load_documents()
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([chunk.content for chunk in self.chunks])

    def search(self, query: str, top_k: int = 3, minimum_score: float = 0.05) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        results = []
        for index, score in ranked[:top_k]:
            if float(score) < minimum_score:
                continue
            chunk = self.chunks[index]
            results.append({
                "source": chunk.source,
                "section": chunk.section,
                "relevance_score": round(float(score), 4),
                "content": chunk.content,
                "metadata": chunk.metadata,
            })
        return results
