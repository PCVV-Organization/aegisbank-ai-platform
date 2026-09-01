"""Redis Vector Search Retriever using RediSearch and HNSW cosine similarity.

Implements the canonical Retriever interface for low-latency vector similarity search
over authorized AegisBank corpus chunks.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from typing import Any

import numpy as np
import redis
from redis.commands.search.query import Query
from redis.exceptions import ResponseError

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.embedding import LocalDenseEmbeddingModel
from aegisbank_rag.retriever import RetrievalHit, Retriever

logger = logging.getLogger(__name__)

DEFAULT_REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
DEFAULT_INDEX_NAME = "idx:aegisbank_rag"
DEFAULT_PREFIX = "aegisbank:rag_chunk:"
VECTOR_DIMENSION = 32


class RedisVectorRetriever(Retriever):
    """Retriever implementation backed by Redis Search Vector Index (HNSW)."""

    def __init__(
        self,
        redis_url: str = DEFAULT_REDIS_URL,
        *,
        index_name: str = DEFAULT_INDEX_NAME,
        prefix: str = DEFAULT_PREFIX,
        model: LocalDenseEmbeddingModel | None = None,
        dimension: int = VECTOR_DIMENSION,
        max_connections: int = 10,
    ) -> None:
        self.name = "redis_vector_search"
        self.redis_url = redis_url
        self.index_name = index_name
        self.prefix = prefix
        self.dimension = dimension
        self._model = model or LocalDenseEmbeddingModel(dimension=dimension)

        self._pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=False,  # Need raw bytes for vector payloads
        )
        self._client: redis.Redis[bytes] = redis.Redis(connection_pool=self._pool)

    def ensure_schema(self, *, force_recreate: bool = False) -> None:
        """Create or verify the RediSearch vector index."""
        if force_recreate:
            try:
                self._client.ft(self.index_name).dropindex(delete_documents=True)
            except ResponseError:
                pass

        try:
            self._client.ft(self.index_name).info()
            logger.debug("Redis vector index %s already exists.", self.index_name)
            return
        except ResponseError:
            # Index does not exist; create it
            pass

        # Create schema using raw FT.CREATE command
        schema_cmd = [
            "FT.CREATE",
            self.index_name,
            "ON",
            "HASH",
            "PREFIX",
            "1",
            self.prefix,
            "SCHEMA",
            "chunk_id",
            "TAG",
            "document_id",
            "TAG",
            "document_version",
            "TAG",
            "status",
            "TAG",
            "topic",
            "TAG",
            "source",
            "TAG",
            "effective_from",
            "TAG",
            "effective_to",
            "TAG",
            "title",
            "TEXT",
            "content",
            "TEXT",
            "embedding",
            "VECTOR",
            "HNSW",
            "6",
            "TYPE",
            "FLOAT32",
            "DIM",
            str(self.dimension),
            "DISTANCE_METRIC",
            "COSINE",
        ]
        self._client.execute_command(*schema_cmd)
        logger.info("Created Redis vector index %s with HNSW cosine metric.", self.index_name)

    def fit(self, chunks: Sequence[Chunk]) -> None:
        """Fit embedding model and ingest corpus chunks into Redis vector index."""
        if not chunks:
            return
        contents = [c.content for c in chunks]
        self._model.fit(contents)
        self.ingest_chunks(chunks)

    def ingest_chunks(self, chunks: Sequence[Chunk]) -> int:
        """Ingest canonical corpus chunks into Redis with dense vector embeddings."""
        if not chunks:
            return 0

        self.ensure_schema()
        contents = [c.content for c in chunks]
        vectors = self._model.encode(contents)

        pipeline = self._client.pipeline(transaction=False)
        for chunk, vector in zip(chunks, vectors, strict=True):
            vec_arr = np.array(vector, dtype=np.float32)
            if vec_arr.shape[0] != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self.dimension}, got {vec_arr.shape[0]}"
                )
            if np.isnan(vec_arr).any() or np.isinf(vec_arr).any():
                raise ValueError(
                    f"Malformed embedding vector with NaN/Inf for chunk {chunk.chunk_id}"
                )

            key = f"{self.prefix}{chunk.chunk_id}".encode("utf-8")
            mapping: dict[bytes, bytes] = {
                b"chunk_id": chunk.chunk_id.encode("utf-8"),
                b"document_id": chunk.document_id.encode("utf-8"),
                b"document_version": chunk.document_version.encode("utf-8"),
                b"status": chunk.status.encode("utf-8"),
                b"topic": chunk.topic.encode("utf-8"),
                b"source": chunk.source.encode("utf-8"),
                b"effective_from": chunk.effective_from.encode("utf-8"),
                b"effective_to": (chunk.effective_to or "").encode("utf-8"),
                b"title": chunk.title.encode("utf-8"),
                b"content": chunk.content.encode("utf-8"),
                b"embedding": vec_arr.tobytes(),
            }
            pipeline.hset(key, mapping=mapping)  # type: ignore[arg-type]

        pipeline.execute()
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        *,
        status: str = "active",
        topic: str | None = None,
    ) -> list[RetrievalHit]:
        """Perform KNN vector similarity search with optional metadata filtering."""
        query_vector = self._model.encode_one(query)
        vec_arr = np.array(query_vector, dtype=np.float32)
        if vec_arr.shape[0] != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.dimension}, "
                f"got {vec_arr.shape[0]}"
            )
        if np.isnan(vec_arr).any() or np.isinf(vec_arr).any():
            raise ValueError("Malformed query embedding vector with NaN/Inf")

        # Build RediSearch filter
        if topic:
            filter_expr = f"(@status:{{{status}}} @topic:{{{topic}}})"
        else:
            filter_expr = f"(@status:{{{status}}})"

        query_str = f"{filter_expr}=>[KNN {top_k} @embedding $query_vec AS vector_distance]"
        q = (
            Query(query_str)
            .sort_by("vector_distance")
            .return_fields(
                "chunk_id",
                "document_id",
                "document_version",
                "status",
                "topic",
                "source",
                "effective_from",
                "effective_to",
                "title",
                "content",
                "vector_distance",
            )
            .dialect(2)
        )

        params: dict[str, Any] = {"query_vec": vec_arr.tobytes()}
        try:
            res = self._client.ft(self.index_name).search(q, query_params=params)
        except ResponseError as err:
            logger.warning("Redis vector search failed: %s", err)
            return []

        hits: list[RetrievalHit] = []
        for rank, doc in enumerate(res.docs, start=1):
            dist = float(getattr(doc, "vector_distance", 1.0))
            score = max(0.0, 1.0 - dist)
            hits.append(
                RetrievalHit(
                    document_id=_decode_field(getattr(doc, "document_id", b"")),
                    document_version=_decode_field(getattr(doc, "document_version", b"")),
                    chunk_id=_decode_field(getattr(doc, "chunk_id", b"")),
                    title=_decode_field(getattr(doc, "title", b"")),
                    topic=_decode_field(getattr(doc, "topic", b"")),
                    content=_decode_field(getattr(doc, "content", b"")),
                    source=_decode_field(getattr(doc, "source", b"")),
                    status=_decode_field(getattr(doc, "status", b"")),
                    effective_from=_decode_field(getattr(doc, "effective_from", b"")),
                    effective_to=_decode_field(getattr(doc, "effective_to", b"")),
                    score=score,
                    rank=rank,
                    retrieval_method=self.name,
                )
            )

        return hits


def _decode_field(value: Any) -> str:
    """Safely decode bytes or string field from Redis Search document."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value) if value is not None else ""
