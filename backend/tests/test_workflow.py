import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from starlette.websockets import WebSocketDisconnect

from app.domain import BusinessError, Principal, Role
from app.models import AuditEvent, Order, Payment
from app.schemas import PaymentInput
from app.services.business import COSTA_RICA


def order_payload(product_id=1):
    return {
        "request_key": str(uuid4()),
        "items": [{"product_id": product_id, "quantity": 2}],
        "notes": "Sin cebolla",
        "service_mode": "dine_in",
        "table_number": "4",
    }


def make_order(client):
    response = client.post("/api/orders", json=order_payload())
    assert response.status_code == 201, response.text
    return response.json()


def open_shift(client, headers):
    response = client.post(
        "/api/staff/shifts", headers=headers["caja"], json={"opening_cents": 1000000}
    )
    assert response.status_code == 201, response.text
    return response.json()


def payment_payload(method="cash", **extra):
    return {"request_key": str(uuid4()), "method": method, "received_cents": 1000000, **extra}


def test_complete_restaurant_workflow(client, headers):
    shift = open_shift(client, headers)
    order = make_order(client)
    assert order["payment_status"] == "unpaid"
    assert client.get("/api/staff/orders", headers=headers["cocina"]).json() == []
    response = client.post(
        f"/api/staff/orders/{order['id']}/pay", headers=headers["caja"], json=payment_payload()
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "queued"
    assert response.json()["payment"]["change_cents"] == 1000000 - order["total_cents"]
    kitchen = client.get("/api/staff/orders", headers=headers["cocina"]).json()
    assert len(kitchen) == 1
    assert kitchen[0]["notes"] == "Sin cebolla"
    assert kitchen[0]["table_number"] == "4"
    for status in ("preparing", "ready", "delivered"):
        response = client.post(
            f"/api/staff/orders/{order['id']}/status",
            headers=headers["cocina"],
            json={"status": status},
        )
        assert response.status_code == 200
    assert client.get("/api/staff/orders", headers=headers["cocina"]).json() == []
    closed = client.post(
        f"/api/staff/shifts/{shift['id']}/close",
        headers=headers["caja"],
        json={"counted_cents": 1000000 + order["total_cents"], "notes": ""},
    )
    assert closed.json()["difference_cents"] == 0
    report = client.get("/api/admin/report", headers=headers["admin"]).json()
    assert report["orders_paid"] == 1
    assert report["by_method"]["cash"] == order["total_cents"]


def test_orders_are_idempotent_and_payload_cannot_change(client):
    payload = order_payload()
    first = client.post("/api/orders", json=payload)
    second = client.post("/api/orders", json=payload)
    assert first.json()["id"] == second.json()["id"]
    payload["items"][0]["quantity"] = 3
    assert client.post("/api/orders", json=payload).status_code == 409


def test_double_payment_and_retry(client, headers):
    open_shift(client, headers)
    order = make_order(client)
    payload = payment_payload()
    url = f"/api/staff/orders/{order['id']}/pay"
    first = client.post(url, headers=headers["caja"], json=payload)
    retry = client.post(url, headers=headers["caja"], json=payload)
    assert first.status_code == retry.status_code == 200
    assert first.json() == retry.json()
    assert client.post(url, headers=headers["caja"], json=payment_payload()).status_code == 409
    payload["received_cents"] += 100
    assert client.post(url, headers=headers["caja"], json=payload).status_code == 409


def test_concurrent_cashiers_cannot_double_charge(client, headers, app):
    open_shift(client, headers)
    order = make_order(client)
    actor = Principal(2, "caja", Role.CASHIER)

    def pay():
        try:
            app.state.orders.pay(order["id"], PaymentInput(**payment_payload()), actor)
            return "paid"
        except BusinessError as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: pay(), range(2)))
    assert sorted(map(str, results)) == ["409", "paid"]
    with app.state.database.read() as session:
        assert session.scalar(select(func.count()).select_from(Payment)) == 1
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.action == "order.paid")
            )
            == 1
        )


def test_failed_cash_payment_does_not_reach_kitchen(client, headers, app):
    open_shift(client, headers)
    order = make_order(client)
    response = client.post(
        f"/api/staff/orders/{order['id']}/pay",
        headers=headers["caja"],
        json=payment_payload(received_cents=100),
    )
    assert response.status_code == 400
    with app.state.database.read() as session:
        saved = session.get(Order, order["id"])
        assert saved.payment_status == "unpaid"
        assert saved.status == "awaiting_payment"
        assert session.scalar(select(func.count()).select_from(Payment)) == 0


def test_requires_open_shift(client, headers):
    order = make_order(client)
    response = client.post(
        f"/api/staff/orders/{order['id']}/pay", headers=headers["caja"], json=payment_payload()
    )
    assert response.status_code == 409


@pytest.mark.parametrize("method", ["card", "sinpe"])
def test_electronic_payments_have_no_change(client, headers, method):
    open_shift(client, headers)
    order = make_order(client)
    response = client.post(
        f"/api/staff/orders/{order['id']}/pay",
        headers=headers["caja"],
        json=payment_payload(method, received_cents=None, reference="ABC123"),
    )
    assert response.status_code == 200
    assert response.json()["payment"]["change_cents"] == 0
    assert (
        client.get("/api/staff/shifts", headers=headers["caja"]).json()["current"][
            "cash_sales_cents"
        ]
        == 0
    )


