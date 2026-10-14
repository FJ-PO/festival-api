from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import FestivalStatus
from app.schemas.artist import ArtistRead
from app.schemas.common import ORMModel, UTCDateTime
from app.schemas.user import UserBrief
from app.schemas.venue import VenueRead


class FestivalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    genre: str | None = Field(default=None, max_length=80)
    start_date: date
    end_date: date
    image_url: str | None = Field(default=None, max_length=500)
    min_age: int = Field(default=0, ge=0, le=99)
    venue_id: int

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date no puede ser anterior a start_date")
        return self


class FestivalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    genre: str | None = Field(default=None, max_length=80)
    start_date: date | None = None
    end_date: date | None = None
    image_url: str | None = Field(default=None, max_length=500)
    min_age: int | None = Field(default=None, ge=0, le=99)
    venue_id: int | None = None


class FestivalRead(ORMModel):
    id: int
    name: str
    slug: str
    description: str | None
    genre: str | None
    start_date: date
    end_date: date
    image_url: str | None
    min_age: int
    status: FestivalStatus
    venue: VenueRead
    organizer: UserBrief
    created_at: datetime


class PerformanceCreate(BaseModel):
    artist_id: int
    stage: str = Field(min_length=1, max_length=100)
    start_time: UTCDateTime
    end_time: UTCDateTime

    @model_validator(mode="after")
    def check_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time debe ser posterior a start_time")
        return self


class PerformanceRead(ORMModel):
    id: int
    festival_id: int
    stage: str
    start_time: datetime
    end_time: datetime
    artist: ArtistRead


class FestivalDetail(FestivalRead):
    performances: list[PerformanceRead]
