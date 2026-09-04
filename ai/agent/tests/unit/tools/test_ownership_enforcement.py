"""Unit tests for deterministic banking data ownership enforcement."""

from __future__ import annotations

import pytest
from mock_core_banking.persistence.database import Database

from aegisbank_agent.tools.banking_tools import GetLoanDetailsTool, GetNextInstallmentTool
from aegisbank_agent.tools.base import AgentContext

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("customer_id", "loan_id"),
    [
        ("CUST-0001", "LOAN-0001"),
        ("CUST-0001", "LOAN-0002"),
        ("CUST-0002", "LOAN-0003"),
    ],
)
def test_loan_details_ownership_success(
    in_memory_db: Database, customer_id: str, loan_id: str
) -> None:
    """Customers are authorized to inspect loans they own."""
    tool = GetLoanDetailsTool(in_memory_db)
    context = AgentContext(session_customer_id=customer_id)
    res = tool.execute({"loan_id": loan_id}, context)

    assert res.success is True
    assert res.data is not None
    assert res.data["loan_id"] == loan_id
    assert res.data["customer_id"] == customer_id


@pytest.mark.parametrize(
    ("customer_id", "unowned_loan_id"),
    [
        ("CUST-0001", "LOAN-0003"),  # Belongs to CUST-0002
        ("CUST-0002", "LOAN-0001"),  # Belongs to CUST-0001
        ("CUST-9999", "LOAN-0001"),  # Nonexistent customer
    ],
)
def test_loan_details_ownership_denied(
    in_memory_db: Database, customer_id: str, unowned_loan_id: str
) -> None:
    """Attempts to inspect loans owned by other customers are strictly denied."""
    tool = GetLoanDetailsTool(in_memory_db)
    context = AgentContext(session_customer_id=customer_id)
    res = tool.execute({"loan_id": unowned_loan_id}, context)

    assert res.success is False
    assert (
        "no pertenece" in (res.error or "").lower()
        or "acceso denegado" in (res.error or "").lower()
    )


@pytest.mark.parametrize(
    ("customer_id", "loan_id", "should_succeed"),
    [
        ("CUST-0001", "LOAN-0001", True),
        ("CUST-0002", "LOAN-0003", True),
        ("CUST-0001", "LOAN-0003", False),  # Cross-access
        ("CUST-0002", "LOAN-0004", False),  # Cross-access
    ],
)
def test_next_installment_ownership_enforcement(
    in_memory_db: Database, customer_id: str, loan_id: str, should_succeed: bool
) -> None:
    """Installment schedule inspection adheres strictly to customer ownership boundaries."""
    tool = GetNextInstallmentTool(in_memory_db)
    context = AgentContext(session_customer_id=customer_id)
    res = tool.execute({"loan_id": loan_id}, context)

    assert res.success is should_succeed
    if should_succeed:
        assert res.data is not None
        assert res.data["loan_id"] == loan_id
    else:
        assert (
            "no pertenece" in (res.error or "").lower()
            or "acceso denegado" in (res.error or "").lower()
        )


def test_ownership_check_determinism(in_memory_db: Database) -> None:
    """Ownership checks are 100% deterministic and replayable across repeated invocations."""
    tool = GetLoanDetailsTool(in_memory_db)
    context = AgentContext(session_customer_id="CUST-0001")

    # Repeat valid call 3 times
    valid_results = [tool.execute({"loan_id": "LOAN-0001"}, context) for _ in range(3)]
    assert all(r.success is True for r in valid_results)
    assert all(r.data == valid_results[0].data for r in valid_results)

    # Repeat cross-access attempt 3 times
    denied_results = [tool.execute({"loan_id": "LOAN-0003"}, context) for _ in range(3)]
    assert all(r.success is False for r in denied_results)
    assert all(r.error == denied_results[0].error for r in denied_results)
