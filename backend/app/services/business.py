import time
from datetime import UTC, date, datetime, timedelta, timezone

from sqlalchemy import func, select

from app.database import Database
from app.domain import BusinessError, Principal
from app.models import (
    AuditEvent,
    BusinessSettings,
    CashMovement,
    CashShift,
    FiscalProfile,
    Order,
    OrderItem,
    Payment,
    User,
)
from app.schemas import BusinessInput, CashMovementInput, FiscalInput
from app.services.audit import record
from app.services.media import check_image

COSTA_RICA = timezone(timedelta(hours=-6))


def business_view(settings: BusinessSettings) -> dict:
    return {key: getattr(settings, key) for key in BusinessInput.model_fields}


def shift_view(shift: CashShift, cash_sales: int, movements: list) -> dict:
    movement_total = sum(
        m.amount_cents if m.kind == "deposit" else -m.amount_cents for m in movements
    )
    expected = shift.opening_cents + cash_sales + movement_total
    return {
        "id": shift.id,
        "opened_at": shift.opened_at,
        "closed_at": shift.closed_at,
        "opening_cents": shift.opening_cents,
        "cash_sales_cents": cash_sales,
        "movement_total_cents": movement_total,
        "movements": [
            {
                "id": m.id,
                "kind": m.kind,
                "amount_cents": m.amount_cents,
                "reason": m.reason,
                "created_at": m.created_at,
                "user_id": m.user_id,
            }
            for m in movements
        ],
        "expected_cents": expected,
        "counted_cents": shift.counted_cents,
        "difference_cents": (
            shift.counted_cents - expected if shift.counted_cents is not None else None
        ),
        "notes": shift.notes,
    }


