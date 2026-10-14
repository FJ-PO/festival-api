from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import TicketStatus
from app.schemas.common import ORMModel


class TicketRead(ORMModel):
    id: int
    code: str
    order_id: int
    festival_id: int
    festival_name: str
    festival_start_date: date
    ticket_type_id: int
    ticket_type_name: str
    owner_id: int
    attendee_name: str
    status: TicketStatus
    issued_at: datetime
    checked_in_at: datetime | None


class TicketUpdate(BaseModel):
    attendee_name: str = Field(min_length=2, max_length=150)


class TicketTransfer(BaseModel):
    email: EmailStr
    attendee_name: str | None = Field(default=None, min_length=2, max_length=150)


class CheckInRequest(BaseModel):
    code: str = Field(min_length=4, max_length=32)
    festival_id: int | None = Field(default=None, description="Festival en cuya puerta se escanea")


CheckInReason = Literal["ok", "not_found", "already_used", "cancelled", "wrong_festival"]


class CheckInResult(BaseModel):
    accepted: bool
    reason: CheckInReason
    message: str
    ticket: TicketRead | None = None
