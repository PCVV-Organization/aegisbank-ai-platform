"""Acceptance tests for AegisBank v0.7 MCP + HITL milestone."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.models import ServiceRequest
from sqlalchemy import select

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.hitl import (
    ApprovalNotFoundError,
    ApprovalStateError,
    ApprovalStatus,
    ArgumentTamperingError,
    CustomerMismatchError,
    HITLApprovalManager,
)
from aegisbank_agent.mcp.server import create_aegisbank_mcp_server
from aegisbank_agent.tools.base import AgentContext
from aegisbank_agent.tools.registry import ToolRegistry


class DummyChoice:
    def __init__(self, message: object):
        self.message = message


class DummyResponse:
    def __init__(self, message: object):
        self.choices = [DummyChoice(message)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


class DummyToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = arguments


# 1. READ vía MCP funciona
@pytest.mark.anyio
async def test_read_via_mcp_works(in_memory_db: Database) -> None:
    server = create_aegisbank_mcp_server(in_memory_db)
    res_str = await server.call_tool("get_my_loans", {"customer_id": "CUST-0001"})
    data = json.loads(res_str.content[0].text)
    assert data["success"] is True
    assert data["data"]["customer_id"] == "CUST-0001"


# 2. WRITE propuesto + REJECT → 0 ServiceRequests nuevos
def test_write_proposed_and_rejected_creates_zero_records(in_memory_db: Database) -> None:
    with in_memory_db.session() as session:
        initial_count = len(
            session.scalars(
                select(ServiceRequest).where(ServiceRequest.customer_id == "CUST-0001")
            ).all()
        )

    mock_client = MagicMock()
    tc = DummyToolCall(
        "call_1",
        "create_service_request",
        json.dumps({"category": "CLAIM", "description": "Reclamo cuota duplicada"}),
    )
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="Su solicitud fue rechazada por usted.")),
    ]

    hitl_mgr = HITLApprovalManager()
    registry = ToolRegistry(include_write_tools=True)
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        hitl_manager=hitl_mgr,
        approval_callback=lambda req: False,  # REJECT
    )

    result = orchestrator.run("Registrar reclamo", customer_id="CUST-0001")
    assert result.success is True
    assert len(result.approval_requests) == 1
    assert result.approval_requests[0].status == ApprovalStatus.REJECTED

    with in_memory_db.session() as session:
        final_count = len(
            session.scalars(
                select(ServiceRequest).where(ServiceRequest.customer_id == "CUST-0001")
            ).all()
        )
    assert final_count == initial_count


# 3. WRITE propuesto + APPROVE → exactamente 1 ServiceRequest nuevo
def test_write_proposed_and_approved_creates_exactly_one_record(in_memory_db: Database) -> None:
    with in_memory_db.session() as session:
        initial_count = len(
            session.scalars(
                select(ServiceRequest).where(ServiceRequest.customer_id == "CUST-0001")
            ).all()
        )

    mock_client = MagicMock()
    tc = DummyToolCall(
        "call_1",
        "create_service_request",
        json.dumps({"category": "CLAIM", "description": "Reclamo cuota duplicada en LOAN-0001"}),
    )
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="Su reclamo fue registrado exitosamente.")),
    ]

    hitl_mgr = HITLApprovalManager()
    from aegisbank_agent.tools.banking_tools import (
        CreateServiceRequestTool,
        GetLoanDetailsTool,
        GetMyLoansTool,
        GetNextInstallmentTool,
    )
    from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool

    registry = ToolRegistry(
        [
            SearchKnowledgeTool(),
            GetMyLoansTool(in_memory_db),
            GetLoanDetailsTool(in_memory_db),
            GetNextInstallmentTool(in_memory_db),
            CreateServiceRequestTool(in_memory_db),
        ]
    )
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        hitl_manager=hitl_mgr,
        approval_callback=lambda req: True,  # APPROVE
    )

    result = orchestrator.run("Registrar reclamo", customer_id="CUST-0001")
    assert result.success is True
    assert len(result.approval_requests) == 1
    assert result.approval_requests[0].status == ApprovalStatus.EXECUTED

    with in_memory_db.session() as session:
        final_count = len(
            session.scalars(
                select(ServiceRequest).where(ServiceRequest.customer_id == "CUST-0001")
            ).all()
        )
    assert final_count == initial_count + 1


# 4. Argumentos alterados tras approval → bloqueado
def test_arguments_altered_post_approval_blocked() -> None:
    mgr = HITLApprovalManager()
    orig = {"category": "CLAIM", "description": "Detalle original"}
    req = mgr.create_request("create_service_request", "CUST-0001", orig)
    mgr.approve(req.approval_id, "CUST-0001")

    tampered = {"category": "CLAIM", "description": "Detalle modificado sin aprobacion"}
    with pytest.raises(ArgumentTamperingError):
        mgr.verify_and_mark_executed(
            approval_id=req.approval_id,
            customer_id="CUST-0001",
            arguments_to_execute=tampered,
            execution_result={},
        )


# 5. Approval de otro cliente → bloqueado
def test_approval_for_different_customer_blocked() -> None:
    mgr = HITLApprovalManager()
    req = mgr.create_request("create_service_request", "CUST-0001", {"category": "CLAIM"})
    with pytest.raises(CustomerMismatchError):
        mgr.approve(req.approval_id, reviewer_customer_id="CUST-0002")


# 6. Approval inexistente → bloqueado
def test_nonexistent_approval_blocked() -> None:
    mgr = HITLApprovalManager()
    with pytest.raises(ApprovalNotFoundError):
        mgr.get_request("APPR-DOES-NOT-EXIST")


# 7. Approval ya ejecutado → bloqueado
def test_already_executed_approval_blocked() -> None:
    mgr = HITLApprovalManager()
    args = {"category": "CLAIM", "description": "Test"}
    req = mgr.create_request("create_service_request", "CUST-0001", args)
    mgr.approve(req.approval_id, "CUST-0001")
    mgr.verify_and_mark_executed(req.approval_id, "CUST-0001", args, {"sr_id": "SR-1"})

    with pytest.raises(ApprovalStateError, match="ya fue ejecutada"):
        mgr.verify_and_mark_executed(req.approval_id, "CUST-0001", args, {"sr_id": "SR-2"})


# 8. Tool desconocido → bloqueado
def test_unknown_tool_blocked() -> None:
    registry = ToolRegistry()
    res = registry.execute(
        "transfer_funds", {"amount": 1000}, AgentContext(session_customer_id="CUST-0001")
    )
    assert res.success is False
    assert "no permitida o desconocida" in (res.error or "")


# 9. customer_id no es controlable por el LLM
def test_customer_id_not_controllable_by_llm(in_memory_db: Database) -> None:
    from aegisbank_agent.tools.banking_tools import CreateServiceRequestTool

    tool = CreateServiceRequestTool(in_memory_db)
    # Attempting to supply customer_id in arguments has no effect; session context is used
    res = tool.execute(
        {
            "category": "CLAIM",
            "description": "Reclamo para otro cliente",
            "customer_id": "CUST-9999",
        },
        AgentContext(session_customer_id="CUST-0001"),
    )
    assert res.success is True
    assert res.data["customer_id"] == "CUST-0001"


# 10. Ninguna otra operación WRITE está expuesta
def test_no_other_write_operations_exposed() -> None:
    registry = ToolRegistry(include_write_tools=True)
    allowed = registry.allowed_tool_names
    # Only create_service_request is a write tool
    write_tools = [
        name
        for name in allowed
        if name.startswith(("create", "update", "delete", "transfer", "pay"))
    ]
    assert write_tools == ["create_service_request"]
    assert "transfer_money" not in allowed
    assert "update_loan" not in allowed
    assert "disburse_credit" not in allowed
