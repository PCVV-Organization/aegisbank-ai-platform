"""Tests for customer ownership enforcement on loans and installments."""

from __future__ import annotations

import pytest
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.seed import seed_database

from aegisbank_agent.tools.banking_tools import (
    GetLoanDetailsTool,
    GetNextInstallmentTool,
)
from aegisbank_agent.tools.base import AgentContext


@pytest.fixture
def seeded_db() -> Database:
    db = Database("sqlite:///:memory:")
    db.create_schema()
    seed_database(db)
    return db


class TestLoanOwnershipEnforcement:
    """Loan details only accessible to owning customer."""

    def test_owner_can_access_own_loan(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is True
        assert result.data is not None
        assert result.data.get("loan_id") == "LOAN-0001"

    def test_cust1_cannot_access_cust2_loan(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0003"}, context)
        assert result.success is False
        assert result.error is not None
        error_lower = (result.error or "").lower()
        assert "no pertenece" in error_lower or "acceso denegado" in error_lower

    def test_cust2_cannot_access_cust1_loan(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0002")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is False
        assert result.error is not None

    def test_nonexistent_customer_cannot_access_any_loan(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-9999")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is False


class TestInstallmentOwnershipEnforcement:
    """Next installment only accessible for loans owned by session customer."""

    def test_owner_can_access_own_installment(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is True
        assert result.data is not None

    def test_cust1_cannot_access_cust2_loan_installment(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0003"}, context)
        assert result.success is False
        assert result.error is not None

    def test_cust2_cannot_access_cust3_loan_installment(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0002")
        result = tool.execute({"loan_id": "LOAN-0004"}, context)
        assert result.success is False


class TestOwnershipCheckIsDeterministic:
    """Ownership checks must be deterministic across multiple calls."""

    def test_same_loan_same_customer_same_result(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        results = [tool.execute({"loan_id": "LOAN-0001"}, context) for _ in range(3)]
        assert all(r.success for r in results)
        assert all(r.data == results[0].data for r in results)

    def test_cross_access_always_fails_for_same_input(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        results = [tool.execute({"loan_id": "LOAN-0003"}, context) for _ in range(3)]
        assert all(not r.success for r in results)
        assert all(r.error == results[0].error for r in results)
