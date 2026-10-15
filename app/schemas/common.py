from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict

from app.core.utils import to_naive_utc

# Las fechas con zona horaria se normalizan a UTC sin tzinfo antes de guardarse
UTCDateTime = Annotated[datetime, AfterValidator(to_naive_utc)]

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class Message(BaseModel):
    detail: str
