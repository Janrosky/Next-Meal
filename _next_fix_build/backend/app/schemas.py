from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TicketStatus = Literal["received", "diagnosing", "approval", "repairing", "ready", "delivered"]
Priority = Literal["low", "normal", "high", "urgent"]


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=4, max_length=40)
    email: str = Field(default="", max_length=180)
    notes: str = Field(default="", max_length=2000)


class CustomerRead(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class TicketCreate(BaseModel):
    customer_id: int
    asset_type: str = Field(min_length=2, max_length=50)
    brand: str = Field(default="", max_length=80)
    model: str = Field(default="", max_length=100)
    serial_number: str = Field(default="", max_length=100)
    issue: str = Field(min_length=3, max_length=5000)
    priority: Priority = "normal"
    assigned_to: str = Field(default="", max_length=100)
    estimated_at: datetime | None = None
    labor_cents: int = Field(default=0, ge=0)
    parts_cents: int = Field(default=0, ge=0)
    notes: str = Field(default="", max_length=5000)


class TicketUpdate(BaseModel):
    diagnosis: str | None = Field(default=None, max_length=5000)
    priority: Priority | None = None
    assigned_to: str | None = Field(default=None, max_length=100)
    estimated_at: datetime | None = None
    labor_cents: int | None = Field(default=None, ge=0)
    parts_cents: int | None = Field(default=None, ge=0)
    paid_cents: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=5000)


class StatusUpdate(BaseModel):
    status: TicketStatus


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    customer_id: int
    customer_name: str
    customer_phone: str
    asset_type: str
    brand: str
    model: str
    serial_number: str
    issue: str
    diagnosis: str
    status: TicketStatus
    priority: Priority
    assigned_to: str
    estimated_at: datetime | None
    labor_cents: int
    parts_cents: int
    paid_cents: int
    notes: str
    created_at: datetime
    updated_at: datetime


class BusinessUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=240)
    currency: str = Field(default="CRC", min_length=3, max_length=3)
    accent: str = "#c8ff45"
    accent_secondary: str = "#7c5cff"
    ticket_prefix: str = Field(default="NF", min_length=1, max_length=5)

    @field_validator("accent", "accent_secondary")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if len(value) != 7 or not value.startswith("#"):
            raise ValueError("El color debe estar en formato hexadecimal.")
        int(value[1:], 16)
        return value.lower()
