from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.domain import PaymentMethod, PreparationStatus, Role

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Username = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[a-z0-9_.-]{3,40}$")
]
Money = Annotated[int, Field(strict=True, gt=0, le=100_000_000)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginInput(InputModel):
    username: Username
    password: str = Field(min_length=1, max_length=128)


class UserInput(InputModel):
    username: Username
    password: str = Field(min_length=10, max_length=128)
    role: Role


class UserUpdate(InputModel):
    role: Role
    active: bool
    password: str | None = Field(default=None, min_length=10, max_length=128)


class CategoryInput(InputModel):
    name: str = Field(min_length=1, max_length=60, pattern=r".*\S.*")


class ProductInput(InputModel):
    name: Name
    description: str = Field(default="", max_length=300)
    category_id: int = Field(gt=0)
    price_cents: Money
    available: bool = True
    icon: str = Field(default="🍽️", min_length=1, max_length=8)


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


class ShiftOpenInput(InputModel):
    opening_cents: int = Field(strict=True, ge=0, le=100_000_000)


class ShiftCloseInput(InputModel):
    counted_cents: int = Field(strict=True, ge=0, le=100_000_000)
    notes: str = Field(default="", max_length=300)
