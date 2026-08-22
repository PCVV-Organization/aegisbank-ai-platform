"""Hybrid retriever that fuses lexical and dense-local via RRF."""

from __future__ import annotations

from collections.abc import Sequence

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.constants import RRF_K
from aegisbank_rag.dense_local import DenseLocalRetriever
from aegisbank_rag.lexical import LexicalRetriever
from aegisbank_rag.retriever import RetrievalHit, Retriever, reciprocal_rank_fusion


class HybridRRFRetriever(Retriever):
    name = "hybrid_rrf"

    def __init__(
        self,
        *,
        rrf_k: int = RRF_K,
        components: int = 64,
    ) -> None:
        self._lexical = LexicalRetriever()
        self._dense = DenseLocalRetriever(components=components)
        self._rrf_k = rrf_k
        self._components = components

    def fit(self, chunks: Sequence[Chunk]) -> None:
        self._lexical.fit(chunks)
        self._dense.fit(chunks)

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalHit]:
        if not query.strip():
            raise ValueError("Query must not be empty")
        pool = max(top_k, self._components) * 2
        lexical_hits = self._lexical.search(query, top_k=pool)
        dense_hits = self._dense.search(query, top_k=pool)
        fused = reciprocal_rank_fusion([lexical_hits, dense_hits], k=self._rrf_k)
        return fused[:top_k]