class BusinessService:
    def __init__(self, database: Database):
        self.database = database

    def settings(self) -> dict:
        with self.database.read() as session:
            settings = session.get(BusinessSettings, 1)
            return business_view(settings)

    def save_settings(self, data: BusinessInput, actor: Principal) -> dict:
        check_image(self.database, data.logo_url)
        check_image(self.database, data.cover_url)
        with self.database.write() as session:
            settings = session.get(BusinessSettings, 1)
            for key, value in data.model_dump().items():
                setattr(settings, key, value.strip() if isinstance(value, str) else value)
            record(session, actor.id, "business.updated", 1)
            return business_view(settings)

    def fiscal(self) -> dict:
        with self.database.read() as session:
            profile = session.get(FiscalProfile, 1)
            return (
                {key: getattr(profile, key) for key in FiscalInput.model_fields}
                if profile
                else FiscalInput().model_dump()
            )

    def save_fiscal(self, data: FiscalInput, actor: Principal) -> dict:
        with self.database.write() as session:
            profile = session.get(FiscalProfile, 1) or FiscalProfile(id=1)
            for key, value in data.model_dump().items():
                setattr(profile, key, value.strip())
            session.add(profile)
            record(session, actor.id, "fiscal.updated", 1)
            return data.model_dump()

    @staticmethod
    def _movements(session, shift_id: int) -> list:
        return list(
            session.scalars(
                select(CashMovement)
                .where(CashMovement.shift_id == shift_id)
                .order_by(CashMovement.id)
            )
        )

    def cash_movement(self, shift_id: int, data: CashMovementInput, actor: Principal) -> dict:
        with self.database.write() as session:
            existing = session.scalar(
                select(CashMovement).where(CashMovement.request_key == str(data.request_key))
            )
            if existing:
                if (
                    existing.shift_id != shift_id
                    or existing.user_id != actor.id
                    or existing.kind != data.kind
                    or existing.amount_cents != data.amount_cents
                    or existing.reason != data.reason.strip()
                ):
                    raise BusinessError("Ese intento corresponde a otro movimiento.", 409)
                return {"id": existing.id}
            shift = session.get(CashShift, shift_id)
            if not shift or shift.closed_at is not None:
                raise BusinessError(
                    "La caja está cerrada. No se pueden registrar movimientos.", 409
                )
            balance = shift_view(
                shift, self._cash_sales(session, shift_id), self._movements(session, shift_id)
            )["expected_cents"]
            if data.kind != "deposit" and data.amount_cents > balance:
                raise BusinessError("El movimiento supera el efectivo esperado en caja.", 409)
            movement = CashMovement(
                request_key=str(data.request_key),
                shift_id=shift_id,
                user_id=actor.id,
                kind=data.kind,
                amount_cents=data.amount_cents,
                reason=data.reason.strip(),
                created_at=int(time.time()),
            )
            session.add(movement)
            session.flush()
            record(
                session,
                actor.id,
                "cash.movement",
                movement.id,
                shift_id=shift_id,
                kind=data.kind,
                amount_cents=data.amount_cents,
                reason=data.reason.strip(),
            )
            return {"id": movement.id}

    @staticmethod
    def _cash_sales(session, shift_id: int) -> int:
        return session.scalar(
            select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
                Payment.shift_id == shift_id, Payment.method == "cash"
            )
        )

    def shifts(self) -> dict:
        with self.database.read() as session:
            shifts = list(
                session.scalars(select(CashShift).order_by(CashShift.id.desc()).limit(30))
            )
            views = [
                shift_view(s, self._cash_sales(session, s.id), self._movements(session, s.id))
                for s in shifts
            ]
            return {
                "current": next((s for s in views if s["closed_at"] is None), None),
                "history": [s for s in views if s["closed_at"] is not None],
            }

    def open_shift(self, opening_cents: int, actor: Principal) -> dict:
        with self.database.write() as session:
            if session.scalar(select(CashShift).where(CashShift.closed_at.is_(None))):
                raise BusinessError("Ya hay una caja abierta en este local.", 409)
            shift = CashShift(
                opened_by=actor.id, opened_at=int(time.time()), opening_cents=opening_cents
            )
            session.add(shift)
            session.flush()
            record(session, actor.id, "shift.opened", shift.id, opening_cents=opening_cents)
            return shift_view(shift, 0, [])

    def close_shift(self, shift_id: int, counted: int, notes: str, actor: Principal) -> dict:
        with self.database.write() as session:
            shift = session.get(CashShift, shift_id)
            if not shift or shift.closed_at is not None:
                raise BusinessError("La caja ya está cerrada o no existe.", 409)
            shift.counted_cents = counted
            shift.closed_at = int(time.time())
            shift.closed_by = actor.id
            shift.notes = notes.strip()
            result = shift_view(
                shift, self._cash_sales(session, shift.id), self._movements(session, shift.id)
            )
            record(session, actor.id, "shift.closed", shift.id, **result)
            return result

    def report(self, day: date) -> dict:
        start = datetime.combine(day, datetime.min.time(), tzinfo=COSTA_RICA)
        end = start + timedelta(days=1)
        lower, upper = int(start.timestamp()), int(end.timestamp())
        with self.database.read() as session:
            payments = list(
                session.scalars(
                    select(Payment)
                    .where(Payment.created_at >= lower, Payment.created_at < upper)
                    .order_by(Payment.id)
                )
            )
            by_method = {
                method: sum(p.amount_cents for p in payments if p.method == method)
                for method in ("cash", "card", "sinpe")
            }
            order_ids = [p.order_id for p in payments]
            top = session.execute(
                select(
                    OrderItem.product_name,
                    func.sum(OrderItem.quantity),
                    func.sum(OrderItem.quantity * OrderItem.unit_price_cents),
                )
                .where(OrderItem.order_id.in_(order_ids))
                .group_by(OrderItem.product_name)
                .order_by(func.sum(OrderItem.quantity).desc())
                .limit(5)
            ).all()
            pending = session.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.status.in_(["queued", "preparing", "ready"]))
            )
            return {
                "day": day.isoformat(),
                "total_cents": sum(by_method.values()),
                "orders_paid": len(payments),
                "by_method": by_method,
                "kitchen_pending": pending,
                "top_products": [
                    {"name": name, "quantity": quantity, "total_cents": total}
                    for name, quantity, total in top
                ],
                "sales": [
                    {
                        "order_id": p.order_id,
                        "time": datetime.fromtimestamp(p.created_at, UTC)
                        .astimezone(COSTA_RICA)
                        .isoformat(),
                        "method": p.method,
                        "amount_cents": p.amount_cents,
                        "cashier_id": p.cashier_id,
                    }
                    for p in payments
                ],
            }

    def audit(self) -> list[dict]:
        with self.database.read() as session:
            rows = session.execute(
                select(AuditEvent, User.username)
                .outerjoin(User, User.id == AuditEvent.user_id)
                .order_by(AuditEvent.id.desc())
                .limit(200)
            ).all()
            return [
                {
                    "id": event.id,
                    "username": username or "Autoservicio",
                    "action": event.action,
                    "entity_id": event.entity_id,
                    "created_at": event.created_at,
                    "details": event.details,
                }
                for event, username in rows
            ]
