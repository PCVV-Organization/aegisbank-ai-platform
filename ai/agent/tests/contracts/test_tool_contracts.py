"""Contract tests for the agent tool registry and write boundary."""

from __future__ import annotations

from aegisbank_agent.tools.registry import ToolRegistry


def test_default_tool_contracts_have_stable_names_and_schemas() -> None:
    registry = ToolRegistry()
    assert registry.allowed_tool_names == [
        "get_loan_details",
        "get_my_loans",
        "get_next_installment",
        "search_knowledge",
    ]
    for tool in registry.export_openai_tools():
        function = tool["function"]
        assert function["name"]
        assert function["parameters"]["type"] == "object"
        assert function["parameters"]["additionalProperties"] is False


def test_default_registry_does_not_expose_write_tools() -> None:
    assert "create_service_request" not in ToolRegistry().allowed_tool_names


def test_write_boundary_is_explicit() -> None:
    assert "create_service_request" in ToolRegistry(include_write_tools=True).allowed_tool_names
