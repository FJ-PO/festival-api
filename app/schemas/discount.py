from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel, UTCDateTime


class DiscountCodeCreate(BaseModel):
    code: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    percent_off: int = Field(ge=1, le=100)
    max_uses: int | None = Field(default=None, gt=0)
    valid_until: UTCDateTime | None = None

    @field_validator("code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()


class DiscountCodeUpdate(BaseModel):
    percent_off: int | None = Field(default=None, ge=1, le=100)
    max_uses: int | None = Field(default=None, gt=0)
    valid_until: UTCDateTime | None = None
    is_active: bool | None = None


class DiscountCodeRead(ORMModel):
    id: int
    festival_id: int
    code: str
    percent_off: int
    max_uses: int | None
    times_used: int
    valid_until: UTCDateTime | None
    is_active: bool
