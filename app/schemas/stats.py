from decimal import Decimal

from pydantic import BaseModel


class TicketTypeStats(BaseModel):
    ticket_type_id: int
    name: str
    price: Decimal
    quantity_total: int
    quantity_sold: int
    quantity_available: int


class FestivalStats(BaseModel):
    festival_id: int
    festival_name: str
    revenue: Decimal
    orders_by_status: dict[str, int]
    tickets_issued: int
    tickets_checked_in: int
    attendance_rate: float
    ticket_types: list[TicketTypeStats]
