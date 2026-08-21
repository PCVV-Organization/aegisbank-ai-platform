from datetime import datetime, timezone

from sqlalchemy import select

from mock_core_banking.domain.enums import ServiceRequestCategory, ServiceRequestStatus
from mock_core_banking.persistence.models import ServiceRequest
from mock_core_banking.persistence.repositories import ServiceRequestRepository


def _payload(description: str = "Synthetic fee review") -> dict[str, str]:
    return {
        "customer_id": "CUST-0001",
        "category": "FEE",
        "description": description,
    }


def test_valid_service_request_is_created_and_retrievable(client) -> None:
    response = client.post("/api/v1/service-requests", json=_payload())
    assert response.status_code == 201
    assert response.headers["Location"] == "/api/v1/service-requests/SR-000003"
    assert response.json() == {
        "service_request_id": "SR-000003",
        "customer_id": "CUST-0001",
        "category": "FEE",
        "description": "Synthetic fee review",
        "status": "OPEN",
        "created_at": response.json()["created_at"],
    }

    retrieved = client.get(response.headers["Location"])
    assert retrieved.status_code == 200
    assert retrieved.json() == response.json()


def test_description_is_trimmed_before_persistence(client) -> None:
    response = client.post("/api/v1/service-requests", json=_payload("  Synthetic review  "))
    assert response.status_code == 201
    assert response.json()["description"] == "Synthetic review"


def test_invalid_payload_uses_validation_error_contract(client) -> None:
    response = client.post("/api/v1/service-requests", json=_payload("   "))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_customer_cannot_create_service_request(client) -> None:
    payload = _payload()
    payload["customer_id"] = "CUST-9999"
    response = client.post("/api/v1/service-requests", json=payload)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


def test_unknown_service_request_returns_stable_404(client) -> None:
    response = client.get("/api/v1/service-requests/SR-999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SERVICE_REQUEST_NOT_FOUND"


def test_write_transaction_rolls_back_on_failure(client, database, monkeypatch) -> None:
    def fail_after_insert(
        repository: ServiceRequestRepository,
        customer_id: str,
        category: ServiceRequestCategory,
        description: str,
    ) -> ServiceRequest:
        record = ServiceRequest(
            service_request_id="SR-999998",
            customer_id=customer_id,
            category=category,
            description=description,
            status=ServiceRequestStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )
        repository._session.add(record)
        repository._session.flush()
        raise RuntimeError("synthetic persistence failure")

    monkeypatch.setattr(ServiceRequestRepository, "create", fail_after_insert)
    response = client.post("/api/v1/service-requests", json=_payload())
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"

    with database.session() as session:
        assert (
            session.scalar(
                select(ServiceRequest).where(ServiceRequest.service_request_id == "SR-999998")
            )
            is None
        )
