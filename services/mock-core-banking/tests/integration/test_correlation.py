import uuid


def test_valid_correlation_id_is_preserved(client) -> None:
    correlation_id = "client.request:2026-08-20_01"
    response = client.get("/health/live", headers={"X-Correlation-ID": correlation_id})
    assert response.headers["X-Correlation-ID"] == correlation_id


def test_missing_correlation_id_generates_uuid(client) -> None:
    response = client.get("/health/live")
    uuid.UUID(response.headers["X-Correlation-ID"])


def test_invalid_or_oversized_correlation_id_is_replaced(client) -> None:
    for invalid in ("invalid id", "x" * 65, "value\nother"):
        response = client.get("/health/live", headers={"X-Correlation-ID": invalid})
        assert response.headers["X-Correlation-ID"] != invalid
        uuid.UUID(response.headers["X-Correlation-ID"])


def test_error_header_matches_error_body(client) -> None:
    response = client.get(
        "/api/v1/customers/CUST-9999",
        headers={"X-Correlation-ID": "error-correlation"},
    )
    assert response.headers["X-Correlation-ID"] == "error-correlation"
    assert response.json()["error"]["correlation_id"] == "error-correlation"


def test_openapi_response_is_correlated(client) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    uuid.UUID(response.headers["X-Correlation-ID"])
