from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import OrderStatus
from app.schemas.common import ORMModel


class OrderItemCreate(BaseModel):
    ticket_type_id: int
    quantity: int = Field(gt=0, le=50)


class OrderCreate(BaseModel):
    festival_id: int
    items: list[OrderItemCreate] = Field(min_length=1)
    discount_code: str | None = None


class OrderPay(BaseModel):
    """Pago simulado. En producción esto lo sustituiría una pasarela (Stripe, Redsys...)."""

    payment_method: Literal["card", "paypal", "bizum"] = "card"
    card_number: str | None = Field(default=None, pattern=r"^\d{12,19}$")


class OrderItemRead(ORMModel):
    id: int
    ticket_type_id: int
    ticket_type_name: str
    quantity: int
    unit_price: Decimal


class OrderRead(ORMModel):
    id: int
    user_id: int
    festival_id: int
    festival_name: str
    status: OrderStatus
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    payment_method: str | None
    payment_reference: str | None
    created_at: datetime
    expires_at: datetime
    paid_at: datetime | None
    items: list[OrderItemRead]
