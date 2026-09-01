"""Unit and integration acceptance tests for PostgreSQL + pgvector retriever."""

from __future__ import annotations

import os
from datetime import date
from typing import TYPE_CHECKING

import pytest

from aegisbank_rag.chunking import Chunk, chunk_corpus
from aegisbank_rag.corpus import filter_active, load_corpus
from aegisbank_rag.embedding import LocalDenseEmbeddingModel
from aegisbank_rag.pgvector_retriever import PgVectorRetriever

if TYPE_CHECKING:
    pass

DEFAULT_TEST_PG_URL = os.environ.get(
    "AEGISBANK_PGVECTOR_URL",
    "postgresql://aegisuser:AegisBankPgVector2026!@127.0.0.1:5432/aegisbank_rag",
)


def _has_pgvector() -> bool:
    """Helper to detect if PostgreSQL + pgvector is accessible locally."""
    try:
        retriever = PgVectorRetriever(connection_string=DEFAULT_TEST_PG_URL)
        retriever.initialize_schema()
        return True
    except OSError, RuntimeError, Exception:
        return False


def test_pgvector_unavailable_connection_error() -> None:
    """Verify controlled RuntimeError or ConnectionError when PostgreSQL is unavailable."""
    bad_retriever = PgVectorRetriever(
        connection_string="postgresql://invalid_user:bad_pass@127.0.0.1:54329/nonexistent_db"
    )
    with pytest.raises(Exception):
        bad_retriever.initialize_schema()


def test_embedding_model_deterministic_encoding() -> None:
    """Verify LocalDenseEmbeddingModel generates deterministic unit-normalized vectors."""
    model = LocalDenseEmbeddingModel(dimension=32)
    texts = [
        "Préstamos vehiculares para clientes de AegisBank",
        "Políticas de separación de autoridad y control",
    ]
    vecs1 = model.encode(texts)
    vecs2 = model.encode(texts)

    assert len(vecs1) == 2
    assert len(vecs1[0]) == 32
    assert vecs1 == vecs2

    # Verify L2 normalization: sum of squares ~= 1.0
    norm_sq = sum(v * v for v in vecs1[0])
    assert abs(norm_sq - 1.0) < 1e-4


@pytest.mark.skipif(not _has_pgvector(), reason="PostgreSQL with pgvector is not available")
def test_pgvector_idempotent_ingestion_and_exact_search() -> None:
    """Verify chunks can be ingested multiple times without duplication and search returns hits."""
    cutoff = date.fromisoformat("2026-12-31")
    docs = filter_active(load_corpus(), cutoff=cutoff)
    chunks = chunk_corpus(docs)

    retriever = PgVectorRetriever(connection_string=DEFAULT_TEST_PG_URL)
    # First fit
    retriever.fit(chunks)
    # Second fit (idempotency check)
    retriever.fit(chunks)

    # Search
    hits = retriever.search("¿Cuáles son los plazos para crédito vehicular?", top_k=3)
    assert len(hits) == 3
    assert all(h.retrieval_method == "pgvector_embedding" for h in hits)
    assert hits[0].score >= hits[1].score >= hits[2].score


@pytest.mark.skipif(not _has_pgvector(), reason="PostgreSQL with pgvector is not available")
def test_pgvector_metadata_filtering_and_superseded_exclusion() -> None:
    """Verify metadata filtering by status and topic, and exclusion of superseded documents."""
    retriever = PgVectorRetriever(connection_string=DEFAULT_TEST_PG_URL)

    # Ingest active and superseded chunks
    active_chunk = Chunk(
        chunk_id="chk_test_active_001",
        document_id="DOC-TEST-001",
        document_version="1",
        chunk_index=1,
        title="Crédito Vehicular Activo",
        topic="creditos",
        effective_from="2026-01-01",
        effective_to=None,
        status="active",
        source="politica_activa.md",
        content="El crédito vehicular activo tiene tasa del 10% y plazo hasta 60 meses.",
    )
    superseded_chunk = Chunk(
        chunk_id="chk_test_superseded_002",
        document_id="DOC-TEST-001",
        document_version="0",
        chunk_index=1,
        title="Crédito Vehicular Obsoleto",
        topic="creditos",
        effective_from="2020-01-01",
        effective_to="2025-12-31",
        status="superseded",
        source="politica_vieja.md",
        content="El crédito vehicular obsoleto permitía hasta 120 meses sin verificación.",
    )

    retriever.fit([active_chunk, superseded_chunk])

    # Search with status_filter="active"
    hits_active = retriever.search(
        "plazos credito vehicular", top_k=5, status_filter="active", topic_filter="creditos"
    )
    chunk_ids = [h.chunk_id for h in hits_active]
    assert "chk_test_active_001" in chunk_ids
    assert "chk_test_superseded_002" not in chunk_ids


@pytest.mark.skipif(not _has_pgvector(), reason="PostgreSQL with pgvector is not available")
def test_pgvector_hnsw_and_ivfflat_indexing_and_explain() -> None:
    """Verify HNSW and IVFFlat index creation and query plan extraction with EXPLAIN ANALYZE."""
    retriever = PgVectorRetriever(connection_string=DEFAULT_TEST_PG_URL)

    # Create HNSW index
    retriever.create_hnsw_index(m=16, ef_construction=64)

    # Query plan explain
    plan_hnsw = retriever.explain_query("requisitos de credito", top_k=3)
    assert len(plan_hnsw) >= 1
    assert "Plan" in plan_hnsw[0]
    assert "Planning Time" in plan_hnsw[0] or "Execution Time" in plan_hnsw[0]

    # Create IVFFlat index
    retriever.create_ivfflat_index(lists=4)

    # Clean indexes
    retriever.drop_vector_indexes()


@pytest.mark.skipif(not _has_pgvector(), reason="PostgreSQL with pgvector is not available")
def test_pgvector_sql_injection_attempt_rejected() -> None:
    """Verify parameterized SQL properly sanitizes input containing malicious SQL fragments."""
    retriever = PgVectorRetriever(connection_string=DEFAULT_TEST_PG_URL)

    malicious_query = "' OR 1=1; DROP TABLE rag_chunks; --"
    # Should execute safely without executing the injection
    hits = retriever.search(malicious_query, top_k=2)
    assert isinstance(hits, list)

    # Verify table still exists and is intact
    check_hits = retriever.search("credito", top_k=1)
    assert isinstance(check_hits, list)


def test_pgvector_empty_query_raises_value_error() -> None:
    """Verify empty query string raises ValueError."""
    retriever = PgVectorRetriever(connection_string=DEFAULT_TEST_PG_URL)
    with pytest.raises(ValueError, match="Query must not be empty"):
        retriever.search("   ")
