import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domain import Role
from app.main import create_app
from app.schemas import UserInput
from app.seed import seed_demo_catalog

TEST_PASSWORD = "Pruebas-locales-2026"


@pytest.fixture
def app(tmp_path):
    return create_app(
        Settings(database_path=tmp_path / "test.sqlite3", static_path=tmp_path / "no-frontend")
    )


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        for username, role in (
            ("admin", Role.ADMIN),
            ("caja", Role.CASHIER),
            ("cocina", Role.KITCHEN),
        ):
            app.state.employees.create(
                UserInput(username=username, password=TEST_PASSWORD, role=role)
            )
        seed_demo_catalog(app.state.database)
        yield client


@pytest.fixture
def headers(client):
    result = {}
    for username in ("admin", "caja", "cocina"):
        response = client.post(
            "/api/auth/login", json={"username": username, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        result[username] = {"Authorization": "Bearer " + response.json()["token"]}
    return result
