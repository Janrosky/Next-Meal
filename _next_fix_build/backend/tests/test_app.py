from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_core_ticket_flow(tmp_path: Path):
    app = create_app(Settings(tmp_path / "test.sqlite3", tmp_path / "missing"))
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        customers = client.get("/api/customers").json()
        created = client.post("/api/tickets", json={
            "customer_id": customers[0]["id"],
            "asset_type": "Automóvil",
            "brand": "Honda",
            "model": "Civic",
            "issue": "No enciende",
            "priority": "urgent",
        })
        assert created.status_code == 201
        ticket = created.json()
        assert ticket["code"].startswith("NF-")
        updated = client.post(f"/api/tickets/{ticket['id']}/status", json={"status": "diagnosing"})
        assert updated.json()["status"] == "diagnosing"
        assert client.get("/api/dashboard").json()["active"] >= 1
