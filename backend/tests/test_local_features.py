import io
import sqlite3
import zipfile
from uuid import uuid4

import pytest
from PIL import Image

from app.database import Database
from app.migrations import ADDITIONS_V2


@pytest.mark.parametrize("password", ["1", "abc", " á ñ🔐 ! ", "a" * 200])
def test_passwords_accept_simple_unicode_and_long_values(client, headers, password):
    created = client.post(
        "/api/admin/users",
        headers=headers["admin"],
        json={"username": "simple", "password": password, "role": "cashier"},
    )
    assert created.status_code == 201
    assert (
        client.post(
            "/api/auth/login", json={"username": "simple", "password": password}
        ).status_code
        == 200
    )
    changed = client.put(
        f"/api/admin/users/{created.json()['id']}",
        headers=headers["admin"],
        json={"role": "cashier", "active": True, "password": "ñ"},
    )
    assert changed.status_code == 200
    assert (
        client.post("/api/auth/login", json={"username": "simple", "password": "ñ"}).status_code
        == 200
    )
    assert (
        client.post(
            "/api/admin/users",
            headers=headers["admin"],
            json={"username": "empty", "password": "", "role": "cashier"},
        ).status_code
        == 422
    )


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (80, 60), "#9b3f23").save(output, "PNG")
    return output.getvalue()


def test_local_images_branding_and_full_backup(client, headers, app):
    data = image_bytes()
    assert client.post("/api/admin/media", content=data).status_code == 401
    assert client.post("/api/admin/media", content=data, headers=headers["caja"]).status_code == 403
    result = client.post("/api/admin/media", content=data, headers=headers["admin"])
    assert result.status_code == 201
    url = result.json()["url"]
    fetched = client.get(url)
    assert fetched.status_code == 200
    assert fetched.headers["content-type"] == "image/webp"
    with Image.open(io.BytesIO(fetched.content)) as image:
        assert image.size == (80, 60)
        assert not image.getexif()
    business = client.get("/api/business").json()
    business.update(logo_url=url, primary_color="#321abc", accepting_orders=False)
    assert (
        client.put("/api/admin/business", json=business, headers=headers["admin"]).status_code
        == 200
    )
    assert client.get("/api/business").json()["primary_color"] == "#321abc"
    product = client.get("/api/admin/catalog", headers=headers["admin"]).json()["products"][0]
    product_id = product.pop("id")
    product.update(image_url=url, featured=True, allergens="Leche", cabys="1234567890123")
    assert (
        client.put(
            f"/api/admin/products/{product_id}", json=product, headers=headers["admin"]
        ).status_code
        == 200
    )
    assert client.get("/api/catalog").json()["products"][0]["id"] == product_id
    response = client.post("/api/admin/backup", headers=headers["admin"])
    name = response.json()["filename"]
    assert client.get("/api/admin/backups/" + name).status_code == 401
    archive_response = client.get("/api/admin/backups/" + name, headers=headers["admin"])
    with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
        assert "soda.sqlite3" in archive.namelist()
        assert "media/" + url.split("/")[-1] in archive.namelist()
        restored = app.state.database.path.parent / "restored"
        archive.extractall(restored)
    database = Database(restored / "soda.sqlite3")
    database.initialize()
    with sqlite3.connect(database.path) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT logo_url FROM business_settings").fetchone()[0] == url
    database.close()


def test_media_validation_and_private_fiscal_profile(client, headers):
    for payload in (b"<svg/>", b"this is not an image"):
        assert (
            client.post("/api/admin/media", content=payload, headers=headers["admin"]).status_code
            == 422
        )
    assert (
        client.post(
            "/api/admin/media", content=b"x" * (5 * 1024 * 1024 + 1), headers=headers["admin"]
        ).status_code
        == 413
    )
    business = client.get("/api/business").json()
    for field, value in (
        ("primary_color", "url(https://example.com)"),
        ("logo_url", "https://example.com/logo.png"),
        ("cover_url", "/api/media/" + "f" * 32 + ".webp"),
    ):
        bad = {**business, field: value}
        assert (
            client.put("/api/admin/business", json=bad, headers=headers["admin"]).status_code == 422
        )
    assert client.get("/api/admin/fiscal").status_code == 401
    assert client.get("/api/admin/fiscal", headers=headers["caja"]).status_code == 403
    profile = client.get("/api/admin/fiscal", headers=headers["admin"]).json()
    profile.update(
        legal_name="Mi Negocio SA", identification="3101123456", email="fiscal@example.com"
    )
    assert (
        client.put("/api/admin/fiscal", json=profile, headers=headers["admin"]).status_code == 200
    )
    assert "legal_name" not in client.get("/api/business").json()


