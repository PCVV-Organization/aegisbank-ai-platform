def test_error_contract_contains_only_public_fields(client) -> None:
    response = client.get("/api/v1/customers/CUST-9999")
    assert response.status_code == 404
    assert set(response.json()) == {"error"}
    assert set(response.json()["error"]) == {"code", "message", "correlation_id"}


def test_validation_response_does_not_echo_input(client) -> None:
    marker = "do-not-echo-this-value"
    response = client.post(
        "/api/v1/service-requests",
        json={
            "customer_id": "CUST-0001",
            "category": "INVALID",
            "description": marker,
        },
    )
    assert response.status_code == 422
    assert marker not in response.text
    assert response.json()["error"]["message"] == "Request validation failed."
    assert set(response.json()["error"]) == {"code", "message", "correlation_id"}


def test_malformed_json_uses_validation_envelope(client) -> None:
    response = client.post(
        "/api/v1/service-requests",
        content=b'{"customer_id":',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_method_not_allowed_uses_error_envelope(client) -> None:
    response = client.post("/health/live")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert response.headers["X-Correlation-ID"] == response.json()["error"]["correlation_id"]
