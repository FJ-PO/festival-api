import secrets
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.session import Base
from app.models.enums import TicketStatus, enum_column
from app.models.festival import Festival
from app.models.order import Order
from app.models.ticket_type import TicketType
from app.models.user import User


def generate_ticket_code() -> str:
    """Código único e impredecible que se codifica en el QR de la entrada."""
    return secrets.token_hex(12).upper()


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=generate_ticket_code)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    ticket_type_id: Mapped[int] = mapped_column(ForeignKey("ticket_types.id"))
    festival_id: Mapped[int] = mapped_column(ForeignKey("festivals.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    attendee_name: Mapped[str] = mapped_column(String(150))
    status: Mapped[TicketStatus] = mapped_column(enum_column(TicketStatus), default=TicketStatus.VALID)
    issued_at: Mapped[datetime] = mapped_column(default=utcnow)
    checked_in_at: Mapped[datetime | None]
    checked_in_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    order: Mapped[Order] = relationship(back_populates="tickets")
    ticket_type: Mapped[TicketType] = relationship()
    festival: Mapped[Festival] = relationship()
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])

    @property
    def festival_name(self) -> str:
        return self.festival.name

    @property
    def festival_start_date(self):
        return self.festival.start_date

    @property
    def venue_name(self) -> str:
        return self.festival.venue.name

    @property
    def ticket_type_name(self) -> str:
        return self.ticket_type.name
