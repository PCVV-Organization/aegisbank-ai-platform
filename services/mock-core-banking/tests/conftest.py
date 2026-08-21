from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mock_core_banking.config import Settings
from mock_core_banking.main import create_app
from mock_core_banking.persistence.database import Database


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "aegisbank-test.db"


@pytest.fixture
def app(database_path: Path) -> FastAPI:
    settings = Settings(
        environment="testing",
        database_url=f"sqlite:///{database_path.as_posix()}",
    )
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI):
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def database(client: TestClient) -> Database:
    return client.app.state.database
