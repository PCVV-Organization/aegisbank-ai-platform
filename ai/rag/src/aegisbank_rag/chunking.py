"""Deterministic chunking for the v0.4 retrieval foundation."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from typing import Final

from aegisbank_rag.corpus import Document

_SENTENCE_SPLIT: Final = re.compile(r"(?<=[\.\?\!])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])")


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    document_version: str
    chunk_index: int
    title: str
    topic: str
    effective_from: str
    effective_to: str | None
    status: str
    source: str
    content: str

    def as_dict(self) -> dict[str, str | int]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_version": self.document_version,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "topic": self.topic,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to if self.effective_to else "",
            "status": self.status,
            "source": self.source,
            "content": self.content,
        }


def _split_sentences(body: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(body.strip())
    return [part.strip() for part in parts if part.strip()]


def _pack_sentences(
    sentences: Iterable[str],
    *,
    min_chars: int,
    max_chars: int,
) -> list[str]:
    chunks: list[str] = []
    buffer: list[str] = []
    for sentence in sentences:
        candidate = sentence if not buffer else " ".join([*buffer, sentence])
        if len(candidate) > max_chars and buffer:
            chunks.append(" ".join(buffer).strip())
            buffer = [sentence]
        else:
            buffer.append(sentence)
    if buffer:
        chunks.append(" ".join(buffer).strip())
    return [chunk for chunk in chunks if len(chunk) >= min_chars]


def chunk_document(
    document: Document,
    *,
    min_chars: int = 50,
    max_chars: int = 300,
) -> list[Chunk]:
    if min_chars <= 0 or max_chars <= min_chars:
        raise ValueError(f"Invalid chunk bounds: min_chars={min_chars}, max_chars={max_chars}")
    sentences = _split_sentences(document.body)
    packed = _pack_sentences(sentences, min_chars=min_chars, max_chars=max_chars)
    chunks: list[Chunk] = []
    for chunk_index, content in enumerate(packed, start=1):
        chunk_id = _build_chunk_id(document.document_id, document.version, chunk_index, content)
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                document_version=document.version,
                chunk_index=chunk_index,
                title=document.title,
                topic=document.topic,
                effective_from=document.effective_from.isoformat(),
                effective_to=(document.effective_to.isoformat() if document.effective_to else None),
                status=document.status,
                source=document.source,
                content=content,
            )
        )
    if not chunks:
        raise ValueError(
            f"Document {document.document_id} v{document.version} produced "
            f"no chunks (body length {len(document.body)})"
        )
    return chunks


def _build_chunk_id(document_id: str, version: str, chunk_index: int, content: str) -> str:
    digest = sha256(f"{document_id}|{version}|{chunk_index}|{content}".encode("utf-8")).hexdigest()[
        :12
    ]
    return f"chk_{document_id}__{version}__c{chunk_index:03d}_{digest}"


def chunk_corpus(documents: Iterable[Document], **kwargs: object) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, **kwargs))  # type: ignore[arg-type]
    validate_chunks(chunks)
    return chunks


def validate_chunks(chunks: list[Chunk]) -> None:
    if not chunks:
        raise ValueError("Chunk list must not be empty")
    seen: set[str] = set()
    for chunk in chunks:
        if chunk.chunk_id in seen:
            raise ValueError(f"Duplicate chunk_id detected: {chunk.chunk_id}")
        seen.add(chunk.chunk_id)
        if not chunk.content.strip():
            raise ValueError(f"Chunk {chunk.chunk_id} has empty content")


def chunk_manifest(chunks: list[Chunk]) -> dict[str, int | dict[str, int]]:
    by_topic: dict[str, int] = {}
    by_document: dict[str, int] = {}
    for chunk in chunks:
        by_topic[chunk.topic] = by_topic.get(chunk.topic, 0) + 1
        by_document[chunk.document_id] = by_document.get(chunk.document_id, 0) + 1
    return {
        "chunk_count": len(chunks),
        "by_topic": dict(sorted(by_topic.items())),
        "by_document": dict(sorted(by_document.items())),
    }
