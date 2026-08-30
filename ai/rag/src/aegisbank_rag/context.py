"""Deterministic context construction with explicit provenance."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from aegisbank_rag.retriever import RetrievalHit


@dataclass(frozen=True, slots=True)
class ContextEntry:
    document_id: str
    version: str
    chunk_id: str
    source: str
    status: str
    rank: int
    content: str

    @classmethod
    def from_hit(cls, hit: RetrievalHit) -> ContextEntry:
        return cls(
            document_id=hit.document_id,
            version=hit.document_version,
            chunk_id=hit.chunk_id,
            source=hit.source,
            status=hit.status,
            rank=hit.rank,
            content=hit.content,
        )

    def as_dict(self) -> dict[str, str | int]:
        return {
            "document_id": self.document_id,
            "version": self.version,
            "chunk_id": self.chunk_id,
            "source": self.source,
            "status": self.status,
            "rank": self.rank,
            "content": self.content,
        }


@dataclass(frozen=True, slots=True)
class GroundingContext:
    entries: tuple[ContextEntry, ...]

    @property
    def chunk_ids(self) -> tuple[str, ...]:
        return tuple(entry.chunk_id for entry in self.entries)

    def as_dict(self) -> dict[str, Any]:
        return {
            "trust": "untrusted_retrieved_evidence",
            "entries": [entry.as_dict() for entry in self.entries],
        }

    def render_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


def build_context(
    hits: Sequence[RetrievalHit],
    *,
    active_only: bool = True,
) -> GroundingContext:
    """Build canonical context in retrieval order, rejecting duplicate provenance."""

    entries: list[ContextEntry] = []
    seen: set[str] = set()
    for hit in sorted(hits, key=lambda item: (item.rank, item.chunk_id)):
        if active_only and hit.status != "active":
            continue
        if not hit.chunk_id.strip() or not hit.content.strip():
            raise ValueError("Retrieved hits require non-empty chunk_id and content")
        if hit.chunk_id in seen:
            raise ValueError(f"Duplicate retrieved chunk_id: {hit.chunk_id}")
        seen.add(hit.chunk_id)
        entries.append(ContextEntry.from_hit(hit))
    return GroundingContext(entries=tuple(entries))
