"""End-to-end orchestrator regressions for v0.13.0-R1.

These tests assert two properties that the manual session uncovered:

* Metamorphic / paraphrase robustness: any user message that expresses the
  ``GET_LOAN_DETAILS`` intent for a specific ``LOAN-XXXX`` must result in a
  *real* structured tool call to ``get_loan_details`` regardless of whether the
  user used the word ``préstamo`` or not.
* No pseudo-tool-call text is ever accepted when an account query is detected.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from mock_core_banking.persistence.database import Database

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.observability.audit import AuditLogger
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.tools.banking_tools import (
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
    create_default_database,
)
from aegisbank_agent.tools.registry import ToolRegistry


def _make_registry(database: Database) -> ToolRegistry:
    return ToolRegistry(
        [
            GetMyLoansTool(database),
            GetLoanDetailsTool(database),
            GetNextInstallmentTool(database),
        ]
    )


@pytest.mark.parametrize(
    "phrase",
    [
        "Dame detalle de mi prestamo LOAN-0001",
        "Muéstrame LOAN-0001",
        "informacion del credito loan-0001",
        "saldo de LOAN-0002",
        "Detalle de mi préstamo LOAN-0001",
    ],
)
def test_loan_details_paraphrases_execute_get_loan_details(
    in_memory_db: Database, phrase: str
) -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = _make_registry(in_memory_db)
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run(phrase, customer_id="CUST-0001")

    tool_names = [record.tool_name for record in result.tool_calls]
    assert "get_loan_details" in tool_names, (
        f"Expected structured get_loan_details execution for phrase {phrase!r}, got {tool_names}"
    )
    assert result.success is True
    assert "get_loan_details(" not in (result.answer or "")
    assert metrics.get_counter("banking_data_required_count") >= 1
    assert metrics.get_counter("banking_tool_invoked_count") >= 1


def test_loan_details_response_does_not_contain_pseudo_tool_call_text(
    in_memory_db: Database,
) -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = _make_registry(in_memory_db)
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run("Muéstrame LOAN-0001", customer_id="CUST-0001")

    assert "get_loan_details(" not in (result.answer or "")
    assert "get_loan_details()" not in (result.answer or "")


def test_greeting_does_not_enumerate_categories_or_tool_names() -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = _make_registry(create_default_database())
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="¡Hola! Soy Aegis, tu asistente bancario. ¿En qué puedo ayudarte hoy?",
                    tool_calls=None,
                )
            )
        ]
    )
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run("Hola, ¿hay alguien?", customer_id="CUST-0001")

    assert result.success is True
    answer = (result.answer or "").lower()
    banned_tokens = ("loan", "installment", "fee", "general", "get_", "search_")
    for internal_token in banned_tokens:
        msg = f"Greeting response leaked token {internal_token!r}: {result.answer}"
        assert internal_token not in answer, msg
    assert len(result.tool_calls) == 0


def test_capability_query_response_uses_user_facing_language_only() -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = _make_registry(create_default_database())
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=(
                        "Puedo ayudarte con tus préstamos, próximas cuotas y políticas oficiales."
                    ),
                    tool_calls=None,
                )
            )
        ]
    )
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run("¿Qué puedes hacer?", customer_id="CUST-0001")

    assert result.success is True
    assert "get_my_loans" not in (result.answer or "")
    assert "search_knowledge" not in (result.answer or "")


def test_ambiguous_complaint_question_requests_clarification() -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = _make_registry(create_default_database())
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run(
        "¿Qué requiero para que mi reclamo tenga efecto?", customer_id="CUST-0001"
    )

    assert result.success is True
    answer_lower = (result.answer or "").lower()
    assert any(token in answer_lower for token in ("aclar", "precis", "refier"))
    assert len(result.tool_calls) == 0
    assert mock_client.chat.completions.create.call_count == 0
    assert metrics.get_counter("knowledge_required_count") == 0


def test_unknown_loan_id_returns_clean_ownership_error(in_memory_db: Database) -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = _make_registry(in_memory_db)
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run("Muéstrame LOAN-9999", customer_id="CUST-0001")

    assert result.success is False
    answer_lower = (result.answer or "").lower()
    assert "no pertenece" in answer_lower or "no encontrado" in answer_lower
    assert metrics.get_counter("banking_tool_missed_count") >= 1
