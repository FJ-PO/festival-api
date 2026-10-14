from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.session import Base
from app.models.discount import DiscountCode
from app.models.enums import OrderStatus, enum_column
from app.models.festival import Festival
from app.models.ticket_type import TicketType
from app.models.user import User


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    festival_id: Mapped[int] = mapped_column(ForeignKey("festivals.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(enum_column(OrderStatus), default=OrderStatus.PENDING, index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_code_id: Mapped[int | None] = mapped_column(ForeignKey("discount_codes.id"))
    payment_method: Mapped[str | None] = mapped_column(String(30))
    payment_reference: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    expires_at: Mapped[datetime]
    paid_at: Mapped[datetime | None]

    user: Mapped[User] = relationship()
    festival: Mapped[Festival] = relationship()
    discount_code: Mapped[DiscountCode | None] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="order")  # noqa: F821

    @property
    def festival_name(self) -> str:
        return self.festival.name


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    ticket_type_id: Mapped[int] = mapped_column(ForeignKey("ticket_types.id"))
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="items")
    ticket_type: Mapped[TicketType] = relationship()

    @property
    def ticket_type_name(self) -> str:
        return self.ticket_type.name
