from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.festival import Festival


class TicketType(Base):
    """Tipo de entrada: abono general, VIP, entrada de día, etc."""

    __tablename__ = "ticket_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    festival_id: Mapped[int] = mapped_column(ForeignKey("festivals.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity_total: Mapped[int]
    quantity_sold: Mapped[int] = mapped_column(default=0)
    max_per_order: Mapped[int] = mapped_column(default=10)
    sale_start: Mapped[datetime | None]
    sale_end: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(default=True)

    festival: Mapped[Festival] = relationship(back_populates="ticket_types")

    @property
    def quantity_available(self) -> int:
        return max(self.quantity_total - self.quantity_sold, 0)