def test_product_price_snapshot_and_unavailable_products(client, headers):
    order = make_order(client)
    products = client.get("/api/admin/catalog", headers=headers["admin"]).json()["products"]
    product = next(p for p in products if p["id"] == 1)
    product_id = product.pop("id")
    product["name"] = "Nombre nuevo"
    product["price_cents"] = 990000
    product["available"] = False
    response = client.put(
        f"/api/admin/products/{product_id}", headers=headers["admin"], json=product
    )
    assert response.status_code == 200
    saved = client.get("/api/staff/orders", headers=headers["caja"]).json()[0]
    assert saved["total_cents"] == order["total_cents"]
    assert saved["items"][0]["name"] == order["items"][0]["name"]
    assert client.post("/api/orders", json=order_payload()).status_code == 409


def test_permissions_are_enforced_on_server(client, headers):
    assert client.get("/api/admin/users").status_code == 401
    assert client.get("/api/admin/users", headers=headers["caja"]).status_code == 403
    assert client.get("/api/staff/shifts", headers=headers["cocina"]).status_code == 403
    order = make_order(client)
    assert (
        client.post(
            f"/api/staff/orders/{order['id']}/pay",
            headers=headers["cocina"],
            json=payment_payload(),
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/staff/orders/{order['id']}/status",
            headers=headers["caja"],
            json={"status": "preparing"},
        ).status_code
        == 403
    )


def test_invalid_and_skipped_transitions(client, headers):
    order = make_order(client)
    url = f"/api/staff/orders/{order['id']}/status"
    assert (
        client.post(url, headers=headers["cocina"], json={"status": "preparing"}).status_code == 409
    )
    open_shift(client, headers)
    client.post(
        f"/api/staff/orders/{order['id']}/pay", headers=headers["caja"], json=payment_payload()
    )
    assert (
        client.post(url, headers=headers["cocina"], json={"status": "delivered"}).status_code == 409
    )
    assert (
        client.post(url, headers=headers["cocina"], json={"status": "cancelled"}).status_code == 409
    )


@pytest.mark.parametrize("quantity", [0, -1, 51, 1.5, True])
def test_invalid_quantities_rejected(client, quantity):
    payload = order_payload()
    payload["items"][0]["quantity"] = quantity
    assert client.post("/api/orders", json=payload).status_code == 422


def test_client_cannot_override_total(client):
    payload = order_payload()
    payload["total_cents"] = 1
    assert client.post("/api/orders", json=payload).status_code == 422


def test_cancelled_order_cannot_be_paid(client, headers):
    open_shift(client, headers)
    order = make_order(client)
    assert (
        client.post(
            f"/api/staff/orders/{order['id']}/cancel",
            headers=headers["caja"],
            json={"reason": "Cliente desistió"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/staff/orders/{order['id']}/pay", headers=headers["caja"], json=payment_payload()
        ).status_code
        == 409
    )


def test_account_deactivation_revokes_access(client, headers):
    response = client.put(
        "/api/admin/users/2", headers=headers["admin"], json={"role": "cashier", "active": False}
    )
    assert response.status_code == 200
    assert client.get("/api/auth/me", headers=headers["caja"]).status_code == 401
    assert (
        client.put(
            "/api/admin/users/1", headers=headers["admin"], json={"role": "kitchen", "active": True}
        ).status_code
        == 400
    )


def test_logout_revokes_session(client, headers):
    assert client.post("/api/auth/logout", headers=headers["caja"]).status_code == 204
    assert client.get("/api/auth/me", headers=headers["caja"]).status_code == 401


def test_shift_difference_and_duplicate_open(client, headers):
    shift = open_shift(client, headers)
    assert (
        client.post(
            "/api/staff/shifts", headers=headers["caja"], json={"opening_cents": 0}
        ).status_code
        == 409
    )
    closed = client.post(
        f"/api/staff/shifts/{shift['id']}/close",
        headers=headers["caja"],
        json={"counted_cents": 999000},
    )
    assert closed.json()["difference_cents"] == -1000


def test_consistent_backup_contains_live_data(client, app, tmp_path):
    make_order(client)
    target = tmp_path / "backup.sqlite3"
    app.state.database.backup(target)
    with sqlite3.connect(target) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1


def test_csv_export_and_local_day(client, headers):
    open_shift(client, headers)
    order = make_order(client)
    client.post(
        f"/api/staff/orders/{order['id']}/pay", headers=headers["caja"], json=payment_payload()
    )
    report = client.get("/api/admin/report", headers=headers["admin"]).json()
    assert report["day"] == datetime.now(COSTA_RICA).date().isoformat()
    csv = client.get("/api/admin/sales.csv", headers=headers["admin"])
    assert csv.status_code == 200
    assert "Monto CRC" in csv.text
    assert "Efectivo" in csv.text


def test_websocket_authentication_and_change_feed(client, headers):
    token = headers["admin"]["Authorization"].split()[1]
    with client.websocket_connect("/api/events") as socket:
        socket.send_json({"token": token})
        event = socket.receive_json()
        assert event["type"] == "changed"
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/api/events") as socket:
        socket.send_json({"token": "invalid"})
        socket.receive_json()
