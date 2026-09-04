"""Contract tests for MCP tool definitions and schema invariants."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from aegisbank_agent.agent import WRITE_TOOLS
from aegisbank_agent.hitl import HITLApprovalManager
from aegisbank_agent.mcp_boundary import create_mcp_server
from aegisbank_agent.tools.banking_tools import (
    CreateServiceRequestTool,
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
    create_default_database,
)
from aegisbank_agent.tools.base import AgentContext
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.contract


def _load_schema(filename: str) -> dict:
    contracts_dir = Path(__file__).resolve().parents[4] / "contracts"
    schema_path = contracts_dir / filename
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_mcp_tools_match_json_schema_contract() -> None:
    db = create_default_database()
    tools = [
        GetMyLoansTool(db),
        GetLoanDetailsTool(db),
        GetNextInstallmentTool(db),
        CreateServiceRequestTool(db),
        SearchKnowledgeTool(),
    ]
    registry = ToolRegistry(tools)
    openai_tools = registry.export_openai_tools()

    # Convert to MCP-like list format for schema check
    tool_defs = [
        {
            "name": t["function"]["name"],
            "description": t["function"]["description"],
            "inputSchema": t["function"]["parameters"],
        }
        for t in openai_tools
    ]

    schema = _load_schema("mcp-tools.schema.json")
    jsonschema.validate(instance=tool_defs, schema=schema)


def test_mcp_server_contract_exposes_server() -> None:
    db = create_default_database()
    mgr = HITLApprovalManager()
    server = create_mcp_server(db, AgentContext("CUST-0001"), mgr)
    assert server.name == "AegisBank Local MCP"


def test_write_tool_contract_invariant() -> None:
    # AegisBank strictly allows only create_service_request as WRITE
    assert WRITE_TOOLS == {"create_service_request"}


def test_contract_fails_if_unauthorized_write_tool_is_introduced() -> None:
    unauthorized_tools = {"create_loan", "transfer_money", "delete_account", "update_balance"}
    assert WRITE_TOOLS.isdisjoint(unauthorized_tools)
