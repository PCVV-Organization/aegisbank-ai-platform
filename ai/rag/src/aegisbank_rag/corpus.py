"""Synthetic banking knowledge corpus with versioned metadata."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from aegisbank_rag.constants import (
    ALLOWED_STATUSES,
    ALLOWED_TOPICS,
    CORPUS_DIR,
    CORPUS_MANIFEST_PATH,
    REQUIRED_DOCUMENT_FIELDS,
)

DATE_FIELDS = ("effective_from", "effective_to")


class CorpusError(ValueError):
    """Raised when the corpus violates its frozen contract."""


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    version: str
    title: str
    topic: str
    effective_from: date
    effective_to: date | None
    status: str
    source: str
    body: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "version": self.version,
            "title": self.title,
            "topic": self.topic,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "status": self.status,
            "source": self.source,
            "body": self.body,
        }


def load_document(path: Path) -> Document:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fields = set(payload)
    missing = set(REQUIRED_DOCUMENT_FIELDS) - fields
    if missing:
        raise CorpusError(f"Document {path.name} missing required fields: {sorted(missing)}")
    extra = fields - set(REQUIRED_DOCUMENT_FIELDS)
    if extra:
        raise CorpusError(f"Document {path.name} contains unexpected fields: {sorted(extra)}")
    try:
        effective_from = date.fromisoformat(payload["effective_from"])
    except ValueError as exc:
        raise CorpusError(
            f"Document {path.name} effective_from is not ISO-8601: {payload['effective_from']!r}"
        ) from exc
    effective_to_raw = payload["effective_to"]
    effective_to: date | None
    if effective_to_raw is None:
        effective_to = None
    else:
        try:
            effective_to = date.fromisoformat(effective_to_raw)
        except ValueError as exc:
            raise CorpusError(
                f"Document {path.name} effective_to is not ISO-8601: {effective_to_raw!r}"
            ) from exc
    if payload["status"] not in ALLOWED_STATUSES:
        raise CorpusError(
            f"Document {path.name} status {payload['status']!r} not in {ALLOWED_STATUSES}"
        )
    if payload["topic"] not in ALLOWED_TOPICS:
        raise CorpusError(
            f"Document {path.name} topic {payload['topic']!r} not in {ALLOWED_TOPICS}"
        )
    if not payload["body"].strip():
        raise CorpusError(f"Document {path.name} body must be non-empty")
    return Document(
        document_id=payload["document_id"],
        version=payload["version"],
        title=payload["title"],
        topic=payload["topic"],
        effective_from=effective_from,
        effective_to=effective_to,
        status=payload["status"],
        source=payload["source"],
        body=payload["body"],
    )


def load_corpus(corpus_dir: Path = CORPUS_DIR) -> list[Document]:
    if not corpus_dir.is_dir():
        raise CorpusError(f"Corpus directory not found: {corpus_dir}")
    documents = [load_document(path) for path in sorted(corpus_dir.glob("*.json"))]
    validate_corpus(documents)
    return documents


def validate_corpus(documents: list[Document]) -> None:
    errors: list[str] = []
    if not documents:
        errors.append("Corpus must contain at least one document")
    versions = [(doc.document_id, doc.version) for doc in documents]
    if len(versions) != len(set(versions)):
        errors.append("Duplicate (document_id, version) pair detected")
    topics = Counter(doc.topic for doc in documents)
    for topic in ALLOWED_TOPICS:
        if topics[topic] == 0:
            errors.append(f"Corpus missing at least one document for topic {topic!r}")
    by_document: dict[str, list[Document]] = {}
    for doc in documents:
        by_document.setdefault(doc.document_id, []).append(doc)
    for document_id, docs in by_document.items():
        docs_sorted = sorted(docs, key=lambda d: d.effective_from)
        last = docs_sorted[-1]
        if last.status != "active":
            errors.append(
                f"Document {document_id} most-recent version {last.version} must "
                f"have status 'active' (got {last.status!r})"
            )
        if last.effective_to is not None:
            errors.append(
                f"Document {document_id} active version {last.version} must "
                f"have an open effective_to (got {last.effective_to!r})"
            )
        active_count = sum(1 for doc in docs_sorted if doc.status == "active")
        if active_count > 1:
            errors.append(f"Document {document_id} has {active_count} active versions")
        for previous, current in zip(docs_sorted, docs_sorted[1:], strict=False):
            if current.status != "active" and current.effective_to is None:
                errors.append(
                    f"Document {document_id} version {current.version} with "
                    f"status {current.status!r} must define effective_to"
                )
            if previous.effective_to is None:
                errors.append(
                    f"Document {document_id} version {previous.version} must "
                    f"define effective_to when a successor version exists"
                )
                continue
            if current.effective_from <= previous.effective_to:
                errors.append(
                    f"Document {document_id} version {current.version} "
                    f"effective_from must be strictly after the previous "
                    f"version's effective_to"
                )
                continue
            if current.status not in ("superseded", "active", "retired"):
                errors.append(
                    f"Document {document_id} version {current.version} has "
                    f"unexpected status {current.status!r}"
                )
    for doc in documents:
        if doc.effective_to is not None and doc.effective_to < doc.effective_from:
            errors.append(
                f"Document {doc.document_id} v{doc.version} effective_to is before effective_from"
            )
    if errors:
        raise CorpusError("; ".join(errors))


def filter_active(
    documents: list[Document],
    cutoff: date,
    *,
    include_statuses: tuple[str, ...] = ("active",),
) -> list[Document]:
    filtered: list[Document] = []
    for doc in documents:
        if doc.status not in include_statuses:
            continue
        if doc.effective_from > cutoff:
            continue
        if doc.effective_to is not None and doc.effective_to <= cutoff:
            continue
        filtered.append(doc)
    return filtered


def build_manifest(documents: list[Document]) -> dict[str, Any]:
    by_status = Counter(doc.status for doc in documents)
    by_topic = Counter(doc.topic for doc in documents)
    return {
        "document_count": len(documents),
        "by_topic": {topic: by_topic[topic] for topic in ALLOWED_TOPICS},
        "by_status": {status: by_status[status] for status in ALLOWED_STATUSES},
        "documents": [
            {
                "document_id": doc.document_id,
                "version": doc.version,
                "topic": doc.topic,
                "status": doc.status,
                "effective_from": doc.effective_from.isoformat(),
                "effective_to": (doc.effective_to.isoformat() if doc.effective_to else None),
            }
            for doc in sorted(documents, key=lambda d: (d.document_id, d.version))
        ],
    }


def write_manifest(
    documents: list[Document],
    manifest_path: Path = CORPUS_MANIFEST_PATH,
) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(documents)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
