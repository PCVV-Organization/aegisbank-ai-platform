from decimal import Decimal


def test_existing_loan_returns_decimal_money_as_strings(client) -> None:
    response = client.get("/api/v1/loans/LOAN-0001")
    assert response.status_code == 200
    data = response.json()
    assert data["loan_id"] == "LOAN-0001"
    assert data["currency"] == "PEN"
    assert data["principal_amount"] == "10000.00"
    assert data["outstanding_balance"] == "2800.00"


def test_unknown_loan_returns_stable_404(client) -> None:
    response = client.get("/api/v1/loans/LOAN-9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LOAN_NOT_FOUND"


def test_next_installment_is_earliest_unpaid_and_never_paid(client) -> None:
    response = client.get("/api/v1/loans/LOAN-0001/installments/next")
    assert response.status_code == 200
    data = response.json()
    assert data["installment_id"] == "INST-0002"
    assert data["status"] == "OVERDUE"
    assert data["status"] != "PAID"
    total = (
        Decimal(data["principal_due"]) + Decimal(data["interest_due"]) + Decimal(data["fees_due"])
    )
    assert total == Decimal(data["total_due"])


def test_loan_with_only_paid_installments_returns_defined_404(client) -> None:
    response = client.get("/api/v1/loans/LOAN-0004/installments/next")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INSTALLMENT_NOT_FOUND"


def test_next_installment_for_unknown_loan_returns_loan_error(client) -> None:
    response = client.get("/api/v1/loans/LOAN-9999/installments/next")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LOAN_NOT_FOUND"
