CUSTOMER_FIELDS = {"customer_id", "display_name", "segment", "status", "created_at"}
LOAN_FIELDS = {
    "loan_id",
    "customer_id",
    "product_code",
    "currency",
    "principal_amount",
    "outstanding_balance",
    "status",
    "opened_at",
}


def test_existing_customer_uses_exact_public_contract(client) -> None:
    response = client.get("/api/v1/customers/CUST-0001")
    assert response.status_code == 200
    assert set(response.json()) == CUSTOMER_FIELDS
    assert response.json()["display_name"] == "Synthetic Customer 0001"


def test_unknown_customer_returns_stable_404(client) -> None:
    response = client.get("/api/v1/customers/CUST-9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


def test_malformed_customer_id_returns_validation_contract(client) -> None:
    response = client.get("/api/v1/customers/not-a-customer")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_customer_loans_contain_only_requested_customer(client) -> None:
    response = client.get("/api/v1/customers/CUST-0001/loans")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(loan["customer_id"] == "CUST-0001" for loan in response.json())
    assert all(set(loan) == LOAN_FIELDS for loan in response.json())
