from datetime import date

import pytest

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import filter_active
from aegisbank_rag.lexical import LexicalRetriever


def test_lexical_retrieval_returns_active_chunks_first(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    active = filter_active(documents, cutoff=cutoff)
    chunks = chunk_corpus(active)
    retriever = LexicalRetriever()
    retriever.fit(chunks)
    hits = retriever.search("crédito personal simulado rango monto plazo", top_k=3)
    assert hits
    for hit in hits:
        assert hit.status == "active"
        if hit.document_id == "creditos_producto_general":
            assert hit.document_version == "v2"


def test_lexical_retrieval_is_deterministic(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = LexicalRetriever()
    retriever.fit(chunks)
    query = "tasas de interés y comisiones"
    first = [hit.chunk_id for hit in retriever.search(query, top_k=3)]
    second = [hit.chunk_id for hit in retriever.search(query, top_k=3)]
    assert first == second


def test_lexical_retrieval_finds_reclamos_query(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = LexicalRetriever()
    retriever.fit(chunks)
    hits = retriever.search("¿Cómo se crea un reclamo ficticio?", top_k=3)
    assert hits
    assert "reclamos" in {hit.topic for hit in hits}


def test_lexical_retrieval_rejects_empty_query(documents) -> None:
    chunks = chunk_corpus(filter_active(documents, cutoff=date.fromisoformat("2026-12-31")))
    retriever = LexicalRetriever()
    retriever.fit(chunks)
    with pytest.raises(ValueError, match="non-empty|empty|strip"):
        retriever.search("   ", top_k=3)
