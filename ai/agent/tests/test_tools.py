"""Tests for read-only function tools and tool registry."""

from __future__ import annotations

from mock_core_banking.persistence.database import Database

from aegisbank_agent.tools.banking_tools import (
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
)
from aegisbank_agent.tools.base import AgentContext
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry


def test_registry_allowlist_structure(tool_registry: ToolRegistry) -> None:
    tools = tool_registry.export_openai_tools()
    assert len(tools) == 3
    tool_names = [t["function"]["name"] for t in tools]
    assert "get_my_loans" in tool_names
    assert "get_loan_details" in tool_names
    assert "get_next_installment" in tool_names


def test_registry_rejects_unknown_tools(
    tool_registry: ToolRegistry, context_cust1: AgentContext
) -> None:
    res = tool_registry.execute("create_service_request", {"description": "test"}, context_cust1)
    assert not res.success
    assert "no permitida o desconocida" in (res.error or "")


def test_registry_rejects_write_tools(
    tool_registry: ToolRegistry, context_cust1: AgentContext
) -> None:
    res = tool_registry.execute("transfer_money", {"amount": 100}, context_cust1)
    assert not res.success
    assert "no permitida" in (res.error or "")


def test_get_my_loans_success(in_memory_db: Database, context_cust1: AgentContext) -> None:
    tool = GetMyLoansTool(in_memory_db)
    res = tool.execute({}, context_cust1)
    assert res.success
    assert res.data["customer_id"] == "CUST-0001"
    assert res.data["total_loans"] == 2
    loan_ids = [loan["loan_id"] for loan in res.data["loans"]]
    assert "LOAN-0001" in loan_ids
    assert "LOAN-0002" in loan_ids


def test_get_my_loans_unknown_customer(in_memory_db: Database) -> None:
    tool = GetMyLoansTool(in_memory_db)
    res = tool.execute({}, AgentContext(session_customer_id="CUST-9999"))
    assert not res.success
    assert "no encontrado" in (res.error or "")


def test_get_loan_details_invalid_arguments(
    in_memory_db: Database, context_cust1: AgentContext
) -> None:
    tool = GetLoanDetailsTool(in_memory_db)
    res = tool.execute({"loan_id": "INVALID"}, context_cust1)
    assert not res.success
    assert "formato válido" in (res.error or "")


def test_get_loan_details_not_found(in_memory_db: Database, context_cust1: AgentContext) -> None:
    tool = GetLoanDetailsTool(in_memory_db)
    res = tool.execute({"loan_id": "LOAN-9999"}, context_cust1)
    assert not res.success
    assert "no encontrado" in (res.error or "")


def test_get_next_installment_success(in_memory_db: Database, context_cust1: AgentContext) -> None:
    tool = GetNextInstallmentTool(in_memory_db)
    res = tool.execute({"loan_id": "LOAN-0001"}, context_cust1)
    assert res.success
    assert res.data["has_next_installment"] is True
    assert res.data["installment_id"] == "INST-0002"
    assert res.data["status"] == "OVERDUE"


def test_search_knowledge_tool() -> None:
    tool = SearchKnowledgeTool()
    res = tool.execute({"query": "requisitos para crédito"}, AgentContext("CUST-0001"))
    assert res.success
    assert "hits" in res.data
    assert len(res.data["hits"]) > 0


def test_search_knowledge_invalid_arg() -> None:
    tool = SearchKnowledgeTool()
    res = tool.execute({"query": ""}, AgentContext("CUST-0001"))
    assert not res.success
    assert "obligatorio" in (res.error or "")
