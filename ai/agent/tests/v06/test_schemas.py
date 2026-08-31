"""Tests for strict schema validation on tool inputs and outputs."""

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


class TestGetMyLoansSchema:
    """get_my_loans() has no parameters and returns customer loans list."""

    def test_no_parameters_required(self):
        tool = GetMyLoansTool()
        schema = tool.parameters_schema
        assert schema.get("type") == "object"
        assert "properties" in schema
        assert len(schema["properties"]) == 0
        assert schema.get("additionalProperties") is False
        assert schema.get("required", []) == []

    def test_execute_with_empty_args(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({}, context)
        assert result.success is True
        assert result.data is not None
        assert "loans" in result.data
        assert "customer_id" in result.data

    def test_execute_ignores_extra_args(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"extra": "ignored"}, context)
        assert result.success is True


class TestGetLoanDetailsSchema:
    """get_loan_details(loan_id) requires LOAN-XXXX format."""

    def test_requires_loan_id(self):
        tool = GetLoanDetailsTool()
        schema = tool.parameters_schema
        assert "loan_id" in schema["properties"]
        assert "loan_id" in schema["required"]

    def test_loan_id_format_in_description(self):
        tool = GetLoanDetailsTool()
        desc = tool.description
        assert "LOAN" in desc or "préstamo" in desc.lower()

    def test_valid_loan_id_succeeds(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is True
        assert result.data is not None
        assert result.data.get("loan_id") == "LOAN-0001"

    def test_invalid_loan_id_format_rejected(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "INVALID"}, context)
        assert result.success is False
        assert result.error is not None

    def test_missing_loan_id_rejected(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({}, context)
        assert result.success is False

    def test_wrong_type_loan_id_rejected(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": 12345}, context)
        assert result.success is False


class TestGetNextInstallmentSchema:
    """get_next_installment(loan_id) requires LOAN-XXXX format."""

    def test_requires_loan_id(self):
        tool = GetNextInstallmentTool()
        schema = tool.parameters_schema
        assert "loan_id" in schema["properties"]
        assert "loan_id" in schema["required"]

    def test_valid_loan_id_succeeds(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-0001"}, context)
        assert result.success is True
        assert result.data is not None

    def test_invalid_loan_id_format_rejected(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-XYZ"}, context)
        assert result.success is False

    def test_nonexistent_loan_returns_error(self, seeded_db: Database):
        tool = GetNextInstallmentTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "LOAN-9999"}, context)
        assert result.success is False
        assert result.error is not None


class TestToolResultSchema:
    """ToolResult always has tool_name, success, and optionally data/error."""

    def test_result_has_required_fields(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({}, context)
        assert hasattr(result, "tool_name")
        assert hasattr(result, "success")
        assert isinstance(result.success, bool)

    def test_result_as_dict_contains_all_fields(self, seeded_db: Database):
        tool = GetMyLoansTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({}, context)
        d = result.as_dict()
        assert "tool_name" in d
        assert "success" in d
        assert (d["success"] and "data" in d) or (not d["success"] and "error" in d)

    def test_error_result_has_no_data(self, seeded_db: Database):
        tool = GetLoanDetailsTool(seeded_db)
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"loan_id": "INVALID"}, context)
        assert result.success is False
        assert result.error is not None
        assert result.data is None
