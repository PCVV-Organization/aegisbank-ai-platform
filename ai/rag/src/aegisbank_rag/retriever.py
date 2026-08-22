"""Local retrieval interface and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.constants import RRF_K


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    document_id: str
    document_version: str
    chunk_id: str
    title: str
    topic: str
    content: str
    source: str
    status: str
    effective_from: str
    effective_to: str | None
    score: float
    rank: int
    retrieval_method: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_version": self.document_version,
            "chunk_id": self.chunk_id,
            "title": self.title,
            "topic": self.topic,
            "content": self.content,
            "source": self.source,
            "status": self.status,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "score": self.score,
            "rank": self.rank,
            "retrieval_method": self.retrieval_method,
        }


class Retriever(ABC):
    name: str

    @abstractmethod
    def fit(self, chunks: Sequence[Chunk]) -> None: ...

    @abstractmethod
    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalHit]: ...


def _build_hits(
    ranked: Iterable[tuple[int, float]],
    chunks: Sequence[Chunk],
    *,
    method: str,
) -> list[RetrievalHit]:
    out: list[RetrievalHit] = []
    for rank, (chunk_index, score) in enumerate(ranked, start=1):
        chunk = chunks[chunk_index]
        out.append(
            RetrievalHit(
                document_id=chunk.document_id,
                document_version=chunk.document_version,
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                topic=chunk.topic,
                content=chunk.content,
                source=chunk.source,
                status=chunk.status,
                effective_from=chunk.effective_from,
                effective_to=chunk.effective_to,
                score=score,
                rank=rank,
                retrieval_method=method,
            )
        )
    return out


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[RetrievalHit]],
    *,
    k: int = RRF_K,
) -> list[RetrievalHit]:
    fused: dict[str, float] = {}
    order: dict[str, RetrievalHit] = {}
    for ranking in rankings:
        for position, hit in enumerate(ranking, start=1):
            fused[hit.chunk_id] = fused.get(hit.chunk_id, 0.0) + 1.0 / (k + position)
            order.setdefault(hit.chunk_id, hit)
    fused_sorted = sorted(fused.items(), key=lambda item: item[1], reverse=True)
    out: list[RetrievalHit] = []
    for rank, (chunk_id, fused_score) in enumerate(fused_sorted, start=1):
        base = order[chunk_id]
        out.append(
            RetrievalHit(
                document_id=base.document_id,
                document_version=base.document_version,
                chunk_id=base.chunk_id,
                title=base.title,
                topic=base.topic,
                content=base.content,
                source=base.source,
                status=base.status,
                effective_from=base.effective_from,
                effective_to=base.effective_to,
                score=fused_score,
                rank=rank,
                retrieval_method="hybrid_rrf",
            )
        )
    return out
