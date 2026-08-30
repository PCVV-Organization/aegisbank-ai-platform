"""Generation-only evaluation over frozen contexts and reference annotations."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean
from typing import Any, Final

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.constants import (
    GENERATION_EVAL_CASES_PATH,
    GENERATION_METRICS_PATH,
    GENERATION_REPORT_PATH,
)
from aegisbank_rag.context import GroundingContext
from aegisbank_rag.generation import (
    GroundedAnswer,
    GroundingValidationError,
    request_grounded_answer,
    validate_grounded_output,
)
from aegisbank_rag.prompting import PromptDefinition
from aegisbank_rag.provider import LLMProvider
from aegisbank_rag.retriever import RetrievalHit

_TOKEN: Final = re.compile(r"[a-záéíóúüñ0-9]+", re.IGNORECASE)
_STOPWORDS: Final = {
    "como",
    "con",
    "cuando",
    "del",
    "desde",
    "donde",
    "el",
    "ella",
    "en",
    "entre",
    "es",
    "esta",
    "las",
    "los",
    "para",
    "por",
    "que",
    "se",
    "sin",
    "una",
    "uno",
    "unos",
    "y",
}
_CASE_FIELDS: Final = {
    "case_id",
    "category",
    "query",
    "context_chunk_ids",
    "synthetic_retrieval_hits",
    "expected_abstained",
    "reference_facts",
    "required_citation_ids",
    "forbidden_phrases",
}
_FIXTURE_FIELDS: Final = {
    "document_id",
    "version",
    "chunk_id",
    "source",
    "status",
    "content",
}


@dataclass(frozen=True, slots=True)
class SyntheticRetrievalHit:
    document_id: str
    version: str
    chunk_id: str
    source: str
    status: str
    content: str


@dataclass(frozen=True, slots=True)
class GenerationCase:
    case_id: str
    category: str
    query: str
    context_chunk_ids: tuple[str, ...]
    synthetic_retrieval_hits: tuple[SyntheticRetrievalHit, ...]
    expected_abstained: bool
    reference_facts: tuple[str, ...]
    required_citation_ids: tuple[str, ...]
    forbidden_phrases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GenerationMetrics:
    groundedness: float
    answer_relevance: float
    completeness: float | None
    citation_validity: float
    citation_coverage: float
    abstention_correctness: float
    unsupported_claim_rate: float
    prompt_injection_resistance: float


def load_generation_cases(path: Path = GENERATION_EVAL_CASES_PATH) -> list[GenerationCase]:
    cases: list[GenerationCase] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict) or set(payload) != _CASE_FIELDS:
            raise ValueError(f"Generation case line {line_number} has unexpected fields")
        case_id = _required_text(payload, "case_id")
        if case_id in seen:
            raise ValueError(f"Duplicate generation case_id: {case_id}")
        seen.add(case_id)
        cases.append(_parse_case(payload, line_number))
    if not cases:
        raise ValueError("Generation evaluation dataset must not be empty")
    return cases


def resolve_case_hits(case: GenerationCase, chunks: Sequence[Chunk]) -> list[RetrievalHit]:
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    missing = set(case.context_chunk_ids) - set(by_id)
    if missing:
        raise ValueError(f"Unknown context chunks for {case.case_id}: {sorted(missing)}")
    hits: list[RetrievalHit] = []
    for rank, chunk_id in enumerate(case.context_chunk_ids, start=1):
        chunk = by_id[chunk_id]
        hits.append(
            RetrievalHit(
                document_id=chunk.document_id,
                document_version=chunk.document_version,
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                topic=chunk.topic,
                content=chunk.content,
                source=chunk.source,
                status=chunk.status,
                effective_from=chunk.effective_from,
                effective_to=chunk.effective_to,
                score=1.0 / rank,
                rank=rank,
                retrieval_method="generation_eval_frozen_context",
            )
        )
    for fixture in case.synthetic_retrieval_hits:
        rank = len(hits) + 1
        hits.append(
            RetrievalHit(
                document_id=fixture.document_id,
                document_version=fixture.version,
                chunk_id=fixture.chunk_id,
                title="Synthetic adversarial evaluation context",
                topic="generation_evaluation",
                content=fixture.content,
                source=fixture.source,
                status=fixture.status,
                effective_from="2026-01-01",
                effective_to=None,
                score=1.0 / rank,
                rank=rank,
                retrieval_method="generation_eval_synthetic_context",
            )
        )
    return hits


def compute_generation_metrics(
    case: GenerationCase,
    answer: GroundedAnswer,
    context: GroundingContext,
) -> GenerationMetrics:
    entries_by_id = {entry.chunk_id: entry for entry in context.entries}
    valid_citations = [citation for citation in answer.citations if citation in entries_by_id]
    citation_validity = (
        len(valid_citations) / len(answer.citations)
        if answer.citations
        else float(answer.abstained)
    )
    required = set(case.required_citation_ids)
    citation_coverage = (
        len(required.intersection(answer.citations)) / len(required)
        if required
        else float(not answer.citations)
    )
    answer_terms = _terms(answer.answer)
    reference_terms = _terms(" ".join(case.reference_facts))
    evidence_terms: set[str] = set()
    for citation in valid_citations:
        entry = entries_by_id[citation]
        evidence_terms.update(
            _terms(
                " ".join(
                    [
                        entry.content,
                        entry.document_id,
                        entry.version,
                        entry.source,
                    ]
                )
            )
        )
    if answer.abstained:
        groundedness = 1.0
        answer_relevance = float(case.expected_abstained)
    else:
        groundedness = _overlap(answer_terms, evidence_terms)
        answer_relevance = _overlap(answer_terms, reference_terms)
    completeness = _overlap(reference_terms, answer_terms) if reference_terms else None
    forbidden_found = any(
        phrase.casefold() in answer.answer.casefold() or phrase in answer.citations
        for phrase in case.forbidden_phrases
    )
    return GenerationMetrics(
        groundedness=round(groundedness, 12),
        answer_relevance=round(answer_relevance, 12),
        completeness=round(completeness, 12) if completeness is not None else None,
        citation_validity=round(citation_validity, 12),
        citation_coverage=round(citation_coverage, 12),
        abstention_correctness=float(answer.abstained == case.expected_abstained),
        unsupported_claim_rate=round(1.0 - groundedness, 12),
        prompt_injection_resistance=float(not forbidden_found),
    )


def evaluate_generation(
    provider: LLMProvider,
    prompt: PromptDefinition,
    cases: Sequence[GenerationCase],
    chunks: Sequence[Chunk],
) -> dict[str, Any]:
    per_case: list[dict[str, Any]] = []
    for case in cases:
        hits = resolve_case_hits(case, chunks)
        try:
            answer, context = request_grounded_answer(provider, prompt, case.query, hits)
        except GroundingValidationError as exc:
            metrics = _invalid_generation_metrics(case)
            per_case.append(
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "accepted": False,
                    "validation_error": str(exc),
                    "answer": None,
                    "metrics": asdict(metrics),
                }
            )
            continue
        validation_error: str | None = None
        try:
            validate_grounded_output(answer, context, prompt)
        except GroundingValidationError as exc:
            validation_error = str(exc)
        metrics = compute_generation_metrics(case, answer, context)
        per_case.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "accepted": validation_error is None,
                "validation_error": validation_error,
                "answer": answer.as_dict(),
                "metrics": asdict(metrics),
            }
        )
    metric_names = tuple(GenerationMetrics.__dataclass_fields__)
    aggregates: dict[str, float] = {}
    for metric_name in metric_names:
        values = [entry["metrics"][metric_name] for entry in per_case]
        numeric = [value for value in values if value is not None]
        aggregates[metric_name] = round(float(fmean(numeric)), 12) if numeric else 0.0
    return {
        "evaluation_kind": "generation_quality_fixed_context",
        "retrieval_quality_included": False,
        "provider": provider.provider_name,
        "model": provider.model_name,
        "prompt_version": prompt.version,
        "cases_evaluated": len(cases),
        "aggregates": aggregates,
        "per_case": per_case,
    }


def _parse_case(payload: dict[str, Any], line_number: int) -> GenerationCase:
    expected_abstained = payload["expected_abstained"]
    if not isinstance(expected_abstained, bool):
        raise ValueError(f"Generation case line {line_number} has invalid expected_abstained")
    fixtures_payload = payload["synthetic_retrieval_hits"]
    if not isinstance(fixtures_payload, list):
        raise ValueError(f"Generation case line {line_number} has invalid synthetic hits")
    fixtures: list[SyntheticRetrievalHit] = []
    for fixture in fixtures_payload:
        if not isinstance(fixture, dict) or set(fixture) != _FIXTURE_FIELDS:
            raise ValueError(f"Generation case line {line_number} has invalid synthetic hit")
        fixtures.append(SyntheticRetrievalHit(**fixture))
    case = GenerationCase(
        case_id=_required_text(payload, "case_id"),
        category=_required_text(payload, "category"),
        query=_required_text(payload, "query"),
        context_chunk_ids=_text_tuple(payload, "context_chunk_ids"),
        synthetic_retrieval_hits=tuple(fixtures),
        expected_abstained=expected_abstained,
        reference_facts=_text_tuple(payload, "reference_facts"),
        required_citation_ids=_text_tuple(payload, "required_citation_ids"),
        forbidden_phrases=_text_tuple(payload, "forbidden_phrases"),
    )
    available = set(case.context_chunk_ids) | {
        fixture.chunk_id for fixture in case.synthetic_retrieval_hits
    }
    unknown_required = set(case.required_citation_ids) - available
    if unknown_required:
        raise ValueError(
            f"Generation case {case.case_id} requires unavailable citations: "
            f"{sorted(unknown_required)}"
        )
    return case


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Generation case field {field} must be non-empty text")
    return value


def _text_tuple(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload[field]
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(f"Generation case field {field} must be a text list")
    return tuple(value)


def _terms(text: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN.findall(text)
        if len(token) > 2 and token.casefold() not in _STOPWORDS
    }


def _overlap(subject: set[str], reference: set[str]) -> float:
    if not subject:
        return 0.0
    return len(subject.intersection(reference)) / len(subject)


def _invalid_generation_metrics(case: GenerationCase) -> GenerationMetrics:
    return GenerationMetrics(
        groundedness=0.0,
        answer_relevance=0.0,
        completeness=0.0 if case.reference_facts else None,
        citation_validity=0.0,
        citation_coverage=0.0,
        abstention_correctness=0.0,
        unsupported_claim_rate=1.0,
        prompt_injection_resistance=0.0,
    )


def write_generation_reports(
    report: dict[str, Any],
    metrics_path: Path = GENERATION_METRICS_PATH,
    report_path: Path = GENERATION_REPORT_PATH,
) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    rendered = _render_generation_report(report)
    report_path.write_text(rendered, encoding="utf-8", newline="\n")


def _render_generation_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# v0.5 Generation Evaluation Report")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "Grounded generation quality evaluation over frozen retrieval contexts "
        "using Foundry Local Chat Completions. The primary metrics are groundedness and "
        "citation validity."
    )
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- **Provider**: {report.get('provider', 'unknown')}")
    lines.append(f"- **Model**: {report.get('model', 'unknown')}")
    lines.append(f"- **Prompt version**: {report.get('prompt_version', 'unknown')}")
    lines.append(f"- **Cases evaluated**: {report.get('cases_evaluated', 0)}")
    lines.append("")
    lines.append("## Aggregated Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | ---: |")
    for metric_name, value in report.get("aggregates", {}).items():
        lines.append(f"| {metric_name} | {value:.6f} |")
    lines.append("")
    lines.append("## Per-case Results")
    lines.append("")
    lines.append("| Case ID | Category | Accepted | Groundedness | Citations Valid |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for case_result in report.get("per_case", []):
        metrics = case_result.get("metrics", {})
        accepted = "yes" if case_result.get("accepted") else "no"
        lines.append(
            f"| {case_result.get('case_id', '?')} | "
            f"{case_result.get('category', '?')} | "
            f"{accepted} | "
            f"{metrics.get('groundedness', 0.0):.6f} | "
            f"{metrics.get('citation_validity', 0.0):.6f} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- All evaluation cases are synthetic. Metrics therefore describe "
        "behaviour on the controlled corpus and not on real banking traffic."
    )
    lines.append(
        "- Groundedness measures token overlap between the answer and the retrieved evidence."
    )
    lines.append(
        "- Citation validity measures the fraction of citations that refer "
        "to chunks present in the grounding context."
    )
    lines.append(
        "- Prompt injection resistance is measured by checking whether "
        "forbidden phrases appear in the generated answer."
    )
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- The corpus is small, hand-authored, and fully synthetic.")
    lines.append("- Generation is evaluated against frozen contexts, not live retrieval.")
    lines.append("- Metrics do not measure factual accuracy beyond citation presence.")
    return "\n".join(lines) + "\n"
