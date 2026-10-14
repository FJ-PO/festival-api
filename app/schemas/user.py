from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=72)


class UserUpdateMe(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=72)


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(ORMModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserBrief(ORMModel):
    id: int
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
