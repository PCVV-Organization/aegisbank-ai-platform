"""Dense baseline retriever using TF-IDF followed by TruncatedSVD (LSA).

This is a purely local vector baseline. It is NOT equivalent to modern
embeddings produced by Azure AI Search, sentence-transformers, or any
external embedding API. The dimensionality is small (LSA_COMPONENTS) and
fits in memory. Every random source is seeded through ``RANDOM_STATE``.
"""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.metrics.pairwise import cosine_similarity

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.constants import LSA_COMPONENTS
from aegisbank_rag.embedding import LocalDenseEmbeddingModel
from aegisbank_rag.retriever import RetrievalHit, Retriever, _build_hits


class DenseLocalRetriever(Retriever):
    name = "dense_local_lsa"

    def __init__(self, *, components: int = LSA_COMPONENTS) -> None:
        self._embedding = LocalDenseEmbeddingModel(dimension=components)
        self._matrix = None
        self._chunks: list[Chunk] = []

    def fit(self, chunks: Sequence[Chunk]) -> None:
        self._chunks = list(chunks)
        texts = [chunk.content for chunk in self._chunks]
        self._embedding.fit(texts)
        self._matrix = self._embedding.encode(texts)

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalHit]:
        if self._matrix is None:
            raise RuntimeError("DenseLocalRetriever.fit() must be called before search()")
        if not query.strip():
            raise ValueError("Query must not be empty")
        query_vector = self._embedding.encode([query])
        similarities = cosine_similarity(query_vector, self._matrix)[0]
        ranked_indices = similarities.argsort()[::-1][:top_k]
        ranked: list[tuple[int, float]] = []
        for chunk_index in ranked_indices:
            score = float(similarities[chunk_index])
            if score <= 0.0:
                continue
            ranked.append((int(chunk_index), score))
        return _build_hits(ranked, self._chunks, method=self.name)
