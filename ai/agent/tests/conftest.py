"""Pytest configuration and fixtures for aegisbank_agent tests."""

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
from aegisbank_agent.tools.registry import ToolRegistry


@pytest.fixture
def in_memory_db() -> Database:
    db = Database("sqlite:///:memory:")
    db.create_schema()
    seed_database(db)
    return db


@pytest.fixture
def context_cust1() -> AgentContext:
    return AgentContext(session_customer_id="CUST-0001")


@pytest.fixture
def context_cust2() -> AgentContext:
    return AgentContext(session_customer_id="CUST-0002")


@pytest.fixture
def banking_tools(
    in_memory_db: Database,
) -> tuple[GetMyLoansTool, GetLoanDetailsTool, GetNextInstallmentTool]:
    return (
        GetMyLoansTool(in_memory_db),
        GetLoanDetailsTool(in_memory_db),
        GetNextInstallmentTool(in_memory_db),
    )


@pytest.fixture
def tool_registry(in_memory_db: Database) -> ToolRegistry:
    my_loans, loan_details, next_installment = (
        GetMyLoansTool(in_memory_db),
        GetLoanDetailsTool(in_memory_db),
        GetNextInstallmentTool(in_memory_db),
    )
    return ToolRegistry(
        tools=[
            my_loans,
            loan_details,
            next_installment,
        ]
    )
