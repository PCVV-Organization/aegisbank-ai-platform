"""Contract checks for the stable synthetic Core Banking HTTP boundary."""

from __future__ import annotations

import json

from mock_core_banking.domain.enums import ServiceRequestCategory
from mock_core_banking.persistence.models import OutboxEvent
from mock_core_banking.persistence.repositories import ServiceRequestRepository

EXPECTED_PATHS = {
    "/health/live",
    "/health/ready",
    "/api/v1/customers/{customer_id}",
    "/api/v1/customers/{customer_id}/loans",
    "/api/v1/loans/{loan_id}",
    "/api/v1/loans/{loan_id}/installments/next",
    "/api/v1/service-requests",
    "/api/v1/service-requests/{service_request_id}",
}


def test_openapi_v1_path_and_field_contract(client) -> None:
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == EXPECTED_PATHS
    loan = schema["components"]["schemas"]["LoanResponse"]["properties"]
    assert {"loan_id", "status", "outstanding_balance"}.issubset(loan)
    installment = schema["components"]["schemas"]["InstallmentResponse"]["properties"]
    assert {"loan_id", "due_date", "total_due"}.issubset(installment)


def test_service_request_contract_has_only_the_authorized_write_route(client) -> None:
    schema = client.get("/openapi.json").json()
    writes = [
        (path, method)
        for path, operations in schema["paths"].items()
        for method in operations
        if method in {"post", "put", "patch", "delete"}
    ]
    assert writes == [("/api/v1/service-requests", "post")]


def test_service_request_created_event_contract(database) -> None:
    with database.session() as session:
        record = ServiceRequestRepository(session).create(
            customer_id="CUST-0001",
            category=ServiceRequestCategory.INSTALLMENT,
            description="Contrato sintético",
        )
        event = session.get(OutboxEvent, f"EVT-{record.service_request_id}")
        assert event is not None
        payload = json.loads(event.payload)

    assert payload["service_request_id"] == record.service_request_id
    assert {"customer_id", "category", "description", "status", "created_at"}.issubset(payload)
