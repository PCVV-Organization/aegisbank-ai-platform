"""Evaluation script for v0.12 comparing historical retrievers with PostgreSQL + pgvector."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import filter_active, load_corpus
from aegisbank_rag.dense_local import DenseLocalRetriever
from aegisbank_rag.evaluation import evaluate, load_qrels, load_queries
from aegisbank_rag.hybrid import HybridRRFRetriever
from aegisbank_rag.lexical import LexicalRetriever
from aegisbank_rag.pgvector_retriever import PgVectorRetriever


def run_v012_evaluation() -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = repo_root / "docs" / "evaluation"
    reports_dir.mkdir(parents=True, exist_ok=True)

    queries = load_queries()
    qrels = load_qrels()
    cutoff = date.fromisoformat("2026-12-31")
    corpus = filter_active(load_corpus(), cutoff=cutoff)
    chunks = chunk_corpus(corpus)

    from aegisbank_rag.pgvector_retriever import DEFAULT_PG_URL

    pg_url = os.environ.get("AEGISBANK_PGVECTOR_URL", DEFAULT_PG_URL)

    retrievers = {
        LexicalRetriever().name: LexicalRetriever(),
        DenseLocalRetriever().name: DenseLocalRetriever(),
        HybridRRFRetriever().name: HybridRRFRetriever(),
        PgVectorRetriever(connection_string=pg_url).name: PgVectorRetriever(
            connection_string=pg_url
        ),
    }

    report = evaluate(chunks, queries, qrels, retrievers, top_k=5)

    output_path = reports_dir / "v012_retrieval_comparison.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[+] v0.12 Retrieval Comparison Report saved to {output_path}")

    print("\n" + "=" * 75)
    print("AEGISBANK RAG RETRIEVAL COMPARISON SUMMARY (Top-K=5)")
    print("=" * 75)
    print(
        f"{'Retriever Method':<24} | {'nDCG@5':<10} | {'MRR@5':<10} | {'Precision@5':<12} | {'Recall@5':<10}"
    )
    print("-" * 75)
    for method, agg in report["aggregates"].items():
        ndcg = agg["ndcg_at_5"]["mean"]
        mrr = agg["mrr_at_5"]["mean"]
        prec = agg["precision_at_5"]["mean"]
        rec = agg["recall_at_5"]["mean"]
        print(
            f"{method:<24} | {ndcg:<10.4f} | {mrr:<10.4f} | {prec:<12.4f} | {rec:<10.4f}"
        )
    print("=" * 75)

    return report


if __name__ == "__main__":
    run_v012_evaluation()
