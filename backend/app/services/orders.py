import hashlib
import time

from sqlalchemy import select

from app.database import Database
from app.domain import NEXT_STATUS, BusinessError, PaymentMethod, PreparationStatus, Principal
from app.models import BusinessSettings, CashShift, Order, OrderItem, Payment, Product
from app.schemas import OrderInput, PaymentInput
from app.services.audit import record


def fingerprint(data) -> str:
    serialized = data.model_dump_json(exclude={"request_key"})
    return hashlib.sha256(serialized.encode()).hexdigest()


def order_view(order: Order) -> dict:
    payment = order.payment
    return {
        "id": order.id,
        "number": f"{order.id:04d}",
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_cents": order.total_cents,
        "notes": order.notes,
        "service_mode": order.service_mode,
        "table_number": order.table_number,
        "items": [
            {
                "product_id": item.product_id,
                "name": item.product_name,
                "quantity": item.quantity,
                "unit_price_cents": item.unit_price_cents,
            }
            for item in order.items
        ],
        "payment": {
            "method": payment.method,
            "amount_cents": payment.amount_cents,
            "received_cents": payment.received_cents,
            "change_cents": payment.received_cents - payment.amount_cents,
            "reference": payment.reference,
        }
        if payment
        else None,
    }


class OrderService:
    def __init__(self, database: Database):
        self.database = database

    def create(self, data: OrderInput) -> dict:
        key, signature = str(data.request_key), fingerprint(data)
        with self.database.write() as session:
            existing = session.scalar(select(Order).where(Order.request_key == key))
            if existing:
                if existing.request_fingerprint != signature:
                    raise BusinessError("Ese intento corresponde a otro pedido.", 409)
                return order_view(existing)
            settings = session.get(BusinessSettings, 1)
            if settings and not settings.accepting_orders:
                raise BusinessError(settings.closed_message, 409)
            product_ids = [line.product_id for line in data.items]
            if len(set(product_ids)) != len(product_ids):
                raise BusinessError("Agrupá las cantidades de cada producto.")
            products = {
                p.id: p for p in session.scalars(select(Product).where(Product.id.in_(product_ids)))
            }
            items = []
            for line in data.items:
                product = products.get(line.product_id)
                if not product or not product.available:
                    raise BusinessError("Un producto ya no está disponible. Revisá el menú.", 409)
                items.append(
                    OrderItem(
                        product_id=product.id,
                        product_name=product.name,
                        quantity=line.quantity,
                        unit_price_cents=product.price_cents,
                    )
                )
            total = sum(i.quantity * i.unit_price_cents for i in items)
            if total > 100_000_000:
                raise BusinessError("El pedido supera el monto máximo permitido.")
            now = int(time.time())
            order = Order(
                request_key=key,
                request_fingerprint=signature,
                created_at=now,
                updated_at=now,
                total_cents=total,
                notes=data.notes.strip(),
                items=items,
                service_mode=data.service_mode,
                table_number=data.table_number.strip(),
            )
            session.add(order)
            session.flush()
            record(session, None, "order.created", order.id, total_cents=total)
            return order_view(order)

    def list(self, kitchen: bool = False, history: bool = False) -> list[dict]:
        with self.database.read() as session:
            query = select(Order)
            if kitchen:
                query = query.where(
                    Order.payment_status == "paid",
                    Order.status.in_(["queued", "preparing", "ready"]),
                )
            elif not history:
                query = query.where(Order.status.not_in(["delivered", "cancelled"]))
            query = query.order_by(Order.created_at.desc(), Order.id.desc()).limit(300)
            return [order_view(order) for order in session.scalars(query)]

    def pay(self, order_id: int, data: PaymentInput, actor: Principal) -> dict:
        key, signature = str(data.request_key), fingerprint(data)
        with self.database.write() as session:
            existing = session.scalar(select(Payment).where(Payment.request_key == key))
            if existing:
                if existing.order_id != order_id or existing.request_fingerprint != signature:
                    raise BusinessError("Ese intento corresponde a otro pago.", 409)
                return order_view(session.get(Order, order_id))
            order = session.get(Order, order_id)
            if not order:
                raise BusinessError("Pedido no encontrado.", 404)
            if order.payment_status == "paid":
                raise BusinessError("Este pedido ya fue cobrado.", 409)
            if order.status != PreparationStatus.AWAITING_PAYMENT:
                raise BusinessError("Este pedido no se puede cobrar.", 409)
            shift = session.scalar(select(CashShift).where(CashShift.closed_at.is_(None)))
            if not shift:
                raise BusinessError("Abrí la caja antes de registrar pagos.", 409)
            received = order.total_cents
            if data.method == PaymentMethod.CASH:
                if data.received_cents is None or data.received_cents < order.total_cents:
                    raise BusinessError("El efectivo recibido no cubre el total.")
                received = data.received_cents
            elif data.received_cents is not None and data.received_cents != order.total_cents:
                raise BusinessError("Los pagos electrónicos deben coincidir con el total.")
            now = int(time.time())
            order.payment = Payment(
                order_id=order.id,
                shift_id=shift.id,
                request_key=key,
                request_fingerprint=signature,
                cashier_id=actor.id,
                method=data.method,
                amount_cents=order.total_cents,
                received_cents=received,
                reference=data.reference.strip(),
                created_at=now,
            )
            order.payment_status = "paid"
            order.status = PreparationStatus.QUEUED
            order.updated_at = now
            record(
                session,
                actor.id,
                "order.paid",
                order.id,
                method=data.method,
                amount_cents=order.total_cents,
                shift_id=shift.id,
            )
            session.flush()
            return order_view(order)

    def advance(self, order_id: int, status: PreparationStatus, actor: Principal) -> dict:
        with self.database.write() as session:
            order = session.get(Order, order_id)
            if not order:
                raise BusinessError("Pedido no encontrado.", 404)
            if order.payment_status != "paid":
                raise BusinessError("El pedido todavía no está pagado.", 409)
            if order.status == status:
                return order_view(order)
            if NEXT_STATUS.get(order.status) != status:
                raise BusinessError(
                    "El pedido cambió. Actualizá y seguí el orden de preparación.", 409
                )
            previous = order.status
            order.status = status
            order.updated_at = int(time.time())
            record(session, actor.id, "order.status", order.id, previous=previous, status=status)
            return order_view(order)

    def cancel(self, order_id: int, reason: str, actor: Principal) -> dict:
        with self.database.write() as session:
            order = session.get(Order, order_id)
            if not order:
                raise BusinessError("Pedido no encontrado.", 404)
            if order.status != PreparationStatus.AWAITING_PAYMENT:
                raise BusinessError("Solo se pueden cancelar pedidos pendientes de pago.", 409)
            order.status = PreparationStatus.CANCELLED
            order.updated_at = int(time.time())
            record(session, actor.id, "order.cancelled", order.id, reason=reason)
            return order_view(order)
