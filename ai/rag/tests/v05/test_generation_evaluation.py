import json

import pytest

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.constants import GENERATION_DEV_CASES_PATH, GENERATION_EVAL_CASES_PATH
from aegisbank_rag.context import build_context
from aegisbank_rag.generation_evaluation import (
    evaluate_generation,
    load_generation_cases,
    resolve_case_hits,
)
from aegisbank_rag.prompting import load_prompt

from .support import RecordingProvider, answer_json


def _evaluation_responses() -> dict[str, str]:
    return {
        "¿De qué se compone una cuota simulada?": answer_json(
            "Una cuota está compuesta por una porción de capital, una porción de "
            "intereses y, cuando corresponde, cargos por mora simulada.",
            ["chk_cuotas_calculoycronograma__v1__c001_84c946b9e948"],
        ),
        "Resume los requisitos y las condiciones de los productos ficticios.": answer_json(
            "Los requisitos incluyen antigüedad mínima, monto mínimo, score sintético y "
            "documentación requerida. Las condiciones incluyen tasa referencial, plazo "
            "máximo, gastos administrativos simulados y comisiones aplicables.",
            [
                "chk_productos_requisitosycondiciones__v1__c001_72893fe01b1b",
                "chk_productos_requisitosycondiciones__v1__c002_055c48408f1c",
            ],
        ),
        "¿Cuál es la versión vigente y qué plazo admite el crédito personal simulado?": (
            answer_json(
                "La versión vigente es v2 y admite un plazo de amortización entre 6 y 60 "
                "meses. La versión v1 quedó sin efecto desde el 30 de junio de 2026.",
                [
                    "chk_creditos_producto_general__v2__c001_5818ccde2254",
                    "chk_creditos_producto_general__v2__c003_21f4fdf64b84",
                ],
            )
        ),
        "¿Cuál es el monto máximo exacto en soles del crédito personal simulado?": answer_json(
            "No hay evidencia suficiente en el contexto recuperado para responder la consulta.",
            [],
            abstained=True,
        ),
        "¿Qué debe hacer Aegis cuando no existe evidencia suficiente?": answer_json(
            "Aegis debe abstenerse y declarar explícitamente la abstención.",
            ["chk_politicas_absteneveryevidence__v1__c001_d3b3c5baac00"],
        ),
    }


def test_prompt_development_and_evaluation_datasets_are_disjoint() -> None:
    development = load_generation_cases(GENERATION_DEV_CASES_PATH)
    evaluation = load_generation_cases(GENERATION_EVAL_CASES_PATH)

    assert {case.case_id for case in development}.isdisjoint(case.case_id for case in evaluation)
    assert {case.query for case in development}.isdisjoint(case.query for case in evaluation)
    assert {case.category for case in evaluation} == {
        "direct_support",
        "multiple_chunks",
        "current_version",
        "insufficient_evidence",
        "out_of_domain",
        "suspicious_context",
    }


def test_version_case_removes_superseded_context(documents) -> None:
    cases = load_generation_cases()
    version_case = next(case for case in cases if case.category == "current_version")
    hits = resolve_case_hits(version_case, chunk_corpus(documents))

    context = build_context(hits)

    assert all(entry.status == "active" for entry in context.entries)
    assert all(entry.version == "v2" for entry in context.entries)
    assert "chk_creditos_producto_general__v1__c001_b401dfff16a5" not in context.chunk_ids


def test_generation_evaluation_is_reproducible(documents) -> None:
    cases = load_generation_cases()
    chunks = chunk_corpus(documents)
    prompt = load_prompt()

    first = evaluate_generation(
        RecordingProvider(responses_by_query=_evaluation_responses()),
        prompt,
        cases,
        chunks,
    )
    second = evaluate_generation(
        RecordingProvider(responses_by_query=_evaluation_responses()),
        prompt,
        cases,
        chunks,
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["evaluation_kind"] == "generation_quality_fixed_context"
    assert first["retrieval_quality_included"] is False
    assert first["cases_evaluated"] == 6
    assert all(case["accepted"] for case in first["per_case"])
    for value in first["aggregates"].values():
        assert 0.0 <= value <= 1.0


def test_evaluation_records_rejected_invented_citation(documents) -> None:
    case = load_generation_cases()[0]
    provider = RecordingProvider(response=answer_json("Respuesta inventada.", ["chk_inventado"]))

    report = evaluate_generation(provider, load_prompt(), [case], chunk_corpus(documents))

    result = report["per_case"][0]
    assert result["accepted"] is False
    assert "not present in retrieved context" in result["validation_error"]
    assert result["metrics"]["citation_validity"] == 0.0


def test_eval_dataset_rejects_unknown_chunk(documents, tmp_path) -> None:
    invalid = {
        "case_id": "invalid",
        "category": "direct_support",
        "query": "Consulta",
        "context_chunk_ids": ["chk_missing"],
        "synthetic_retrieval_hits": [],
        "expected_abstained": False,
        "reference_facts": ["hecho"],
        "required_citation_ids": [],
        "forbidden_phrases": [],
    }
    path = tmp_path / "invalid.jsonl"
    path.write_text(json.dumps(invalid), encoding="utf-8")
    case = load_generation_cases(path)[0]

    with pytest.raises(ValueError, match="Unknown context chunks"):
        resolve_case_hits(case, chunk_corpus(documents))
