import asyncio
import csv
import io
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from app.domain import BusinessError, Principal, Role
from app.schemas import (
    BusinessInput,
    CancelInput,
    CategoryInput,
    LoginInput,
    OrderInput,
    PaymentInput,
    ProductInput,
    ShiftCloseInput,
    ShiftOpenInput,
    StatusInput,
    UserInput,
    UserUpdate,
)
from app.services.business import COSTA_RICA

router = APIRouter(prefix="/api")
bearer = HTTPBearer(auto_error=False)


def require(*roles: Role):
    def dependency(
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> Principal:
        if not credentials or credentials.scheme.lower() != "bearer":
            raise BusinessError("Iniciá sesión para continuar.", 401)
        actor = request.app.state.auth.authenticate(credentials.credentials)
        if roles and actor.role not in roles:
            raise BusinessError("Tu perfil no tiene permiso para esta acción.", 403)
        return actor

    return dependency


Staff = Annotated[Principal, Depends(require())]
Admin = Annotated[Principal, Depends(require(Role.ADMIN))]
Cashier = Annotated[Principal, Depends(require(Role.ADMIN, Role.CASHIER))]
Kitchen = Annotated[Principal, Depends(require(Role.ADMIN, Role.KITCHEN))]


def changed(request: Request, result):
    request.app.state.feed.publish()
    return result


@router.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@router.get("/business")
def business(request: Request):
    return request.app.state.business.settings()


@router.get("/catalog")
def catalog(request: Request):
    return request.app.state.catalog.list()


@router.post("/orders", status_code=201)
def create_order(data: OrderInput, request: Request):
    request.app.state.order_limiter.check(request.client.host if request.client else "local")
    return changed(request, request.app.state.orders.create(data))


@router.post("/auth/login")
def login(data: LoginInput, request: Request):
    return request.app.state.auth.login(
        data.username, data.password, request.client.host if request.client else "local"
    )


@router.get("/auth/me")
def me(actor: Staff):
    return {"id": actor.id, "username": actor.username, "role": actor.role}


@router.post("/auth/logout", status_code=204)
def logout(request: Request, actor: Staff):
    token = request.headers["authorization"].split(" ", 1)[1]
    request.app.state.auth.logout(token)


@router.get("/staff/orders")
def orders(request: Request, actor: Staff, history: bool = False):
    return request.app.state.orders.list(kitchen=actor.role == Role.KITCHEN, history=history)


@router.post("/staff/orders/{order_id}/pay")
def pay(order_id: int, data: PaymentInput, request: Request, actor: Cashier):
    return changed(request, request.app.state.orders.pay(order_id, data, actor))


@router.post("/staff/orders/{order_id}/status")
def advance(order_id: int, data: StatusInput, request: Request, actor: Kitchen):
    return changed(request, request.app.state.orders.advance(order_id, data.status, actor))


@router.post("/staff/orders/{order_id}/cancel")
def cancel(order_id: int, data: CancelInput, request: Request, actor: Cashier):
    return changed(request, request.app.state.orders.cancel(order_id, data.reason, actor))


@router.get("/staff/shifts")
def shifts(request: Request, actor: Cashier):
    return request.app.state.business.shifts()


@router.post("/staff/shifts", status_code=201)
def open_shift(data: ShiftOpenInput, request: Request, actor: Cashier):
    return changed(request, request.app.state.business.open_shift(data.opening_cents, actor))


@router.post("/staff/shifts/{shift_id}/close")
def close_shift(shift_id: int, data: ShiftCloseInput, request: Request, actor: Cashier):
    return changed(
        request,
        request.app.state.business.close_shift(shift_id, data.counted_cents, data.notes, actor),
    )


@router.get("/admin/catalog")
def admin_catalog(request: Request, actor: Admin):
    return request.app.state.catalog.list(include_unavailable=True)


@router.post("/admin/categories", status_code=201)
def create_category(data: CategoryInput, request: Request, actor: Admin):
    return changed(request, request.app.state.catalog.save_category(data, actor, None))


@router.put("/admin/categories/{category_id}")
def update_category(category_id: int, data: CategoryInput, request: Request, actor: Admin):
    return changed(request, request.app.state.catalog.save_category(data, actor, category_id))


@router.post("/admin/products", status_code=201)
def create_product(data: ProductInput, request: Request, actor: Admin):
    return changed(request, request.app.state.catalog.save_product(data, actor, None))


@router.put("/admin/products/{product_id}")
def update_product(product_id: int, data: ProductInput, request: Request, actor: Admin):
    return changed(request, request.app.state.catalog.save_product(data, actor, product_id))


@router.get("/admin/users")
def users(request: Request, actor: Admin):
    return request.app.state.employees.list()


@router.post("/admin/users", status_code=201)
def create_user(data: UserInput, request: Request, actor: Admin):
    return changed(request, request.app.state.employees.create(data, actor))


@router.put("/admin/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, request: Request, actor: Admin):
    return changed(request, request.app.state.employees.update(user_id, data, actor))


@router.put("/admin/business")
def update_business(data: BusinessInput, request: Request, actor: Admin):
    return changed(request, request.app.state.business.save_settings(data, actor))


@router.get("/admin/report")
def report(request: Request, actor: Admin, day: str = Query(default="")):
    try:
        report_day = (
            datetime.strptime(day, "%Y-%m-%d").date() if day else datetime.now(COSTA_RICA).date()
        )
    except ValueError as error:
        raise BusinessError("Fecha inválida. Usá AAAA-MM-DD.") from error
    return request.app.state.business.report(report_day)


@router.get("/admin/sales.csv")
def sales_csv(request: Request, actor: Admin, day: str = ""):
    data = report(request, actor, day)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Pedido", "Fecha Costa Rica", "Medio", "Monto CRC", "Cajero"])
    methods = {"cash": "Efectivo", "card": "Tarjeta", "sinpe": "SINPE Móvil"}
    for sale in data["sales"]:
        writer.writerow(
            [
                sale["order_id"],
                sale["time"],
                methods[sale["method"]],
                f"{sale['amount_cents'] // 100}.{sale['amount_cents'] % 100:02d}",
                sale["cashier_id"],
            ]
        )
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ventas-{data["day"]}.csv"'},
    )


@router.get("/admin/audit")
def audit(request: Request, actor: Admin):
    return request.app.state.business.audit()


@router.post("/admin/backup")
def backup(request: Request, actor: Admin):
    name = "soda-" + datetime.now(COSTA_RICA).strftime("%Y%m%d-%H%M%S-%f") + ".sqlite3"
    target = request.app.state.database.path.parent / "backups" / name
    request.app.state.database.backup(target)
    return {"filename": name, "message": "Respaldo guardado en data/backups del servidor."}


@router.websocket("/events")
async def events(websocket: WebSocket):
    await websocket.accept()
    try:
        # Tokens are sent in the first message so access logs never contain them.
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5)
        token = message.get("token", "")
        if not isinstance(token, str) or len(token) > 200:
            await websocket.close(code=1008)
            return
        revision = -1
        while True:
            await run_in_threadpool(websocket.app.state.auth.authenticate, token)
            current = websocket.app.state.feed.revision()
            if current != revision:
                await websocket.send_json({"type": "changed", "revision": current})
                revision = current
            else:
                await websocket.send_json({"type": "heartbeat"})
            await asyncio.sleep(2)
    except (BusinessError, TimeoutError, ValueError, AttributeError):
        await websocket.close(code=1008)
    except (WebSocketDisconnect, RuntimeError, OSError):
        return
