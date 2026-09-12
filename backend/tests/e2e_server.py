"""Isolated browser test server. Never initialize test accounts in the real database."""

import os
from pathlib import Path

import uvicorn

from app.config import PROJECT_ROOT, Settings
from app.database import Database
from app.domain import Role
from app.schemas import UserInput
from app.seed import initialize_business, seed_demo_catalog
from app.services.employees import EmployeeService

TEST_PASSWORD = "Solo-Pruebas-2026!"


def main():
    path = Path(os.environ["SODA_DATABASE"]).resolve()
    allowed_root = (PROJECT_ROOT / "data" / "e2e").resolve()
    if not path.is_relative_to(allowed_root) or path.exists():
        raise RuntimeError("Las pruebas necesitan una base nueva dentro de data/e2e.")
    database = Database(path)
    database.initialize()
    initialize_business(database)
    seed_demo_catalog(database)
    for username, role in (("admin", Role.ADMIN), ("caja", Role.CASHIER), ("cocina", Role.KITCHEN)):
        EmployeeService(database).create(
            UserInput(username=username, password=TEST_PASSWORD, role=role)
        )
    database.close()
    from app.main import create_app

    uvicorn.run(create_app(Settings.from_environment()), host="127.0.0.1", port=8011)


if __name__ == "__main__":
    main()
