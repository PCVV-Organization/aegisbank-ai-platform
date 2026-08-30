"""Command-line interface for the v0.4 RAG retrieval foundation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aegisbank_rag.chunking import Chunk, chunk_corpus
from aegisbank_rag.constants import (
    CORPUS_DIR,
    CORPUS_MANIFEST_PATH,
    DEFAULT_K,
    GENERATION_METRICS_PATH,
    GENERATION_REPORT_PATH,
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
from aegisbank_rag.foundry_local import (
    DEFAULT_MODEL_ALIAS,
    FoundryLocalProvider,
    resolve_foundry_base_url,
)
from aegisbank_rag.generation import parse_grounded_answer
from aegisbank_rag.generation_evaluation import (
    evaluate_generation,
    load_generation_cases,
    write_generation_reports,
)
from aegisbank_rag.prompting import load_prompt
from aegisbank_rag.provider import LLMRequest
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

    gen_evaluate_parser = subparsers.add_parser(
        "evaluate-generation",
        help="Run generation evaluation against frozen contexts via Foundry Local",
    )
    gen_evaluate_parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_ALIAS,
    )
    gen_evaluate_parser.add_argument(
        "--metrics-output",
        type=Path,
        default=GENERATION_METRICS_PATH,
    )
    gen_evaluate_parser.add_argument(
        "--report-output",
        type=Path,
        default=GENERATION_REPORT_PATH,
    )
    gen_evaluate_parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Foundry Local base URL (resolved from status if not provided)",
    )

    smoke_parser = subparsers.add_parser(
        "smoke",
        help="Run one local Foundry Local contract smoke call",
    )
    smoke_parser.add_argument("--model", type=str, default=DEFAULT_MODEL_ALIAS)
    smoke_parser.add_argument("--base-url", type=str, default=None)

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
        if args.command == "evaluate-generation":
            return int(_handle_evaluate_generation(args))
        if args.command == "smoke":
            return int(_handle_smoke(args))
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
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


def _handle_evaluate_generation(args: argparse.Namespace) -> int:
    if args.metrics_output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing generation metrics: {args.metrics_output}. "
            "Remove or rename the file before re-running."
        )
    base_url = args.base_url or resolve_foundry_base_url()
    provider = FoundryLocalProvider(model=args.model, base_url=base_url)
    prompt = load_prompt()
    cases = load_generation_cases()
    chunks = list(chunk_corpus(load_corpus(CORPUS_DIR)))
    report = evaluate_generation(provider, prompt, cases, chunks)
    report["runtime"] = {
        "provider": provider.provider_name,
        "foundry_local_version": _foundry_local_version(),
        "model_alias": provider.model_name,
        "model_ids": provider.served_model_ids(),
        "base_url": provider.base_url,
        "external_network_traffic": False,
    }
    write_generation_reports(report, args.metrics_output, args.report_output)
    _log_runtime_sanitized(provider, base_url)
    summary = {
        "result": "generation_evaluated",
        "provider": report["provider"],
        "model": report["model"],
        "prompt_version": report["prompt_version"],
        "cases_evaluated": report["cases_evaluated"],
        "metrics_path": str(args.metrics_output),
        "report_path": str(args.report_output),
        "aggregates": report["aggregates"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _handle_smoke(args: argparse.Namespace) -> int:
    base_url = args.base_url or resolve_foundry_base_url()
    provider = FoundryLocalProvider(model=args.model, base_url=base_url)
    request = LLMRequest(
        prompt_version="smoke",
        system_prompt="Devuelve únicamente JSON válido con answer, citations y abstained.",
        user_prompt='{"answer":"ok","citations":[],"abstained":true}',
        response_schema={"type": "object"},
    )
    parsed = parse_grounded_answer(provider.generate(request))
    if not parsed.abstained or parsed.citations:
        raise ValueError("Smoke response did not satisfy the structured contract")
    print(
        json.dumps(
            {
                "result": "SMOKE_PASS",
                "provider": provider.provider_name,
                "model": provider.model_name,
                "endpoint_local": base_url.startswith("http://127.0.0.1:"),
                "parsed": True,
            },
            sort_keys=True,
        )
    )
    return 0


def _foundry_local_version() -> str:
    completed = subprocess.run(["foundry", "--version"], capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def _log_runtime_sanitized(provider: FoundryLocalProvider, base_url: str) -> None:
    redacted_url = base_url.replace("http://", "").replace("https://", "")
    if "@" in redacted_url:
        redacted_url = redacted_url.split("@", 1)[-1]
    msg = (
        f"RUNTIME: foundry-local provider={provider.provider_name} "
        f"model={provider.model_name} endpoint={redacted_url}"
    )
    print(msg, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
