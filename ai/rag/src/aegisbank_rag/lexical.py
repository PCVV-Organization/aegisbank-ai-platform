"""Lexical retrieval backed by TF-IDF."""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.retriever import RetrievalHit, Retriever, _build_hits

LEXICAL_VECTORIZER: dict[str, object] = {
    "lowercase": True,
    "ngram_range": (1, 2),
    "min_df": 1,
    "max_df": 1.0,
    "sublinear_tf": True,
    "norm": "l2",
    "stop_words": None,
    "token_pattern": r"(?u)\b\w\w+\b",
}


class LexicalRetriever(Retriever):
    name = "lexical_tfidf"

    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(**LEXICAL_VECTORIZER)
        self._matrix = None
        self._chunks: list[Chunk] = []

    def fit(self, chunks: Sequence[Chunk]) -> None:
        self._chunks = list(chunks)
        self._matrix = self._vectorizer.fit_transform(chunk.content for chunk in self._chunks)

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalHit]:
        if self._matrix is None:
            raise RuntimeError("LexicalRetriever.fit() must be called before search()")
        if not query.strip():
            raise ValueError("Query must not be empty")
        query_vector = self._vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self._matrix)[0]
        ranked_indices = similarities.argsort()[::-1][:top_k]
        ranked: list[tuple[int, float]] = []
        for chunk_index in ranked_indices:
            score = float(similarities[chunk_index])
            if score <= 0.0:
                continue
            ranked.append((int(chunk_index), score))
        return _build_hits(ranked, self._chunks, method=self.name)
