from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.schemas.user import Token, UserRead, UserRegister, UserUpdateMe

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: DbSession):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese email")
    user = User(
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    """Login con formulario OAuth2 (campo `username` = email). Devuelve un JWT Bearer."""
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cuenta desactivada")
    return Token(access_token=create_access_token(user.id, user.role), user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserRead)
def update_me(data: UserUpdateMe, user: CurrentUser, db: DbSession):
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.new_password is not None:
        if not data.current_password or not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La contraseña actual no es correcta")
        user.hashed_password = hash_password(data.new_password)
    db.commit()
    db.refresh(user)
    return user
