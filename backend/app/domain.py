from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    CASHIER = "cashier"
    KITCHEN = "kitchen"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    SINPE = "sinpe"


class PreparationStatus(StrEnum):
    AWAITING_PAYMENT = "awaiting_payment"
    QUEUED = "queued"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


NEXT_STATUS = {
    PreparationStatus.QUEUED: PreparationStatus.PREPARING,
    PreparationStatus.PREPARING: PreparationStatus.READY,
    PreparationStatus.READY: PreparationStatus.DELIVERED,
}


@dataclass(frozen=True)
class Principal:
    id: int
    username: str
    role: Role


class BusinessError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
