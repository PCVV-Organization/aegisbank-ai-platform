"""Unit tests for tool security boundaries: rejection of unapproved,
mutating, or malformed tools.
"""

from __future__ import annotations

import pytest

from aegisbank_agent.tools.base import AgentContext
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "invalid_name",
    [
        "create_loan",
        "transfer_money",
        "file_claim",
        "get_my_loan",  # Typo variant
        "GET_MY_LOANS",  # Case-sensitivity variant
        "drop_tables",
    ],
)
def test_unknown_and_malformed_tool_names_rejected(invalid_name: str) -> None:
    """Registry rejects unapproved, misspelled, or improper-cased tool names."""
    registry = ToolRegistry()
    context = AgentContext(session_customer_id="CUST-0001")
    result = registry.execute(invalid_name, {}, context)
    assert result.success is False
    assert invalid_name not in registry.allowed_tool_names


def test_no_write_tools_exposed_in_default_registry() -> None:
    """Default registry exposes zero mutating or state-changing tools."""
    registry = ToolRegistry()
    write_indicators = ["create", "update", "delete", "transfer", "file", "register", "submit"]
    for name in registry.allowed_tool_names:
        for indicator in write_indicators:
            assert indicator not in name.lower(), f"Tool '{name}' appears to be a write tool"


def test_read_tools_are_idempotent_and_non_mutating() -> None:
    """Invoking the same read tool multiple times produces identical idempotent results."""
    registry = ToolRegistry()
    context = AgentContext(session_customer_id="CUST-0001")
    res1 = registry.execute("get_my_loans", {}, context)
    res2 = registry.execute("get_my_loans", {}, context)
    assert res1.success is True
    assert res2.success is True
    assert res1.data == res2.data
