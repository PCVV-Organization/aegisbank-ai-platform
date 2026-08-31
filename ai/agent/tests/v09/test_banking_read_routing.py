"""Acceptance tests for policy-enforced routing to authenticated READ tools."""

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
from aegisbank_agent.tools.registry import ToolRegistry


class _Response:
    def __init__(self, message: object):
        self.choices = [type("Choice", (), {"message": message})()]


class _Message:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


def _tool_call(name: str, arguments: dict[str, str]) -> object:
    function = type("Function", (), {"name": name, "arguments": json.dumps(arguments)})()
    return type("ToolCall", (), {"id": "CALL-001", "function": function})()


def test_account_list_is_resolved_before_generation() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _Response(
        _Message(content="Tienes dos préstamos propios.")
    )
    metrics = OperationalMetrics()
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetNextInstallmentTool(db)])

    result = AgentOrchestrator(client=client, registry=registry, metrics=metrics).run(
        "¿Cuáles son mis préstamos activos?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert [call.tool_name for call in result.tool_calls] == ["get_my_loans"]
    assert metrics.get_counter("banking_tool_invoked_count") == 1
    sent_tools = client.chat.completions.create.call_args.kwargs["tools"]
    assert sent_tools == []


def test_combined_account_query_routes_structured_follow_up() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _Response(
            _Message(tool_calls=[_tool_call("get_next_installment", {"loan_id": "LOAN-0002"})])
        ),
        _Response(_Message(content="La próxima cuota de LOAN-0002 vence según el calendario.")),
    ]
    metrics = OperationalMetrics()
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetNextInstallmentTool(db)])

    result = AgentOrchestrator(client=client, registry=registry, metrics=metrics).run(
        "¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert [call.tool_name for call in result.tool_calls] == [
        "get_my_loans",
        "get_next_installment",
    ]
    assert all(call.result.success for call in result.tool_calls)
    first_call = client.chat.completions.create.call_args_list[0].kwargs
    assert [item["function"]["name"] for item in first_call["tools"]] == ["get_next_installment"]
    assert first_call["tool_choice"] == {
        "type": "function",
        "function": {"name": "get_next_installment"},
    }
