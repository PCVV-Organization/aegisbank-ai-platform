"""Offline retrieval evaluation pipeline for v0.4."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from importlib.metadata import version
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.constants import (
    DEFAULT_K,
    EXPERIMENT_NAME,
    EXPERIMENT_VERSION,
    METRICS_PATH,
    PRIMARY_METRIC,
    QRELS_PATH,
    QUERIES_PATH,
    RANDOM_STATE,
    REPORT_PATH,
)
from aegisbank_rag.corpus import Document, filter_active, load_corpus
from aegisbank_rag.dense_local import DenseLocalRetriever
from aegisbank_rag.hybrid import HybridRRFRetriever
from aegisbank_rag.lexical import LexicalRetriever
from aegisbank_rag.metrics import METRIC_NAMES, compute_metrics
from aegisbank_rag.retriever import RetrievalHit, Retriever


@dataclass(frozen=True, slots=True)
class QueryRecord:
    query_id: str
    category: str
    text: str

    def as_dict(self) -> dict[str, str]:
        return {
            "query_id": self.query_id,
            "category": self.category,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class Qrel:
    query_id: str
    category: str
    relevant: tuple[str, ...]


def load_queries(
    queries_path: Path = QUERIES_PATH,
) -> list[QueryRecord]:
    queries: list[QueryRecord] = []
    for line_number, line in enumerate(
        queries_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        payload = json.loads(line)
        if set(payload) != {"query_id", "category", "text"}:
            raise ValueError(
                f"queries.jsonl line {line_number} has unexpected fields: {sorted(payload)}"
            )
        queries.append(
            QueryRecord(
                query_id=payload["query_id"],
                category=payload["category"],
                text=payload["text"],
            )
        )
    if not queries:
        raise ValueError("queries.jsonl must contain at least one query")
    return queries


def load_qrels(qrels_path: Path = QRELS_PATH) -> list[Qrel]:
    payload = json.loads(qrels_path.read_text(encoding="utf-8"))
    qrels = [
        Qrel(
            query_id=item["query_id"],
            category=item["category"],
            relevant=tuple(item["relevant"]),
        )
        for item in payload["qrels"]
    ]
    if not qrels:
        raise ValueError("qrels.json must contain at least one entry")
    return qrels


def build_active_corpus(
    documents: Sequence[Document] | None = None,
    *,
    cutoff: date | None = None,
) -> list[Document]:
    corpus = documents if documents is not None else load_corpus()
    if cutoff is None:
        cutoff = date.fromisoformat("2026-12-31")
    return filter_active(corpus, cutoff=cutoff)


def make_retrievers() -> dict[str, Retriever]:
    return {
        LexicalRetriever().name: LexicalRetriever(),
        DenseLocalRetriever().name: DenseLocalRetriever(),
        HybridRRFRetriever().name: HybridRRFRetriever(),
    }


def evaluate(
    chunks: Sequence[Chunk],
    queries: Sequence[QueryRecord],
    qrels: Sequence[Qrel],
    retrievers: dict[str, Retriever],
    *,
    top_k: int = DEFAULT_K,
) -> dict[str, Any]:
    for retriever in retrievers.values():
        retriever.fit(chunks)
    qrels_by_id = {qrel.query_id: qrel for qrel in qrels}
    per_method: dict[str, list[dict[str, Any]]] = {name: [] for name in retrievers}
    misclassified: dict[str, list[dict[str, Any]]] = {name: [] for name in retrievers}
    for query in queries:
        qrel = qrels_by_id.get(query.query_id)
        if qrel is None:
            continue
        relevant = list(qrel.relevant)
        for name, retriever in retrievers.items():
            hits = retriever.search(query.text, top_k=top_k)
            retrieved = [hit.chunk_id for hit in hits]
            metrics = compute_metrics(retrieved, relevant, k=top_k)
            entry: dict[str, Any] = {
                "query_id": query.query_id,
                "category": query.category,
                "metrics": metrics,
                "retrieved": retrieved,
                "relevant": relevant,
                "abstracted_relevant_count": len(relevant),
                "abstracted_top_k": top_k,
            }
            per_method[name].append(entry)
            if qrel.category == "ood" and retrieved:
                misclassified[name].append(
                    {
                        "query_id": query.query_id,
                        "text": query.text,
                        "retrieved": retrieved,
                    }
                )
            elif qrel.category != "ood" and not any(chunk_id in relevant for chunk_id in retrieved):
                misclassified[name].append(
                    {
                        "query_id": query.query_id,
                        "text": query.text,
                        "retrieved": retrieved,
                    }
                )
    aggregates: dict[str, dict[str, dict[str, float]]] = {}
    for name, entries in per_method.items():
        aggregated: dict[str, dict[str, float]] = {}
        for metric_name in METRIC_NAMES:
            values = [entry["metrics"][metric_name] for entry in entries]
            if values:
                aggregated[metric_name] = {
                    "mean": round(float(fmean(values)), 12),
                    "std": round(float(pstdev(values)), 12),
                    "min": round(float(min(values)), 12),
                    "max": round(float(max(values)), 12),
                }
            else:
                aggregated[metric_name] = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        aggregates[name] = aggregated
    category_breakdown: dict[str, dict[str, dict[str, float]]] = {}
    for name, entries in per_method.items():
        per_category: dict[str, list[dict[str, float]]] = {}
        for entry in entries:
            per_category.setdefault(entry["category"], []).append(entry["metrics"])
        breakdown: dict[str, dict[str, float]] = {}
        for category, metrics_list in per_category.items():
            if not metrics_list:
                continue
            breakdown[category] = {
                metric_name: round(
                    float(fmean(metric[metric_name] for metric in metrics_list)),
                    12,
                )
                for metric_name in METRIC_NAMES
            }
        category_breakdown[name] = breakdown
    return {
        "experiment_name": EXPERIMENT_NAME,
        "experiment_version": EXPERIMENT_VERSION,
        "primary_metric": PRIMARY_METRIC,
        "queries_evaluated": len(queries),
        "qrels_evaluated": len(qrels),
        "top_k": top_k,
        "random_state": RANDOM_STATE,
        "per_method": per_method,
        "misclassified": misclassified,
        "aggregates": aggregates,
        "category_breakdown": category_breakdown,
        "software": {
            "scikit_learn": version("scikit-learn"),
            "numpy": version("numpy"),
        },
    }


def write_evaluation_reports(
    report: dict[str, Any],
    metrics_path: Path = METRICS_PATH,
    report_path: Path = REPORT_PATH,
) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    rendered = render_report(report)
    report_path.write_text(rendered, encoding="utf-8", newline="\n")


def render_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# v0.4 RAG Retrieval Report")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "Local, byte-deterministic retrieval foundation over a synthetic "
        "Spanish banking corpus. The primary metric is "
        f"`{report['primary_metric']}`."
    )
    lines.append("")
    lines.append("## Aggregated Metrics @ top-5")
    lines.append("")
    lines.append("| Method | nDCG@5 | MRR@5 | Precision@5 | Recall@5 |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for method, metrics in report["aggregates"].items():
        lines.append(
            f"| {method} | "
            f"{metrics['ndcg_at_5']['mean']:.6f} | "
            f"{metrics['mrr_at_5']['mean']:.6f} | "
            f"{metrics['precision_at_5']['mean']:.6f} | "
            f"{metrics['recall_at_5']['mean']:.6f} |"
        )
    lines.append("")
    lines.append("## Per-category breakdown @ top-5")
    lines.append("")
    for method, breakdown in report["category_breakdown"].items():
        lines.append(f"### {method}")
        lines.append("")
        lines.append("| Category | nDCG@5 | MRR@5 | Precision@5 | Recall@5 |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for category, metrics in sorted(breakdown.items()):
            lines.append(
                f"| {category} | "
                f"{metrics['ndcg_at_5']:.6f} | "
                f"{metrics['mrr_at_5']:.6f} | "
                f"{metrics['precision_at_5']:.6f} | "
                f"{metrics['recall_at_5']:.6f} |"
            )
        lines.append("")
    lines.append("## Coverage of Out-of-Domain Queries")
    lines.append("")
    lines.append("| Method | OOD queries with no relevant | Hits accidentally returned |")
    lines.append("| --- | ---: | ---: |")
    queries = load_queries()
    ood_count = sum(1 for q in queries if q.category == "ood")
    for method in report["misclassified"]:
        lines.append(f"| {method} | {ood_count} | {len(report['misclassified'][method])} |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- All corpora, queries, and qrels are synthetic. Metrics therefore "
        "describe behaviour on the controlled corpus and not on real banking "
        "traffic."
    )
    lines.append(
        "- LSA dense vectors are a purely local baseline; they do not "
        "approximate modern embedders nor Azure AI Search ranking."
    )
    lines.append(
        "- Hybrid RRF combines lexical and dense rankings with a fixed "
        "`k=60`. The value is frozen for `v0.4`; tuning is out of scope."
    )
    lines.append(
        "- Out-of-domain queries are expected to return no relevant chunk. "
        "If a method surfaces a non-empty list for an OOD query it is "
        "counted as accidental and may justify future thresholding."
    )
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- The corpus is small, hand-authored, and fully synthetic.")
    lines.append(
        "- TruncatedSVD/LSA cannot represent out-of-vocabulary tokens and "
        "shows limited paraphrastic strength."
    )
    lines.append(
        "- The hybrid ranker does not tune weights. Any later optimisation "
        "requires separate authorization and must not be back-applied to "
        "`v0.4` metrics."
    )
    return "\n".join(lines) + "\n"


def retrieve_top_k(
    retriever: Retriever,
    query: str,
    *,
    top_k: int = DEFAULT_K,
) -> list[RetrievalHit]:
    return retriever.search(query, top_k=top_k)
