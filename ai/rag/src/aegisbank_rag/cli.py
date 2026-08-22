"""Command-line interface for the v0.4 RAG retrieval foundation."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aegisbank_rag.chunking import Chunk, chunk_corpus
from aegisbank_rag.constants import (
    CORPUS_DIR,
    CORPUS_MANIFEST_PATH,
    DEFAULT_K,
    METRICS_PATH,
    REPORT_PATH,
)
from aegisbank_rag.corpus import Document, load_corpus, write_manifest
from aegisbank_rag.evaluation import (
    build_active_corpus,
    evaluate,
    load_qrels,
    load_queries,
    make_retrievers,
    write_evaluation_reports,
)
from aegisbank_rag.retriever import Retriever


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aegisbank-rag",
        description="Local retrieval foundation for AegisBank RAG v0.4",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser(
        "index",
        help="Load the corpus, chunk it, refresh the manifest, persist metadata",
    )
    index_parser.add_argument("--corpus-dir", type=Path, default=CORPUS_DIR)
    index_parser.add_argument("--manifest-output", type=Path, default=CORPUS_MANIFEST_PATH)

    search_parser = subparsers.add_parser(
        "search", help="Run a single query through one or all retrievers"
    )
    search_parser.add_argument("query")
    search_parser.add_argument("--top-k", type=int, default=DEFAULT_K)
    search_parser.add_argument(
        "--method",
        choices=("lexical_tfidf", "dense_local_lsa", "hybrid_rrf", "all"),
        default="all",
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Run the frozen offline evaluation and refresh reports"
    )
    evaluate_parser.add_argument("--top-k", type=int, default=DEFAULT_K)
    evaluate_parser.add_argument("--metrics-output", type=Path, default=METRICS_PATH)
    evaluate_parser.add_argument("--report-output", type=Path, default=REPORT_PATH)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "index":
            return int(_handle_index(args))
        if args.command == "search":
            return int(_handle_search(args))
        if args.command == "evaluate":
            return int(_handle_evaluate(args))
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


def _handle_index(args: argparse.Namespace) -> int:
    documents = load_corpus(args.corpus_dir)
    write_manifest(documents, args.manifest_output)
    chunks: list[Chunk] = chunk_corpus(documents)
    payload: dict[str, Any] = {
        "result": "indexed",
        "corpus_size": len(documents),
        "chunk_count": len(chunks),
        "manifest": str(args.manifest_output),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _handle_search(args: argparse.Namespace) -> int:
    documents: list[Document] = build_active_corpus()
    chunks: list[Chunk] = list(chunk_corpus(documents))
    retrievers = make_retrievers()
    for retriever in retrievers.values():
        retriever.fit(chunks)
    methods = list(retrievers) if args.method == "all" else [args.method]
    query = args.query.strip()
    if not query:
        raise ValueError("Query must not be empty")
    output: dict[str, Any] = {
        "query": query,
        "top_k": args.top_k,
        "results": {},
    }
    for method in methods:
        retriever = retrievers[method]
        hits = retriever.search(query, top_k=args.top_k)
        output["results"][method] = [hit.as_dict() for hit in hits]
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _handle_evaluate(args: argparse.Namespace) -> int:
    documents = build_active_corpus()
    chunks: list[Chunk] = list(chunk_corpus(documents))
    queries = load_queries()
    qrels = load_qrels()
    retrievers = make_retrievers()
    report = evaluate(chunks, queries, qrels, retrievers, top_k=args.top_k)
    write_evaluation_reports(report, args.metrics_output, args.report_output)
    summary = {
        "result": "evaluated",
        "primary_metric": report["primary_metric"],
        "top_k": report["top_k"],
        "queries_evaluated": report["queries_evaluated"],
        "metrics_path": str(args.metrics_output),
        "report_path": str(args.report_output),
        "aggregates": {
            method: {
                "ndcg_at_5": metrics["ndcg_at_5"]["mean"],
                "mrr_at_5": metrics["mrr_at_5"]["mean"],
            }
            for method, metrics in report["aggregates"].items()
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _active_retrievers(
    retrievers: dict[str, Retriever], methods: Sequence[str]
) -> dict[str, Retriever]:
    if set(methods) == {"all"}:
        return retrievers
    return {name: retrievers[name] for name in methods}


if __name__ == "__main__":
    raise SystemExit(main())
