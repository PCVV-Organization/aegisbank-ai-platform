"""Dense baseline retriever using TF-IDF followed by TruncatedSVD (LSA).

This is a purely local vector baseline. It is NOT equivalent to modern
embeddings produced by Azure AI Search, sentence-transformers, or any
external embedding API. The dimensionality is small (LSA_COMPONENTS) and
fits in memory. Every random source is seeded through ``RANDOM_STATE``.
"""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.constants import LSA_COMPONENTS, RANDOM_STATE
from aegisbank_rag.lexical import LEXICAL_VECTORIZER
from aegisbank_rag.retriever import RetrievalHit, Retriever, _build_hits


class DenseLocalRetriever(Retriever):
    name = "dense_local_lsa"

    def __init__(self, *, components: int = LSA_COMPONENTS) -> None:
        self._vectorizer = TfidfVectorizer(**LEXICAL_VECTORIZER)
        self._svd = TruncatedSVD(
            n_components=min(components, 32),
            random_state=RANDOM_STATE,
            algorithm="randomized",
            n_iter=5,
            tol=0.0,
        )
        self._matrix = None
        self._chunks: list[Chunk] = []
        self._components = components

    def fit(self, chunks: Sequence[Chunk]) -> None:
        self._chunks = list(chunks)
        tfidf = self._vectorizer.fit_transform(chunk.content for chunk in self._chunks)
        n_components = min(self._components, max(1, min(tfidf.shape) - 1))
        self._svd = TruncatedSVD(
            n_components=n_components,
            random_state=RANDOM_STATE,
            algorithm="randomized",
            n_iter=5,
            tol=0.0,
        )
        reduced = self._svd.fit_transform(tfidf)
        self._matrix = normalize(reduced, norm="l2", axis=1)

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalHit]:
        if self._matrix is None:
            raise RuntimeError("DenseLocalRetriever.fit() must be called before search()")
        if not query.strip():
            raise ValueError("Query must not be empty")
        query_tfidf = self._vectorizer.transform([query])
        query_reduced = self._svd.transform(query_tfidf)
        query_vector = normalize(query_reduced, norm="l2", axis=1)
        similarities = cosine_similarity(query_vector, self._matrix)[0]
        ranked_indices = similarities.argsort()[::-1][:top_k]
        ranked: list[tuple[int, float]] = []
        for chunk_index in ranked_indices:
            score = float(similarities[chunk_index])
            if score <= 0.0:
                continue
            ranked.append((int(chunk_index), score))
        return _build_hits(ranked, self._chunks, method=self.name)
