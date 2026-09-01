"""Acceptance and unit tests for RedisVectorRetriever using RediSearch (v0.12.2).

Verifies vector schema creation, dense embedding ingestion, KNN search,
status/topic filtering, dimension validation, idempotency, and ranking quality.
"""

from __future__ import annotations

import pytest
import redis

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import load_corpus
from aegisbank_rag.embedding import LocalDenseEmbeddingModel
from aegisbank_rag.redis_retriever import (
    DEFAULT_REDIS_URL,
    VECTOR_DIMENSION,
    RedisVectorRetriever,
)


def _is_redis_running() -> bool:
    try:
        r = redis.Redis.from_url(DEFAULT_REDIS_URL, socket_timeout=0.5)
        return bool(r.ping())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _is_redis_running(),
    reason="Redis server is not running on 127.0.0.1:6379",
)


@pytest.fixture(scope="module")
def corpus_chunks():
    docs = load_corpus()
    chunks = chunk_corpus(docs)
    assert len(chunks) > 0
    return chunks


@pytest.fixture(scope="module")
def shared_embedding_model(corpus_chunks):
    model = LocalDenseEmbeddingModel(dimension=VECTOR_DIMENSION)
    contents = [c.content for c in corpus_chunks]
    model.fit(contents)
    return model


@pytest.fixture
def redis_retriever(corpus_chunks, shared_embedding_model) -> RedisVectorRetriever:
    retriever = RedisVectorRetriever(
        index_name="idx:test_aegisbank_rag",
        prefix="aegisbank:test_chunk:",
        model=shared_embedding_model,
        dimension=VECTOR_DIMENSION,
    )
    retriever.ensure_schema(force_recreate=True)
    retriever.ingest_chunks(corpus_chunks)
    return retriever


def test_redis_vector_index_creation_and_ingest(
    redis_retriever: RedisVectorRetriever, corpus_chunks
) -> None:
    """Verify index creation and chunk ingestion count."""
    count = redis_retriever.ingest_chunks(corpus_chunks)
    assert count == len(corpus_chunks)


def test_redis_vector_knn_search_and_ranking(redis_retriever: RedisVectorRetriever) -> None:
    """Verify KNN similarity search returns ranked hits with valid scores."""
    hits = redis_retriever.search("¿Cuál es el plazo máximo para un crédito personal?", top_k=5)
    assert len(hits) > 0
    assert len(hits) <= 5

    # Check descending score order
    for i in range(len(hits) - 1):
        assert hits[i].score >= hits[i + 1].score

    # Check top hit relevance
    top_hit = hits[0]
    assert top_hit.status == "active"
    assert top_hit.retrieval_method == "redis_vector_search"
    assert len(top_hit.content) > 0


def test_redis_vector_metadata_filter_topic_and_status(
    redis_retriever: RedisVectorRetriever,
) -> None:
    """Verify search respects metadata filters (topic and active status)."""
    hits = redis_retriever.search("requisitos y tasas", top_k=5, topic="reclamos")
    for hit in hits:
        assert hit.topic == "reclamos"
        assert hit.status == "active"


def test_redis_vector_dimension_mismatch_rejected(shared_embedding_model, corpus_chunks) -> None:
    """Verify ValueError is raised when vector dimension does not match index dimension."""
    bad_retriever = RedisVectorRetriever(
        index_name="idx:test_bad_dim",
        model=shared_embedding_model,
        dimension=64,  # Mismatch with 32-dim model
    )
    chunks = corpus_chunks[:1]
    with pytest.raises(ValueError, match="Vector dimension mismatch"):
        bad_retriever.ingest_chunks(chunks)


def test_redis_vector_duplicate_ingest_is_idempotent(
    redis_retriever: RedisVectorRetriever, corpus_chunks
) -> None:
    """Verify re-ingesting the same chunks updates existing hashes without creating duplicates."""
    count1 = redis_retriever.ingest_chunks(corpus_chunks)
    count2 = redis_retriever.ingest_chunks(corpus_chunks)
    assert count1 == count2 == len(corpus_chunks)

    # Search should still return expected top_k hits, not duplicates
    hits = redis_retriever.search("reclamos comisiones", top_k=3)
    assert len(hits) <= 3
    chunk_ids = [h.chunk_id for h in hits]
    assert len(chunk_ids) == len(set(chunk_ids))
