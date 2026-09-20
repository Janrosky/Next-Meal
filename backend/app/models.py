from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin', 'cashier', 'kitchen')"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(16))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[int] = mapped_column(Integer)
    user: Mapped[User] = relationship()


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price_cents > 0"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(300), default="")
    price_cents: Mapped[int] = mapped_column(Integer)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    icon: Mapped[str] = mapped_column(String(8), default="🍽️")
    image_url: Mapped[str] = mapped_column(String(100), default="")
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    allergens: Mapped[str] = mapped_column(String(300), default="")
    cabys: Mapped[str] = mapped_column(String(13), default="")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_cents > 0"),
        CheckConstraint("payment_status IN ('unpaid', 'paid')"),
        CheckConstraint(
            "status IN ('awaiting_payment', 'queued', 'preparing', 'ready', "
            "'delivered', 'cancelled')"
        ),
        {"sqlite_autoincrement": True},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    request_key: Mapped[str] = mapped_column(String(36), unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(Integer, index=True)
    updated_at: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="awaiting_payment", index=True)
    payment_status: Mapped[str] = mapped_column(String(16), default="unpaid")
    total_cents: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(String(300), default="")
    service_mode: Mapped[str] = mapped_column(String(16), default="takeaway")
    table_number: Mapped[str] = mapped_column(String(12), default="")
    items: Mapped[list["OrderItem"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="OrderItem.id"
    )
    payment: Mapped["Payment | None"] = relationship(lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0"),
        CheckConstraint("unit_price_cents > 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_cents: Mapped[int] = mapped_column(Integer)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("method IN ('cash', 'card', 'sinpe')"),
        CheckConstraint("received_cents >= amount_cents"),
        CheckConstraint("amount_cents > 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    request_key: Mapped[str] = mapped_column(String(36), unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    shift_id: Mapped[int] = mapped_column(ForeignKey("cash_shifts.id"), index=True)
    cashier_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    method: Mapped[str] = mapped_column(String(12))
    amount_cents: Mapped[int] = mapped_column(Integer)
    received_cents: Mapped[int] = mapped_column(Integer)
    reference: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[int] = mapped_column(Integer, index=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(40))
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[int] = mapped_column(Integer, index=True)


class CashShift(Base):
    __tablename__ = "cash_shifts"
    __table_args__ = (
        CheckConstraint("opening_cents >= 0"),
        CheckConstraint("counted_cents IS NULL OR counted_cents >= 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    opened_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    closed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    opened_at: Mapped[int] = mapped_column(Integer)
    closed_at: Mapped[int | None] = mapped_column(Integer)
    opening_cents: Mapped[int] = mapped_column(Integer)
    counted_cents: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(String(300), default="")


class BusinessSettings(Base):
    __tablename__ = "business_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    tagline: Mapped[str] = mapped_column(String(160))
    sinpe_phone: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(200))
    logo_url: Mapped[str] = mapped_column(String(100), default="")
    cover_url: Mapped[str] = mapped_column(String(100), default="")
    primary_color: Mapped[str] = mapped_column(String(7), default="#184c3b")
    accent_color: Mapped[str] = mapped_column(String(7), default="#e99a53")
    background_color: Mapped[str] = mapped_column(String(7), default="#f6f7f3")
    surface_color: Mapped[str] = mapped_column(String(7), default="#ffffff")
    text_color: Mapped[str] = mapped_column(String(7), default="#233b32")
    hero_title: Mapped[str] = mapped_column(String(100), default="Tu antojo, recién hecho.")
    receipt_footer: Mapped[str] = mapped_column(String(200), default="¡Gracias por tu visita!")
    opening_hours: Mapped[str] = mapped_column(String(300), default="")
    accepting_orders: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_message: Mapped[str] = mapped_column(
        String(200), default="En este momento no recibimos pedidos."
    )


class FiscalProfile(Base):
    __tablename__ = "fiscal_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(160), default="")
    identification: Mapped[str] = mapped_column(String(20), default="")
    activity_code: Mapped[str] = mapped_column(String(10), default="")
    email: Mapped[str] = mapped_column(String(160), default="")
    branch_code: Mapped[str] = mapped_column(String(3), default="001")
    terminal_code: Mapped[str] = mapped_column(String(5), default="00001")


class CashMovement(Base):
    __tablename__ = "cash_movements"
    __table_args__ = (
        CheckConstraint("kind IN ('deposit', 'withdrawal', 'expense')"),
        CheckConstraint("amount_cents > 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    request_key: Mapped[str] = mapped_column(String(36), unique=True)
    shift_id: Mapped[int] = mapped_column(ForeignKey("cash_shifts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(16))
    amount_cents: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[int] = mapped_column(Integer)
