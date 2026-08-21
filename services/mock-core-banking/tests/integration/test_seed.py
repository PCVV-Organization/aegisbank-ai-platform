from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select

from mock_core_banking.config import Settings
from mock_core_banking.main import create_app
from mock_core_banking.persistence.models import Customer, Installment, Loan, ServiceRequest
from mock_core_banking.persistence.seed import build_seed_data, seed_database
from mock_core_banking.schemas import (
    CustomerResponse,
    InstallmentResponse,
    LoanResponse,
    ServiceRequestResponse,
)


def _count(database, model: type) -> int:
    with database.session() as session:
        return session.scalar(select(func.count()).select_from(model)) or 0


def test_seed_has_required_counts_and_valid_relationships(database) -> None:
    assert _count(database, Customer) == 3
    assert _count(database, Loan) == 4
    assert _count(database, Installment) == 10
    assert _count(database, ServiceRequest) == 2

    customers, loans, installments, service_requests = build_seed_data()
    customer_ids = {customer.customer_id for customer in customers}
    loan_ids = {loan.loan_id for loan in loans}
    assert all(loan.customer_id in customer_ids for loan in loans)
    assert all(installment.loan_id in loan_ids for installment in installments)
    assert all(request.customer_id in customer_ids for request in service_requests)


def test_seed_is_deterministic_and_idempotent(database) -> None:
    first = build_seed_data()
    second = build_seed_data()
    assert [customer.customer_id for customer in first[0]] == [
        customer.customer_id for customer in second[0]
    ]
    assert [installment.total_due for installment in first[2]] == [
        installment.total_due for installment in second[2]
    ]

    seed_database(database)
    assert _count(database, Customer) == 3
    assert _count(database, ServiceRequest) == 2


def test_created_service_request_survives_application_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "restart.db"
    settings = Settings(
        environment="testing",
        database_url=f"sqlite:///{database_path.as_posix()}",
    )
    with TestClient(create_app(settings)) as first_client:
        created = first_client.post(
            "/api/v1/service-requests",
            json={
                "customer_id": "CUST-0001",
                "category": "GENERAL",
                "description": "Persist across restart",
            },
        )
        assert created.status_code == 201
        location = created.headers["Location"]

    with TestClient(create_app(settings)) as second_client:
        retrieved = second_client.get(location)
        assert retrieved.status_code == 200
        assert retrieved.json()["description"] == "Persist across restart"


def test_database_schema_excludes_prohibited_fields(database) -> None:
    prohibited = {
        "dni",
        "document_number",
        "phone",
        "email",
        "address",
        "card_number",
        "cvv",
        "password",
        "real_account_number",
        "biometric",
    }
    inspector = inspect(database.engine)
    columns = {
        column["name"]
        for table in inspector.get_table_names()
        for column in inspector.get_columns(table)
    }
    assert columns.isdisjoint(prohibited)

    public_fields = set().union(
        CustomerResponse.model_fields,
        LoanResponse.model_fields,
        InstallmentResponse.model_fields,
        ServiceRequestResponse.model_fields,
    )
    assert public_fields.isdisjoint(prohibited)


def test_installment_totals_match_seed_components() -> None:
    installments = build_seed_data()[2]
    for installment in installments:
        assert installment.total_due == (
            installment.principal_due + installment.interest_due + installment.fees_due
        )


def test_customer_seed_is_obviously_synthetic() -> None:
    customers = build_seed_data()[0]
    assert all(customer.customer_id.startswith("CUST-00") for customer in customers)
    assert all(customer.display_name.startswith("Synthetic Customer ") for customer in customers)
