from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import Municipality, enum_column


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    address: Mapped[str] = mapped_column(String(255))
    municipality: Mapped[Municipality] = mapped_column(enum_column(Municipality), index=True)
    capacity: Mapped[int]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
