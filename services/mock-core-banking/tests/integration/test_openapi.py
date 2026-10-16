EXPECTED_OPERATIONS = {
    "/health/live": {"get"},
    "/health/ready": {"get"},
    "/api/v1/customers/{customer_id}": {"get"},
    "/api/v1/customers/{customer_id}/loans": {"get"},
    "/api/v1/loans/{loan_id}": {"get"},
    "/api/v1/loans/{loan_id}/installments/next": {"get"},
    "/api/v1/service-requests": {"get", "post"},
    "/api/v1/service-requests/{service_request_id}": {"get"},
}


def test_openapi_contains_exact_public_path_set(client) -> None:
    schema = client.get("/openapi.json").json()
    assert schema["info"]["version"] == "0.2.0"
    assert set(schema["paths"]) == set(EXPECTED_OPERATIONS)
    for path, methods in EXPECTED_OPERATIONS.items():
        assert set(schema["paths"][path]) == methods


def test_openapi_documents_explicit_success_and_error_models(client) -> None:
    schema = client.get("/openapi.json").json()
    get = schema["paths"]["/api/v1/service-requests"]["get"]
    assert {"200", "404", "422"}.issubset(get["responses"])
    post = schema["paths"]["/api/v1/service-requests"]["post"]
    assert {"201", "404", "422"}.issubset(post["responses"])
    assert post["responses"]["201"]["content"]["application/json"]["schema"]
    assert post["responses"]["404"]["content"]["application/json"]["schema"]
    assert post["responses"]["422"]["content"]["application/json"]["schema"]


def test_openapi_customer_schema_contains_no_prohibited_fields(client) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    customer_fields = set(schemas["CustomerResponse"]["properties"])
    assert customer_fields == {
        "customer_id",
        "display_name",
        "segment",
        "status",
        "created_at",
    }
