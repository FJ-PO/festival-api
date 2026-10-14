from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DiscountCode(Base):
    __tablename__ = "discount_codes"
    __table_args__ = (UniqueConstraint("festival_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    festival_id: Mapped[int] = mapped_column(ForeignKey("festivals.id"), index=True)
    code: Mapped[str] = mapped_column(String(40))
    percent_off: Mapped[int]
    max_uses: Mapped[int | None]
    times_used: Mapped[int] = mapped_column(default=0)
    valid_until: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(default=True)
