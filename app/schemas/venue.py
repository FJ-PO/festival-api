from pydantic import BaseModel, Field

from app.models.enums import Municipality
from app.schemas.common import ORMModel


class VenueBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    address: str = Field(max_length=255)
    municipality: Municipality
    capacity: int = Field(gt=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class VenueCreate(VenueBase):
    pass


class VenueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address: str | None = Field(default=None, max_length=255)
    municipality: Municipality | None = None
    capacity: int | None = Field(default=None, gt=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class VenueRead(VenueBase, ORMModel):
    id: int
