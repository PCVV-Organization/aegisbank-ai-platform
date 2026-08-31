"""Tests for Core Banking integration using deterministic local mock."""

from __future__ import annotations

import pytest
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.seed import seed_database

from aegisbank_agent.tools.banking_tools import (
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
)
from aegisbank_agent.tools.base import AgentContext


@pytest.fixture
def seeded_db() -> Database:
    db = Database("sqlite:///:memory:")
    db.create_schema()
    seed_database(db)
    return db


class TestCoreBankingCustomerData:
    """Core Banking mock returns correct customer data."""

    def test_cust0001_has_two_loans(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({}, context)
        assert result.success is True
        assert result.data["total_loans"] == 2

    def test_cust0002_has_one_loan(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0002")
        result = tool.execute({}, context)
        assert result.success is True
        assert result.data["total_loans"] == 1

    def test_cust0003_has_closed_loan(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0003")
        result = tool.execute({}, context)
        assert result.success is True
        assert len(result.data["loans"]) == 1
        assert result.data["loans"][0]["status"] == "CLOSED"


class TestCoreBankingLoanDetails:
    """Core Banking loan details match seeded data."""

    def test_loan_0001_belongs_to_cust0001(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is True
        assert result.data["customer_id"] == "CUST-0001"

    def test_loan_0001_is_delinquent(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is True
        assert result.data["status"] == "DELINQUENT"

    def test_loan_0002_is_active(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0002"}, context)
        assert result.success is True
        assert result.data["status"] == "ACTIVE"

    def test_loan_0003_belongs_to_cust0002(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0002")
        result = tool.execute({"loan_id": "LOAN-0003"}, context)
        assert result.success is True
        assert result.data["customer_id"] == "CUST-0002"


class TestCoreBankingInstallmentSchedule:
    """Core Banking installment schedule is correctly computed."""

    def test_loan_0001_has_next_installment(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is True
        assert result.data["has_next_installment"] is True
        assert "installment_id" in result.data

    def test_loan_0004_is_closed_no_installments(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0003")
        result = tool.execute({"loan_id": "LOAN-0004"}, context)
        assert result.success is True
        assert result.data["has_next_installment"] is False


class TestCoreBankingDeterminism:
    """Core Banking mock returns identical results on repeated calls."""

    def test_get_my_loans_deterministic(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        results = [tool.execute({}, context) for _ in range(5)]
        data_sequence = [r.data for r in results]
        assert all(d == data_sequence[0] for d in data_sequence)

    def test_get_loan_details_deterministic(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        results = [tool.execute({"loan_id": "LOAN-0001"}, context) for _ in range(5)]
        data_sequence = [r.data for r in results]
        assert all(d == data_sequence[0] for d in data_sequence)
