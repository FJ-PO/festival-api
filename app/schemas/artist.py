from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ArtistBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    genre: str | None = Field(default=None, max_length=80)
    country: str | None = Field(default=None, max_length=100)
    bio: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class ArtistCreate(ArtistBase):
    pass


class ArtistUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    genre: str | None = Field(default=None, max_length=80)
    country: str | None = Field(default=None, max_length=100)
    bio: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class ArtistRead(ArtistBase, ORMModel):
    id: int
