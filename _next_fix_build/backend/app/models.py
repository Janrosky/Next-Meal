from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "business"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(100), default="Next-Fix")
    phone: Mapped[str] = mapped_column(String(40), default="")
    address: Mapped[str] = mapped_column(String(240), default="")
    currency: Mapped[str] = mapped_column(String(3), default="CRC")
    accent: Mapped[str] = mapped_column(String(7), default="#c8ff45")
    accent_secondary: Mapped[str] = mapped_column(String(7), default="#7c5cff")
    ticket_prefix: Mapped[str] = mapped_column(String(5), default="NF")


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    phone: Mapped[str] = mapped_column(String(40), index=True)
    email: Mapped[str] = mapped_column(String(180), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="customer")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("labor_cents >= 0 AND parts_cents >= 0 AND paid_cents >= 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    brand: Mapped[str] = mapped_column(String(80), default="")
    model: Mapped[str] = mapped_column(String(100), default="")
    serial_number: Mapped[str] = mapped_column(String(100), default="", index=True)
    issue: Mapped[str] = mapped_column(Text)
    diagnosis: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="received", index=True)
    priority: Mapped[str] = mapped_column(String(16), default="normal", index=True)
    assigned_to: Mapped[str] = mapped_column(String(100), default="")
    estimated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    labor_cents: Mapped[int] = mapped_column(Integer, default=0)
    parts_cents: Mapped[int] = mapped_column(Integer, default=0)
    paid_cents: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    customer: Mapped[Customer] = relationship(back_populates="tickets")


class TicketEvent(Base):
    __tablename__ = "ticket_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
