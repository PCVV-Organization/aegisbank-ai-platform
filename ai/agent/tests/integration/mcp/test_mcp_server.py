"""Unit tests for AegisBank MCP Server."""

from __future__ import annotations

import json

import pytest
from mock_core_banking.persistence.database import Database

from aegisbank_agent.hitl import HITLApprovalManager
from aegisbank_agent.mcp.server import create_aegisbank_mcp_server

pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_mcp_server_tool_listing(in_memory_db: Database) -> None:
    hitl_mgr = HITLApprovalManager()
    server = create_aegisbank_mcp_server(in_memory_db, hitl_mgr)
    tools = await server.list_tools()

    tool_names = [t.name for t in tools]
    assert "search_knowledge" in tool_names
    assert "get_my_loans" in tool_names
    assert "get_loan_details" in tool_names
    assert "get_next_installment" in tool_names
    assert "create_service_request" in tool_names

    # Check annotations
    for t in tools:
        if t.name == "create_service_request":
            assert t.annotations is not None
            assert t.annotations.read_only_hint is False
        else:
            assert t.annotations is not None
            assert t.annotations.read_only_hint is True


@pytest.mark.anyio
async def test_mcp_server_read_tools_execution(in_memory_db: Database) -> None:
    server = create_aegisbank_mcp_server(in_memory_db)
    res_loans_str = await server.call_tool("get_my_loans", {"customer_id": "CUST-0001"})
    res_loans = json.loads(res_loans_str.content[0].text)
    assert res_loans["success"] is True
    assert res_loans["data"]["customer_id"] == "CUST-0001"
    assert res_loans["data"]["total_loans"] == 2

    res_doc_str = await server.call_tool("search_knowledge", {"query": "tasas de credito"})
    res_doc = json.loads(res_doc_str.content[0].text)
    assert res_doc["success"] is True
    assert len(res_doc["data"]["hits"]) > 0


@pytest.mark.anyio
async def test_mcp_server_write_without_approval_rejected(in_memory_db: Database) -> None:
    server = create_aegisbank_mcp_server(in_memory_db)
    res_str = await server.call_tool(
        "create_service_request",
        {"category": "CLAIM", "description": "Cobro duplicado", "customer_id": "CUST-0001"},
    )
    res = json.loads(res_str.content[0].text)
    assert res["success"] is False
    assert "approval_id" in res["error"]


@pytest.mark.anyio
async def test_mcp_server_write_with_approval_executed(in_memory_db: Database) -> None:
    hitl_mgr = HITLApprovalManager()
    server = create_aegisbank_mcp_server(in_memory_db, hitl_mgr)

    appr = hitl_mgr.create_request(
        "create_service_request",
        "CUST-0001",
        {"category": "CLAIM", "description": "Cobro duplicado en cuota 3"},
    )
    hitl_mgr.approve(appr.approval_id, "CUST-0001")

    res_str = await server.call_tool(
        "create_service_request",
        {
            "category": "CLAIM",
            "description": "Cobro duplicado en cuota 3",
            "customer_id": "CUST-0001",
            "approval_id": appr.approval_id,
        },
    )
    res = json.loads(res_str.content[0].text)
    assert res["success"] is True
    assert "service_request_id" in res["data"]
    assert res["data"]["customer_id"] == "CUST-0001"
