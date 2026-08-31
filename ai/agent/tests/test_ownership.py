"""Tests verifying deterministic customer ownership enforcement."""

from __future__ import annotations

from mock_core_banking.persistence.database import Database

from aegisbank_agent.tools.banking_tools import GetLoanDetailsTool, GetNextInstallmentTool
from aegisbank_agent.tools.base import AgentContext


def test_loan_details_ownership_success(
    in_memory_db: Database, context_cust1: AgentContext
) -> None:
    tool = GetLoanDetailsTool(in_memory_db)
    # LOAN-0001 belongs to CUST-0001
    res = tool.execute({"loan_id": "LOAN-0001"}, context_cust1)
    assert res.success
    assert res.data["loan_id"] == "LOAN-0001"
    assert res.data["customer_id"] == "CUST-0001"


def test_loan_details_ownership_denied(in_memory_db: Database, context_cust1: AgentContext) -> None:
    tool = GetLoanDetailsTool(in_memory_db)
    # LOAN-0003 belongs to CUST-0002; CUST-0001 must be denied
    res = tool.execute({"loan_id": "LOAN-0003"}, context_cust1)
    assert not res.success
    assert "Acceso denegado" in (res.error or "")
    assert "no pertenece al cliente autenticado" in (res.error or "")


def test_next_installment_ownership_success(
    in_memory_db: Database, context_cust2: AgentContext
) -> None:
    tool = GetNextInstallmentTool(in_memory_db)
    # LOAN-0003 belongs to CUST-0002
    res = tool.execute({"loan_id": "LOAN-0003"}, context_cust2)
    assert res.success
    assert res.data["loan_id"] == "LOAN-0003"
    assert res.data["has_next_installment"] is True


def test_next_installment_ownership_denied(
    in_memory_db: Database, context_cust1: AgentContext
) -> None:
    tool = GetNextInstallmentTool(in_memory_db)
    # LOAN-0003 belongs to CUST-0002; CUST-0001 must be denied
    res = tool.execute({"loan_id": "LOAN-0003"}, context_cust1)
    assert not res.success
    assert "Acceso denegado" in (res.error or "")
