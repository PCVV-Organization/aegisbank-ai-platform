"""Tests for unknown/invalid tool rejection and security boundaries."""

from __future__ import annotations

from aegisbank_agent.tools.base import AgentContext
from aegisbank_agent.tools.registry import ToolRegistry


class TestUnknownToolRejection:
    """Unknown tool names must be rejected at the registry level."""

    def test_unknown_tool_returns_error(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("create_loan", {}, context)
        assert result.success is False
        assert "no permitida" in (result.error or "")

    def test_unknown_tool_not_in_allowed_list(self):
        registry = ToolRegistry()
        assert "create_loan" not in registry.allowed_tool_names
        assert "transfer_money" not in registry.allowed_tool_names
        assert "file_claim" not in registry.allowed_tool_names

    def test_typo_tool_rejected(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("get_my_loan", {}, context)
        assert result.success is False

    def test_case_sensitive_tool_names(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("GET_MY_LOANS", {}, context)
        assert result.success is False


class TestWriteOperationsBlocked:
    """Write operations must be rejected - no write tools exist."""

    def test_no_write_tools_in_registry(self):
        registry = ToolRegistry()
        write_indicators = ["create", "update", "delete", "transfer", "file", "register", "submit"]
        for name in registry.allowed_tool_names:
            for indicator in write_indicators:
                assert indicator not in name.lower(), f"Tool {name} appears to be a write tool"

    def test_empty_arguments_for_read_tool(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result = registry.execute("get_my_loans", {}, context)
        assert result.success is True


class TestToolCallNotMutating:
    """Tools should not mutate state - verified by calling same tool twice."""

    def test_same_call_produces_same_result(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result1 = registry.execute("get_my_loans", {}, context)
        result2 = registry.execute("get_my_loans", {}, context)
        assert result1.success == result2.success
        assert result1.data == result2.data
