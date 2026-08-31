"""Focused E2E regressions for the critical AegisBank journeys."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.tools.banking_tools import (
    GetMyLoansTool,
    GetNextInstallmentTool,
    create_default_database,
)
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry


class _Response:
    def __init__(self, message: object):
        self.choices = [type("Choice", (), {"message": message})()]


class _Message:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


def _call(name: str, arguments: dict[str, str]) -> object:
    function = type("Function", (), {"name": name, "arguments": json.dumps(arguments)})()
    return type("ToolCall", (), {"id": "E2E-001", "function": function})()


def test_e2e_read_account_policy_routes_real_tool() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _Response(
        _Message(content="Estos son tus préstamos sintéticos.")
    )
    registry = ToolRegistry([GetMyLoansTool(create_default_database())])

    result = AgentOrchestrator(client=client, registry=registry).run(
        "¿Cuáles son mis préstamos activos?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert [record.tool_name for record in result.tool_calls] == ["get_my_loans"]
    assert result.tool_calls[0].result.data["customer_id"] == "CUST-0001"


def test_e2e_multistep_read_routes_next_installment() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _Response(_Message(tool_calls=[_call("get_next_installment", {"loan_id": "LOAN-0002"})])),
        _Response(_Message(content="La cuota fue consultada en Core Banking.")),
    ]
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetNextInstallmentTool(db)])

    result = AgentOrchestrator(client=client, registry=registry).run(
        "¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert [record.tool_name for record in result.tool_calls] == [
        "get_my_loans",
        "get_next_installment",
    ]
    assert result.tool_calls[-1].result.success is True


def test_e2e_rag_gap_abstains_before_generation() -> None:
    client = MagicMock()
    metrics = OperationalMetrics()
    registry = ToolRegistry([SearchKnowledgeTool()])

    result = AgentOrchestrator(client=client, registry=registry, metrics=metrics).run(
        "¿Cuál es el plazo máximo para un crédito vehicular?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert result.tool_calls[0].tool_name == "search_knowledge"
    assert "No encuentro información suficiente" in result.answer
    assert metrics.get_counter("knowledge_abstention_count") == 1
