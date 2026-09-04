"""Acceptance tests for Banking Read Tool Routing and Policy Enforcement in v0.9.2."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from mock_core_banking.persistence.database import Database

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.knowledge_routing import account_tool_allowlist, requires_account_data
from aegisbank_agent.observability.audit import AuditLogger
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.tools.banking_tools import (
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
)
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.integration


class DummyChoice:
    def __init__(self, message: object):
        self.message = message


class DummyResponse:
    def __init__(self, message: object):
        self.choices = [DummyChoice(message)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


class DummyToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = arguments


def test_requires_account_data_classification() -> None:
    assert requires_account_data("¿Cuáles son mis préstamos activos?") is True
    assert requires_account_data("¿Cuánto debo en mi próxima cuota?") is True
    assert requires_account_data("¿Cuál es el saldo de mi préstamo?") is True
    assert requires_account_data("Hola, buenas tardes") is False
    assert requires_account_data("¿Cuáles son los requisitos de un crédito?") is False


def test_account_tool_allowlist_minimal_exposure() -> None:
    allowlist_loans = account_tool_allowlist("¿Cuáles son mis préstamos?")
    assert "get_my_loans" in allowlist_loans

    allowlist_installment = account_tool_allowlist("¿Cuánto debo en mi próxima cuota?")
    assert "get_next_installment" in allowlist_installment


def test_case_a_my_loans_query_executes_get_my_loans(in_memory_db: Database) -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = ToolRegistry(
        [
            GetMyLoansTool(in_memory_db),
            GetLoanDetailsTool(in_memory_db),
            GetNextInstallmentTool(in_memory_db),
            SearchKnowledgeTool(),
        ]
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="Tienes 2 préstamos: LOAN-0001 y LOAN-0002.")
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run("¿Cuáles son mis préstamos activos?", customer_id="CUST-0001")

    assert result.success is True
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_my_loans"
    assert result.tool_calls[0].result.success is True
    assert metrics.get_counter("banking_data_required_count") == 1
    assert metrics.get_counter("banking_tool_invoked_count") == 1


def test_case_b_next_installment_executes_get_next_installment(in_memory_db: Database) -> None:
    metrics = OperationalMetrics()
    registry = ToolRegistry(
        [
            GetMyLoansTool(in_memory_db),
            GetLoanDetailsTool(in_memory_db),
            GetNextInstallmentTool(in_memory_db),
        ]
    )

    tc = DummyToolCall("tc_01", "get_next_installment", json.dumps({"loan_id": "LOAN-0001"}))
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="Tu próxima cuota vence el 2026-03-01.")),
    ]

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry, metrics=metrics)
    result = orchestrator.run(
        "¿Cuándo vence la próxima cuota de LOAN-0001?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    tool_names = [tc.tool_name for tc in result.tool_calls]
    assert "get_next_installment" in tool_names


def test_case_c_combined_query_executes_multi_step_chain(in_memory_db: Database) -> None:
    metrics = OperationalMetrics()
    registry = ToolRegistry(
        [
            GetMyLoansTool(in_memory_db),
            GetLoanDetailsTool(in_memory_db),
            GetNextInstallmentTool(in_memory_db),
        ]
    )

    tc = DummyToolCall("tc_02", "get_next_installment", json.dumps({"loan_id": "LOAN-0002"}))
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="Préstamo LOAN-0002 activo, cuota de 875 PEN.")),
    ]

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry, metrics=metrics)
    result = orchestrator.run(
        "¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    tool_names = [tc.tool_name for tc in result.tool_calls]
    assert "get_my_loans" in tool_names
    assert "get_next_installment" in tool_names


def test_case_d_loan_of_another_customer_denied(in_memory_db: Database) -> None:
    registry = ToolRegistry([GetLoanDetailsTool(in_memory_db)])

    tc = DummyToolCall("tc_03", "get_loan_details", json.dumps({"loan_id": "LOAN-0003"}))
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="No tienes acceso a ese préstamo.")),
    ]

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("Detalle del préstamo LOAN-0003", customer_id="CUST-0001")

    assert len(result.tool_calls) == 1
    # LOAN-0003 belongs to CUST-0002, so CUST-0001 must be denied
    assert result.tool_calls[0].result.success is False
    assert "no pertenece" in result.tool_calls[0].result.error


def test_case_e_and_f_rag_policy_and_knowledge_gap() -> None:
    registry = ToolRegistry([SearchKnowledgeTool()])
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)

    # Knowledge gap query
    result = orchestrator.run(
        "¿Cuáles son los plazos máximos para un crédito vehicular?",
        customer_id="CUST-0001",
    )
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "search_knowledge"
    assert "No encuentro información suficiente" in result.answer


def test_case_g_casual_query_no_tools_forced() -> None:
    metrics = OperationalMetrics()
    registry = ToolRegistry([SearchKnowledgeTool()])
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="¡Buenos días! ¿Cómo estás?")
    )

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry, metrics=metrics)
    result = orchestrator.run("Hola, buenos días", customer_id="CUST-0001")

    assert len(result.tool_calls) == 0
    assert metrics.get_counter("banking_data_required_count") == 0


def test_case_h_pseudo_tool_call_is_never_parsed() -> None:
    metrics = OperationalMetrics()
    registry = ToolRegistry([SearchKnowledgeTool()])
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="get_my_loans()")
    )

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry, metrics=metrics)
    result = orchestrator.run("Hola", customer_id="CUST-0001")

    assert len(result.tool_calls) == 0
    assert result.answer == "get_my_loans()"
