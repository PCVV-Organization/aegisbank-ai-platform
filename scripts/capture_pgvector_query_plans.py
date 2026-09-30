"""Capture reproducible local pgvector query plans for the v0.12 evidence record."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import filter_active, load_corpus
from aegisbank_rag.pgvector_retriever import PgVectorRetriever


def main() -> int:
    from aegisbank_rag.pgvector_retriever import DEFAULT_PG_URL

    pg_url = os.environ.get("AEGISBANK_PGVECTOR_URL", DEFAULT_PG_URL)
    retriever = PgVectorRetriever(connection_string=pg_url)
    chunks = chunk_corpus(filter_active(load_corpus(), cutoff=date(2026, 12, 31)))
    retriever.fit(chunks)
    plans: dict[str, object] = {}
    retriever.drop_vector_indexes()
    plans["exact"] = retriever.explain_query("requisitos de crédito", top_k=5)
    retriever.create_hnsw_index()
    plans["hnsw"] = retriever.explain_query("requisitos de crédito", top_k=5)
    retriever.drop_vector_indexes()
    retriever.create_ivfflat_index()
    plans["ivfflat"] = retriever.explain_query("requisitos de crédito", top_k=5)
    retriever.drop_vector_indexes()
    output = Path("reports/evaluation/v012-pgvector-query-plans.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plans, indent=2), encoding="utf-8")
    print(f"query plans saved to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
