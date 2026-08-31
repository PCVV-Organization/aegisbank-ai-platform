"""Tests for tool registry: allowlist, unknown tool rejection, execution."""

from __future__ import annotations

from aegisbank_agent.tools.base import AgentContext, FunctionTool, ToolResult
from aegisbank_agent.tools.registry import ToolRegistry


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
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    def execute(self, arguments: dict, context: AgentContext) -> ToolResult:
        if self._success:
            return ToolResult(tool_name=self._name, success=True, data={"result": "ok"})
        return ToolResult(tool_name=self._name, success=False, error=self._error_msg or "error")


class FailingTool(FunctionTool):
    """Tool that raises exception during execution."""

    @property
    def name(self) -> str:
        return "failing"

    @property
    def description(self) -> str:
        return "A tool that fails"

    @property
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    def execute(self, arguments: dict, context: AgentContext) -> ToolResult:
        raise RuntimeError("intentional failure")


class TestToolRegistryAllowlist:
    """Registry should only contain the 4 read-only tools."""

    def test_default_tools_are_registered(self):
        registry = ToolRegistry()
        assert set(registry.allowed_tool_names) == {
            "get_loan_details",
            "get_my_loans",
            "get_next_installment",
            "search_knowledge",
        }

    def test_custom_tools_can_be_registered(self):
        tool = DummyTool("dummy_tool")
        registry = ToolRegistry(tools=[tool])
        assert "dummy_tool" in registry.allowed_tool_names
        assert len(registry.allowed_tool_names) == 1

    def test_register_adds_tool(self):
        registry = ToolRegistry()
        tool = DummyTool("extra_tool")
        registry.register(tool)
        assert "extra_tool" in registry.allowed_tool_names

    def test_get_tool_returns_tool(self):
        registry = ToolRegistry()
        tool = registry.get_tool("get_my_loans")
        assert tool is not None
        assert tool.name == "get_my_loans"

    def test_get_tool_returns_none_for_unknown(self):
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent_tool") is None


class TestUnknownToolRejection:
    """Unknown tools must be rejected with appropriate error."""

    def test_execute_unknown_tool_returns_error(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("nonexistent_tool", {}, context)
        assert result.success is False
        error_msg = result.error or ""
        assert "no permitida" in error_msg or "desconocida" in error_msg

    def test_execute_unknown_tool_lists_allowed(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("nonexistent_tool", {}, context)
        error_msg = result.error or ""
        for allowed in registry.allowed_tool_names:
            assert allowed in error_msg


class TestToolExecution:
    """Tool execution returns proper ToolResult."""

    def test_execute_returns_tool_result(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("get_my_loans", {}, context)
        assert isinstance(result, ToolResult)
        assert result.tool_name == "get_my_loans"

    def test_execute_propagates_exception_as_failure(self):
        registry = ToolRegistry(tools=[FailingTool()])
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("failing", {}, context)
        assert result.success is False
        error_msg = result.error or ""
        assert "intentional failure" in error_msg


class TestExportOpenAITools:
    """Registry exports tools in OpenAI function-calling format."""

    def test_export_returns_list(self):
        registry = ToolRegistry()
        tools = registry.export_openai_tools()
        assert isinstance(tools, list)
        assert len(tools) == 4

    def test_export_contains_function_type(self):
        registry = ToolRegistry()
        tools = registry.export_openai_tools()
        for tool in tools:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "parameters" in tool["function"]

    def test_export_matches_tool_names(self):
        registry = ToolRegistry()
        tools = registry.export_openai_tools()
        exported_names = {t["function"]["name"] for t in tools}
        assert exported_names == set(registry.allowed_tool_names)
