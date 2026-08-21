def test_liveness_is_exact_and_correlated(client) -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "aegisbank-mock-core",
        "version": "0.2.0",
    }
    assert response.headers["X-Correlation-ID"]


def test_readiness_checks_available_database(client) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_returns_safe_503_when_database_is_unavailable(
    client, database, monkeypatch
) -> None:
    monkeypatch.setattr(database, "is_ready", lambda: False)
    response = client.get("/health/ready", headers={"X-Correlation-ID": "ready-test"})
    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "DATASTORE_UNAVAILABLE",
            "message": "Local datastore is unavailable.",
            "correlation_id": "ready-test",
        }
    }
    assert response.headers["X-Correlation-ID"] == "ready-test"
