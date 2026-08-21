from decimal import Decimal

import pytest
from pydantic import ValidationError

from mock_core_banking.domain.enums import ServiceRequestStatus
from mock_core_banking.schemas import InstallmentResponse, ServiceRequestCreate


def test_installment_response_accepts_consistent_decimal_contract() -> None:
    installment = InstallmentResponse.model_validate(
        {
            "installment_id": "INST-0001",
            "loan_id": "LOAN-0001",
            "installment_number": 1,
            "due_date": "2026-02-01",
            "principal_due": "100.00",
            "interest_due": "10.00",
            "fees_due": "1.00",
            "total_due": "111.00",
            "status": "PENDING",
        }
    )
    assert installment.total_due == Decimal("111.00")


def test_service_request_strips_description() -> None:
    request = ServiceRequestCreate.model_validate(
        {
            "customer_id": "CUST-0001",
            "category": "GENERAL",
            "description": "  Synthetic request  ",
        }
    )
    assert request.description == "Synthetic request"


@pytest.mark.parametrize(
    "payload",
    [
        {"customer_id": "REAL-1", "category": "GENERAL", "description": "Request"},
        {"customer_id": "CUST-0001", "category": "OTHER", "description": "Request"},
        {"customer_id": "CUST-0001", "category": "GENERAL", "description": "   "},
        {
            "customer_id": "CUST-0001",
            "category": "GENERAL",
            "description": "Request",
            "unexpected": "field",
        },
    ],
)
def test_service_request_rejects_invalid_contract(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        ServiceRequestCreate.model_validate(payload)


def test_service_request_statuses_are_exact() -> None:
    assert {status.value for status in ServiceRequestStatus} == {
        "OPEN",
        "IN_REVIEW",
        "RESOLVED",
        "REJECTED",
    }
