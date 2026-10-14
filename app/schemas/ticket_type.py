from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel, UTCDateTime


class TicketTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantity_total: int = Field(gt=0)
    max_per_order: int = Field(default=10, gt=0, le=50)
    sale_start: UTCDateTime | None = None
    sale_end: UTCDateTime | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def check_window(self):
        if self.sale_start and self.sale_end and self.sale_end <= self.sale_start:
            raise ValueError("sale_end debe ser posterior a sale_start")
        return self


class TicketTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    quantity_total: int | None = Field(default=None, gt=0)
    max_per_order: int | None = Field(default=None, gt=0, le=50)
    sale_start: UTCDateTime | None = None
    sale_end: UTCDateTime | None = None
    is_active: bool | None = None


class TicketTypeRead(ORMModel):
    id: int
    festival_id: int
    name: str
    description: str | None
    price: Decimal
    quantity_total: int
    quantity_sold: int
    quantity_available: int
    max_per_order: int
    sale_start: UTCDateTime | None
    sale_end: UTCDateTime | None
    is_active: bool