def test_pause_rejects_new_orders_but_allows_existing_retry(client, headers):
    payload = {"request_key": str(uuid4()), "items": [{"product_id": 1, "quantity": 1}]}
    order = client.post("/api/orders", json=payload).json()
    business = client.get("/api/business").json()
    business.update(accepting_orders=False, closed_message="Volvemos mañana")
    client.put("/api/admin/business", json=business, headers=headers["admin"])
    assert client.post("/api/orders", json=payload).json()["id"] == order["id"]
    payload["request_key"] = str(uuid4())
    blocked = client.post("/api/orders", json=payload)
    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "Volvemos mañana"
    business["accepting_orders"] = True
    client.put("/api/admin/business", json=business, headers=headers["admin"])
    assert client.post("/api/orders", json=payload).status_code == 201


def test_cash_movements_balance_idempotency_and_closed_shift(client, headers):
    shift = client.post(
        "/api/staff/shifts", json={"opening_cents": 100000}, headers=headers["caja"]
    ).json()
    url = f"/api/staff/shifts/{shift['id']}/movements"
    draft = {
        "request_key": str(uuid4()),
        "kind": "expense",
        "amount_cents": 25000,
        "reason": "Compra de hielo",
    }
    first = client.post(url, json=draft, headers=headers["caja"])
    assert first.status_code == 201
    assert client.post(url, json=draft, headers=headers["caja"]).json() == first.json()
    assert (
        client.post(url, json={**draft, "amount_cents": 20000}, headers=headers["caja"]).status_code
        == 409
    )
    assert (
        client.post(
            url,
            json={**draft, "request_key": str(uuid4()), "amount_cents": 76000},
            headers=headers["caja"],
        ).status_code
        == 409
    )
    deposit = {**draft, "request_key": str(uuid4()), "kind": "deposit", "amount_cents": 10000}
    assert client.post(url, json=deposit, headers=headers["cocina"]).status_code == 403
    assert client.post(url, json=deposit, headers=headers["caja"]).status_code == 201
    current = client.get("/api/staff/shifts", headers=headers["caja"]).json()["current"]
    assert current["expected_cents"] == 85000
    assert current["cash_sales_cents"] == 0
    assert len(current["movements"]) == 2
    closed = client.post(
        f"/api/staff/shifts/{shift['id']}/close",
        json={"counted_cents": 85000},
        headers=headers["caja"],
    ).json()
    assert closed["difference_cents"] == 0
    assert client.post(url, json=draft, headers=headers["caja"]).json() == first.json()
    assert (
        client.post(
            url, json={**deposit, "request_key": str(uuid4())}, headers=headers["caja"]
        ).status_code
        == 409
    )


def test_v1_migration_preserves_existing_data_and_creates_backup(client, app, tmp_path):
    legacy = tmp_path / "legacy" / "soda.sqlite3"
    app.state.database.backup(legacy)
    with sqlite3.connect(legacy) as db:
        for table, columns in ADDITIONS_V2.items():
            for name in columns:
                db.execute(f'ALTER TABLE "{table}" DROP COLUMN "{name}"')
        db.execute("DROP TABLE cash_movements")
        db.execute("DROP TABLE fiscal_profiles")
        db.execute("PRAGMA user_version=1")
        old_products = db.execute("SELECT id, name, price_cents FROM products").fetchall()
    migrated = Database(legacy)
    migrated.initialize()
    migrated.initialize()
    with sqlite3.connect(legacy) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert db.execute("SELECT id, name, price_cents FROM products").fetchall() == old_products
        assert db.execute("SELECT accepting_orders FROM business_settings").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 3
    backups = list((legacy.parent / "backups").glob("pre-upgrade-v1-*.sqlite3"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
    migrated.close()
