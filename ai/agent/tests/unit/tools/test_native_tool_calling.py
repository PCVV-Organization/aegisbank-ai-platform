from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.tools.base import AgentContext, FunctionTool, ToolResult
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


class _ReadTool(FunctionTool):
    def __init__(self, tool_name: str) -> None:
        self._name = tool_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Synthetic read-only acceptance tool."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"customer_id": context.session_customer_id, "arguments": arguments},
        )


class _StructuredClient:
    def __init__(self, tool_name: str) -> None:
        self.calls: list[dict[str, Any]] = []
        self._tool_name = tool_name
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            tool_call = SimpleNamespace(
                id="call_acceptance_001",
                function=SimpleNamespace(name=self._tool_name, arguments="{}"),
            )
            message = SimpleNamespace(content=None, tool_calls=[tool_call])
            return SimpleNamespace(
                choices=[SimpleNamespace(message=message, finish_reason="tool_calls")]
            )
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Respuesta basada en la lectura", tool_calls=None
                    ),
                    finish_reason="stop",
                )
            ]
        )


def test_structured_get_my_loans_call_executes_and_round_trips() -> None:
    client = _StructuredClient("get_my_loans")
    orchestrator = AgentOrchestrator(
        client=client,
        registry=ToolRegistry([_ReadTool("get_my_loans")]),
    )

    result = orchestrator.run("¿Cuáles son mis préstamos?", customer_id="CUST-0001")

    assert result.success
    assert [call.tool_name for call in result.tool_calls] == ["get_my_loans"]
    assert len(client.calls) == 2
    assert client.calls[0]["tool_choice"] == "auto"
    assert client.calls[1]["messages"][-1]["role"] == "tool"
    assert client.calls[1]["messages"][-1]["tool_call_id"] == "call_acceptance_001"


def test_structured_next_installment_call_executes() -> None:
    client = _StructuredClient("get_next_installment")
    orchestrator = AgentOrchestrator(
        client=client,
        registry=ToolRegistry([_ReadTool("get_next_installment")]),
    )

    result = orchestrator.run("¿Cuándo vence mi cuota?", customer_id="CUST-0001")

    assert result.success
    assert result.tool_calls[0].tool_name == "get_next_installment"


def test_structured_search_knowledge_call_executes() -> None:
    client = _StructuredClient("search_knowledge")
    orchestrator = AgentOrchestrator(
        client=client,
        registry=ToolRegistry([_ReadTool("search_knowledge")]),
    )

    result = orchestrator.run("¿Qué requisitos tiene el crédito?", customer_id="CUST-0001")

    assert result.success
    assert result.tool_calls[0].tool_name == "search_knowledge"


def test_acceptance_tool_result_is_json_serializable() -> None:
    client = _StructuredClient("get_my_loans")
    orchestrator = AgentOrchestrator(
        client=client,
        registry=ToolRegistry([_ReadTool("get_my_loans")]),
    )

    result = orchestrator.run("Consulta mis préstamos", customer_id="CUST-0001")

    json.dumps(result.as_dict(), ensure_ascii=False)
