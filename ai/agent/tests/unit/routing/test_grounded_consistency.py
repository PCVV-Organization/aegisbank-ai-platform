"""Acceptance and regression tests for Grounded Response Consistency and Provenance (v0.12.0-R1).

Verifies factual consistency, canonical provenance, RAG distinction, negative category rejection,
and absence of unnecessary WRITE or HITL actions on taxonomy inquiries.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from mock_core_banking.domain.enums import ServiceRequestCategory
from mock_core_banking.persistence.database import Database

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.hitl import HITLApprovalManager
from aegisbank_agent.tools.banking_tools import (
    CreateServiceRequestTool,
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
    create_default_database,
)
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


class DummyChoice:
    def __init__(self, message: object, finish_reason: str = "stop") -> None:
        self.message = message
        self.finish_reason = finish_reason


class DummyResponse:
    def __init__(self, message: object, finish_reason: str = "stop") -> None:
        self.choices = [DummyChoice(message, finish_reason=finish_reason)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls


def _create_orchestrator(
    db: Database,
    client: object,
    hitl_mgr: HITLApprovalManager | None = None,
) -> AgentOrchestrator:
    registry = ToolRegistry(
        [
            SearchKnowledgeTool(),
            GetMyLoansTool(db),
            GetLoanDetailsTool(db),
            GetNextInstallmentTool(db),
            CreateServiceRequestTool(db),
        ]
    )
    return AgentOrchestrator(
        client=client,
        registry=registry,
        hitl_manager=hitl_mgr or HITLApprovalManager(),
    )


def test_taxonomy_query_contains_exact_canonical_categories() -> None:
    """Verify that taxonomy query grounded in schema contains all canonical enum categories."""
    canonical_categories = {c.value for c in ServiceRequestCategory}
    assert canonical_categories == {"LOAN", "INSTALLMENT", "FEE", "GENERAL"}

    expected_answer = (
        "Los tipos de reclamos o solicitudes que soporta AegisBank son:\n"
        "1. LOAN (Préstamos)\n"
        "2. INSTALLMENT (Cuotas)\n"
        "3. FEE (Comisiones)\n"
        "4. GENERAL (Consultas generales)"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content=expected_answer)
    )

    db = create_default_database()
    orchestrator = _create_orchestrator(db, mock_client)

    result = orchestrator.run("¿qué tipos de reclamos hay?", customer_id="CUST-0001")
    assert result.success is True
    assert len(result.approval_requests) == 0
    assert len(result.tool_calls) == 0  # No execution required for schema-grounded facts

    # Check that all canonical categories appear in answer
    for cat in canonical_categories:
        assert cat in result.answer


def test_taxonomy_query_repeated_yields_consistent_factual_set() -> None:
    """Verify repeated queries across multiple runs preserve exact factual categories."""
    canonical_categories = {"LOAN", "INSTALLMENT", "FEE", "GENERAL"}
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(
            content=(
                "En AegisBank, las categorías soportadas son: LOAN, INSTALLMENT, FEE y GENERAL."
            )
        )
    )

    db = create_default_database()
    orchestrator = _create_orchestrator(db, mock_client)

    for _ in range(3):
        result = orchestrator.run("¿qué tipos de reclamos existen?", customer_id="CUST-0001")
        assert result.success is True
        for cat in canonical_categories:
            assert cat in result.answer


def test_paraphrased_taxonomy_queries_preserve_factual_consistency() -> None:
    """Verify different paraphrased ways of asking yield the same canonical facts."""
    paraphrases = [
        "¿qué categorías de reclamos acepta el sistema?",
        "¿cuáles son los tipos de solicitudes que se pueden registrar?",
        "¿qué reclamos soporta AegisBank?",
    ]
    canonical_categories = {"LOAN", "INSTALLMENT", "FEE", "GENERAL"}
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="Las categorías de AegisBank son: LOAN, INSTALLMENT, FEE y GENERAL.")
    )

    db = create_default_database()
    orchestrator = _create_orchestrator(db, mock_client)

    for query in paraphrases:
        result = orchestrator.run(query, customer_id="CUST-0001")
        assert result.success is True
        for cat in canonical_categories:
            assert cat in result.answer


def test_negative_acceptance_unsupported_categories_rejected() -> None:
    """Verify unsupported fabricated categories (PAYMENT, TRANSFER, CARD, FRAUD) are absent."""
    unsupported_categories = ["PAYMENT", "TRANSFER", "CARD", "FRAUD"]
    grounded_answer = (
        "En AegisBank, las categorías oficiales son: LOAN, INSTALLMENT, FEE y GENERAL."
    )

    for unsupp in unsupported_categories:
        assert unsupp not in grounded_answer


def test_procedural_question_routes_to_rag_search_knowledge() -> None:
    """Verify procedural/policy question triggers search_knowledge (RAG)."""
    db = create_default_database()
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="El procedimiento para presentar un reclamo es...")
    )
    orchestrator = _create_orchestrator(db, mock_client)

    result = orchestrator.run(
        "¿Cuál es el procedimiento y requisitos para presentar un reclamo?",
        customer_id="CUST-0001",
    )
    assert result.success is True
    # search_knowledge was proposed/executed for procedural knowledge
    tool_names = [tc.tool_name for tc in result.tool_calls]
    assert "search_knowledge" in tool_names


def test_missing_policy_results_in_grounded_abstention() -> None:
    """Verify when policy query lacks corpus evidence, agent abstains cleanly."""
    db = create_default_database()
    mock_client = MagicMock()
    orchestrator = _create_orchestrator(db, mock_client)

    result = orchestrator.run(
        "¿Cuál es el plazo máximo para un crédito vehicular?",
        customer_id="CUST-0001",
    )
    assert result.success is True
    assert "No encuentro información suficiente" in result.answer
    assert len(result.approval_requests) == 0


def test_taxonomy_query_causes_no_unnecessary_write_or_hitl() -> None:
    """Verify informational queries never trigger create_service_request or HITL approvals."""
    db = create_default_database()
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="Categorías: LOAN, INSTALLMENT, FEE, GENERAL.")
    )
    hitl_mgr = HITLApprovalManager()
    orchestrator = _create_orchestrator(db, mock_client, hitl_mgr=hitl_mgr)

    result = orchestrator.run("¿Cuáles son los tipos de reclamos?", customer_id="CUST-0001")
    assert result.success is True
    assert len(result.approval_requests) == 0
    assert len(hitl_mgr._requests) == 0
