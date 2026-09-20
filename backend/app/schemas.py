from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.domain import PaymentMethod, PreparationStatus, Role

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Username = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[a-z0-9_.-]{3,40}$")
]
Money = Annotated[int, Field(strict=True, gt=0, le=100_000_000)]
LocalImage = Annotated[str, StringConstraints(pattern=r"^(/api/media/[a-f0-9]{32}\.webp)?$")]
Color = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginInput(InputModel):
    username: Username
    password: str = Field(min_length=1)


class UserInput(InputModel):
    username: Username
    password: str = Field(min_length=1)
    role: Role


class UserUpdate(InputModel):
    role: Role
    active: bool
    password: str | None = Field(default=None, min_length=1)


class CategoryInput(InputModel):
    name: str = Field(min_length=1, max_length=60, pattern=r".*\S.*")
    sort_order: int = Field(default=0, ge=0, le=9999)


class ProductInput(InputModel):
    name: Name
    description: str = Field(default="", max_length=300)
    category_id: int = Field(gt=0)
    price_cents: Money
    available: bool = True
    icon: str = Field(default="🍽️", min_length=1, max_length=8)
    image_url: LocalImage = ""
    featured: bool = False
    sort_order: int = Field(default=0, ge=0, le=9999)
    allergens: str = Field(default="", max_length=300)
    cabys: str = Field(default="", pattern=r"^(\d{13})?$")


class OrderLineInput(InputModel):
    product_id: int = Field(strict=True, gt=0)
    quantity: int = Field(strict=True, ge=1, le=50)


class OrderInput(InputModel):
    service_mode: Literal["dine_in", "takeaway"] = "takeaway"
    table_number: str = Field(default="", max_length=12)
    request_key: UUID
    items: list[OrderLineInput] = Field(min_length=1, max_length=50)
    notes: str = Field(default="", max_length=300)


class PaymentInput(InputModel):
    request_key: UUID
    method: PaymentMethod
    received_cents: Money | None = None
    reference: str = Field(default="", max_length=100)


class StatusInput(InputModel):
    status: PreparationStatus


class CancelInput(InputModel):
    reason: str = Field(min_length=3, max_length=300)


class BusinessInput(InputModel):
    name: Name
    tagline: str = Field(max_length=160)
    sinpe_phone: str = Field(default="", pattern=r"^(\d{8})?$")
    phone: str = Field(default="", max_length=20)
    address: str = Field(default="", max_length=200)
    logo_url: LocalImage = ""
    cover_url: LocalImage = ""
    primary_color: Color = "#184c3b"
    accent_color: Color = "#e99a53"
    background_color: Color = "#f6f7f3"
    surface_color: Color = "#ffffff"
    text_color: Color = "#233b32"
    hero_title: Name = "Tu antojo, recién hecho."
    receipt_footer: str = Field(default="¡Gracias por tu visita!", max_length=200)
    opening_hours: str = Field(default="", max_length=300)
    accepting_orders: bool = True
    closed_message: Name = "En este momento no recibimos pedidos."


class FiscalInput(InputModel):
    legal_name: str = Field(default="", max_length=160)
    identification: str = Field(default="", max_length=20, pattern=r"^[a-zA-Z0-9-]*$")
    activity_code: str = Field(default="", pattern=r"^[0-9]{0,10}$")
    email: str = Field(default="", max_length=160, pattern=r"^([^\s@]+@[^\s@]+\.[^\s@]+)?$")
    branch_code: str = Field(default="001", pattern=r"^\d{3}$")
    terminal_code: str = Field(default="00001", pattern=r"^\d{5}$")


class CashMovementInput(InputModel):
    request_key: UUID
    kind: Literal["deposit", "withdrawal", "expense"]
    amount_cents: Money
    reason: str = Field(min_length=3, max_length=200, pattern=r".*\S.*")


class ShiftOpenInput(InputModel):
    opening_cents: int = Field(strict=True, ge=0, le=100_000_000)


class ShiftCloseInput(InputModel):
    counted_cents: int = Field(strict=True, ge=0, le=100_000_000)
    notes: str = Field(default="", max_length=300)
