"""Unit tests for ToolRegistry allowlisting, tool execution, and OpenAI format export."""

from __future__ import annotations

from typing import Any

import pytest

from aegisbank_agent.tools.base import AgentContext, FunctionTool, ToolResult
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


class DummyTool(FunctionTool):
    """Minimal FunctionTool implementation for testing."""

    def __init__(self, name: str, success: bool = True, error_msg: str | None = None):
        self._name = name
        self._success = success
        self._error_msg = error_msg

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Dummy tool {self._name}"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        if self._success:
            return ToolResult(tool_name=self._name, success=True, data={"result": "ok"})
        return ToolResult(tool_name=self._name, success=False, error=self._error_msg or "error")


class FailingTool(FunctionTool):
    """Tool that raises an unexpected exception during execution."""

    @property
    def name(self) -> str:
        return "failing"

    @property
    def description(self) -> str:
        return "A tool that raises an exception"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        raise RuntimeError("intentional failure")


def test_default_tools_are_registered() -> None:
    """Default registry exposes canonical read-only tools."""
    registry = ToolRegistry()
    assert set(registry.allowed_tool_names) == {
        "get_loan_details",
        "get_my_loans",
        "get_next_installment",
        "search_knowledge",
    }


def test_custom_tools_and_get_tool() -> None:
    """Registry accepts custom tools and allows retrieval by name."""
    tool_a = DummyTool("tool_a")
    registry = ToolRegistry(tools=[tool_a])

    assert registry.get_tool("tool_a") is tool_a
    assert registry.get_tool("nonexistent") is None
    assert "tool_a" in registry.allowed_tool_names


@pytest.mark.parametrize(
    "tool_name",
    ["create_service_request", "transfer_money", "delete_account", "unknown_tool"],
)
def test_unknown_and_unauthorized_tools_rejected(tool_name: str) -> None:
    """Registry strictly rejects unauthorized or unknown tools at execution boundary."""
    registry = ToolRegistry(tools=[DummyTool("tool_a")])
    context = AgentContext(session_customer_id="CUST-0001")

    res = registry.execute(tool_name, {}, context)
    assert res.success is False
    assert "no permitida" in (res.error or "").lower() or "desconocida" in (res.error or "").lower()


def test_tool_execution_returns_tool_result() -> None:
    """Execution returns structured ToolResult and propagates success/error payloads."""
    tool_ok = DummyTool("tool_ok", success=True)
    tool_err = DummyTool("tool_err", success=False, error_msg="custom failure")
    registry = ToolRegistry(tools=[tool_ok, tool_err])
    context = AgentContext(session_customer_id="CUST-0001")

    ok_res = registry.execute("tool_ok", {}, context)
    assert ok_res.success is True
    assert ok_res.data == {"result": "ok"}

    err_res = registry.execute("tool_err", {}, context)
    assert err_res.success is False
    assert err_res.error == "custom failure"


def test_tool_execution_catches_unhandled_exception() -> None:
    """Exceptions raised inside tools are caught and converted to failed ToolResult."""
    registry = ToolRegistry(tools=[FailingTool()])
    context = AgentContext(session_customer_id="CUST-0001")

    res = registry.execute("failing", {}, context)
    assert res.success is False
    assert "Error inesperado" in (res.error or "") or "intentional failure" in (res.error or "")


def test_export_openai_tools_format() -> None:
    """Exported tool definitions match OpenAI Chat Completions tool calling schema."""
    registry = ToolRegistry()
    exported = registry.export_openai_tools()

    assert isinstance(exported, list)
    assert len(exported) == 4
    for tool_def in exported:
        assert tool_def["type"] == "function"
        fn = tool_def["function"]
        assert "name" in fn
        assert "description" in fn
        assert "parameters" in fn
        assert fn["parameters"].get("type") == "object"
