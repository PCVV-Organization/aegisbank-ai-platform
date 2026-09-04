"""Acceptance tests for the v0.7 local MCP and HITL boundary."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from mcp import Client
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.models import ServiceRequest
from mock_core_banking.persistence.seed import seed_database
from sqlalchemy import func, select

from aegisbank_agent.hitl import HITLApprovalManager
from aegisbank_agent.mcp_boundary import (
    MCP_TOOL_NAMES,
    MCPApprovalGateway,
    call_stdio,
    create_mcp_server,
)
from aegisbank_agent.tools.base import AgentContext

pytestmark = pytest.mark.integration


@pytest.fixture
def database(tmp_path) -> Database:
    db = Database(f"sqlite:///{tmp_path / 'mcp.sqlite'}")
    db.create_schema()
    seed_database(db)
    return db


def run(coro):
    return asyncio.run(coro)


async def connected_tools(database: Database, customer_id: str = "CUST-0001"):
    server = create_mcp_server(database, AgentContext(customer_id))
    client = Client(server)
    await client.__aenter__()
    return server, client


def request_count(database: Database, customer_id: str = "CUST-0001") -> int:
    with database.session() as session:
        return session.scalar(
            select(func.count())
            .select_from(ServiceRequest)
            .where(ServiceRequest.customer_id == customer_id)
        )


def test_read_via_mcp_and_exact_tool_allowlist(database: Database) -> None:
    async def scenario() -> None:
        server, client = await connected_tools(database)
        try:
            listed = await client.list_tools()
            assert {tool.name for tool in listed.tools} == set(MCP_TOOL_NAMES)
            result = await client.call_tool("get_my_loans", {})
            assert result.structured_content["success"] is True
        finally:
            await client.__aexit__(None, None, None)

    run(scenario())


def test_reject_does_not_call_write(database: Database) -> None:
    async def scenario() -> None:
        manager = HITLApprovalManager()
        context = AgentContext("CUST-0001")
        gateway = MCPApprovalGateway(context, manager)
        request = gateway.propose({"category": "INSTALLMENT", "description": "Cuota duplicada"})
        manager.reject(request.approval_id, "CUST-0001")
        async with Client(create_mcp_server(database, context, manager)) as client:
            result = await client.call_tool(
                "create_service_request",
                {
                    "approval_id": request.approval_id,
                    "category": "INSTALLMENT",
                    "description": "Cuota duplicada",
                },
            )
        assert result.structured_content["success"] is False
        assert request_count(database) == 1

    run(scenario())


def test_approve_executes_exactly_one_write(database: Database) -> None:
    manager = HITLApprovalManager()
    context = AgentContext("CUST-0001")
    gateway = MCPApprovalGateway(context, manager)
    request = gateway.propose({"category": "INSTALLMENT", "description": "Cuota duplicada"})
    server = create_mcp_server(database, context, manager)
    result = gateway.approve_and_call(server, request)
    assert result.structured_content["success"] is True
    assert request_count(database) == 2
    assert manager.get_request(request.approval_id).status.value == "EXECUTED"


def test_tampered_arguments_are_blocked(database: Database) -> None:
    async def scenario() -> None:
        manager = HITLApprovalManager()
        context = AgentContext("CUST-0001")
        request = manager.create_request(
            "create_service_request",
            context.session_customer_id,
            {"category": "INSTALLMENT", "description": "Cuota duplicada"},
        )
        manager.approve(request.approval_id, context.session_customer_id)
        async with Client(create_mcp_server(database, context, manager)) as client:
            result = await client.call_tool(
                "create_service_request",
                {
                    "approval_id": request.approval_id,
                    "category": "INSTALLMENT",
                    "description": "Descripción alterada",
                },
            )
        assert result.structured_content["error"]["code"] == "ARGUMENT_TAMPERING"
        assert request_count(database) == 1

    run(scenario())


@pytest.mark.parametrize(
    "customer_id, approval_id",
    [("CUST-0002", "owned"), ("CUST-0001", "missing")],
)
def test_wrong_or_missing_approval_is_blocked(
    database: Database, customer_id: str, approval_id: str
) -> None:
    async def scenario() -> None:
        manager = HITLApprovalManager()
        owner = AgentContext("CUST-0001")
        request = manager.create_request(
            "create_service_request",
            owner.session_customer_id,
            {"category": "GENERAL", "description": "Reclamo sintético"},
        )
        manager.approve(request.approval_id, owner.session_customer_id)
        supplied_id = request.approval_id if approval_id == "owned" else "APPR-MISSING"
        async with Client(
            create_mcp_server(database, AgentContext(customer_id), manager)
        ) as client:
            result = await client.call_tool(
                "create_service_request",
                {
                    "approval_id": supplied_id,
                    "category": "GENERAL",
                    "description": "Reclamo sintético",
                },
            )
        assert result.structured_content["success"] is False
        assert request_count(database, "CUST-0001") == 1

    run(scenario())


def test_executed_approval_and_unknown_tool_are_blocked(database: Database) -> None:
    async def scenario() -> None:
        manager = HITLApprovalManager()
        context = AgentContext("CUST-0001")
        gateway = MCPApprovalGateway(context, manager)
        request = gateway.propose({"category": "GENERAL", "description": "Reclamo sintético"})
        server = create_mcp_server(database, context, manager)
        await gateway._call_in_process(server, manager.approve(request.approval_id, "CUST-0001"))
        second = await gateway._call_in_process(
            server,
            manager.get_request(request.approval_id),
        )
        assert second.structured_content["success"] is False
        async with Client(server) as client:
            unknown_res = await client.call_tool("delete_customer", {})
            assert (
                unknown_res.is_error is True
                or unknown_res.structured_content.get("success") is False
            )
        assert request_count(database) == 2

    run(scenario())


def test_customer_id_is_runtime_owned(database: Database) -> None:
    async def scenario() -> None:
        context = AgentContext("CUST-0001")
        manager = HITLApprovalManager()
        server = create_mcp_server(database, context, manager)
        async with Client(server) as client:
            tools = (await client.list_tools()).tools
            write = next(tool for tool in tools if tool.name == "create_service_request")
            assert "customer_id" not in write.input_schema["properties"]
            result = await client.call_tool(
                "create_service_request",
                {
                    "approval_id": "APPR-MISSING",
                    "category": "GENERAL",
                    "description": "Reclamo sintético",
                    "customer_id": "CUST-0002",
                },
            )
            assert result.structured_content["success"] is False

    run(scenario())


def test_stdio_transport_negotiates_and_serves_read(tmp_path) -> None:
    async def scenario() -> None:
        server_script = Path(__file__).parents[2] / "src" / "aegisbank_agent" / "mcp_server.py"
        result, protocol_version = await call_stdio(
            server_script,
            "get_my_loans",
            {},
            customer_id="CUST-0001",
            database_url=f"sqlite:///{tmp_path / 'stdio.sqlite'}",
            approval_file=tmp_path / "approvals.json",
        )
        assert protocol_version == "2026-07-28"
        assert result.structured_content["success"] is True

    run(scenario())
