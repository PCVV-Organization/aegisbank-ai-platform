"""Unit tests for knowledge and banking intent routing helpers."""

from __future__ import annotations

import pytest

from aegisbank_agent.knowledge_routing import (
    account_tool_allowlist,
    classify_service_inquiry,
    detect_loan_details_request,
    extract_loan_id,
    is_capability_query,
    is_greeting,
    requires_account_data,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "text",
    [
        "Dame detalle de mi prestamo LOAN-0001",
        "Dame detalle de mi LOAN-0001",
        "Muéstrame LOAN-0001",
        "informacion del credito loan-0002",
        "saldo de LOAN-0042",
    ],
)
def test_extract_loan_id_returns_canonical_form(text: str) -> None:
    """Canonical regex extracts normalized LOAN-XXXX identifier from varied paraphrases."""
    loan_id = extract_loan_id(text)
    assert loan_id is not None
    assert loan_id == loan_id.upper()
    assert loan_id.startswith("LOAN-")


def test_extract_loan_id_returns_none_when_absent() -> None:
    """Extractor returns None when no loan ID pattern is present."""
    assert extract_loan_id("Dame mis prestamos") is None
    assert extract_loan_id("Hola, ¿cómo estás?") is None


def test_detect_loan_details_request_with_explicit_id() -> None:
    """Request with explicit loan ID routes directly to account request without listing."""
    decision = detect_loan_details_request("Muéstrame el detalle de LOAN-0001")
    assert decision["loan_id"] == "LOAN-0001"
    assert decision["needs_loan_list_first"] is False
    assert decision["is_account_request"] is True


def test_detect_loan_details_request_without_id_needs_list_first() -> None:
    """Ambiguous loan request without ID requires listing loans first."""
    decision = detect_loan_details_request("Dame detalle de mi préstamo")
    assert decision["loan_id"] is None
    assert decision["needs_loan_list_first"] is True
    assert decision["is_account_request"] is True


@pytest.mark.parametrize(
    "text",
    [
        "Dame detalle de mi prestamo LOAN-0001",
        "Dame detalle de mi LOAN-0001",
        "Muéstrame LOAN-0001",
        "Saldo de LOAN-0042",
        "Información de mi crédito LOAN-0001",
    ],
)
def test_requires_account_data_for_loan_id_variants(text: str) -> None:
    """Queries referencing loan IDs require account data regardless of keyword phrasing."""
    assert requires_account_data(text) is True


@pytest.mark.parametrize(
    "text",
    ["Hola", "buenos dias", "Buenas tardes", "que tal", "SALUDOS"],
)
def test_is_greeting_detects_short_social_messages(text: str) -> None:
    """Greetings are recognized accurately to prevent unnecessary tool forcing."""
    assert is_greeting(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "Dame mis prestamos",
        "Que requiero para registrar un reclamo",
        "Muéstrame LOAN-0001",
        "Que puedes hacer",
    ],
)
def test_is_greeting_does_not_match_domain_queries(text: str) -> None:
    """Domain queries with business intent are never misclassified as greetings."""
    assert is_greeting(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "Que puedes hacer",
        "que puedes",
        "Cuales son tus funciones",
        "en que me puedes ayudar",
        "como me puedes ayudar",
    ],
)
def test_is_capability_query_detects_capability_questions(text: str) -> None:
    """Capability questions are detected for user-facing business language responses."""
    assert is_capability_query(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "Que requiero para que mi reclamo tenga efecto",
        "que requiero para que mi reclamo proceda",
        "que se requiere para un reclamo",
        "requisitos para mi reclamo",
    ],
)
def test_classify_service_inquiry_detects_ambiguous_complaint_questions(text: str) -> None:
    """Ambiguous complaint queries are triaged to prompt conversational clarification."""
    assert classify_service_inquiry(text) == "CLARIFICATION"


def test_classify_service_inquiry_rejects_clear_queries() -> None:
    """Clear informational queries do not trigger false clarification prompts."""
    assert classify_service_inquiry("Dame mis prestamos") != "CLARIFICATION"
    assert classify_service_inquiry("Que requiero para un credito vehicular") != "CLARIFICATION"


@pytest.mark.parametrize(
    "text",
    [
        "que campos requiero para un reclamo",
        "que datos necesito para registrar un reclamo",
    ],
)
def test_classify_service_inquiry_classifies_schema_questions(text: str) -> None:
    """Technical/schema questions are accurately categorized as DOMAIN_SCHEMA."""
    assert classify_service_inquiry(text) == "DOMAIN_SCHEMA"


def test_account_tool_allowlist_with_loan_id_selects_only_details() -> None:
    """Explicit loan ID query exposes only get_loan_details to prevent tool sprawl."""
    tools = account_tool_allowlist("Muéstrame LOAN-0001")
    assert "get_loan_details" in tools
    assert "get_my_loans" not in tools


def test_account_tool_allowlist_with_loan_id_and_installment_question() -> None:
    """Installment-specific query exposes get_next_installment."""
    tools = account_tool_allowlist("Muéstrame LOAN-0001 y su próxima cuota")
    assert "get_next_installment" in tools
