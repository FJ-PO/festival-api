from datetime import date, datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.session import Base
from app.models.artist import Artist
from app.models.enums import FestivalStatus, enum_column
from app.models.user import User
from app.models.venue import Venue


class Festival(Base):
    __tablename__ = "festivals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(80), index=True)
    start_date: Mapped[date] = mapped_column(index=True)
    end_date: Mapped[date]
    image_url: Mapped[str | None] = mapped_column(String(500))
    min_age: Mapped[int] = mapped_column(default=0)
    status: Mapped[FestivalStatus] = mapped_column(enum_column(FestivalStatus), default=FestivalStatus.DRAFT)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    venue: Mapped[Venue] = relationship()
    organizer: Mapped[User] = relationship()
    performances: Mapped[list["Performance"]] = relationship(
        back_populates="festival", cascade="all, delete-orphan", order_by="Performance.start_time"
    )
    ticket_types: Mapped[list["TicketType"]] = relationship(  # noqa: F821
        back_populates="festival", cascade="all, delete-orphan"
    )

    @property
    def price_from(self):
        """Precio más barato entre los tipos de entrada activos (para "desde X €" en el front)."""
        prices = [tt.price for tt in self.ticket_types if tt.is_active]
        return min(prices) if prices else None


class Performance(Base):
    """Actuación de un artista dentro del cartel de un festival."""

    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(primary_key=True)
    festival_id: Mapped[int] = mapped_column(ForeignKey("festivals.id"), index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"))
    stage: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]

    festival: Mapped[Festival] = relationship(back_populates="performances")
    artist: Mapped[Artist] = relationship()
