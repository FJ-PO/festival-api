from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Festival, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def _user_from_token(db: Session, token: str) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_error
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return _user_from_token(db, token)


def get_optional_user(
    db: DbSession, token: Annotated[str | None, Depends(optional_oauth2_scheme)]
) -> User | None:
    return _user_from_token(db, token) if token else None


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_roles(*roles: UserRole):
    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permisos para esta acción")
        return user

    return checker


AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
ManagerUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.ORGANIZER))]
GateUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.ORGANIZER, UserRole.STAFF))]


def can_manage_festival(user: User | None, festival: Festival) -> bool:
    if user is None:
        return False
    return user.role == UserRole.ADMIN or (
        user.role == UserRole.ORGANIZER and festival.organizer_id == user.id
    )


def get_managed_festival(db: Session, festival_id: int, user: User) -> Festival:
    """Devuelve el festival si el usuario puede gestionarlo (admin u organizador propietario)."""
    festival = db.get(Festival, festival_id)
    if festival is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Festival no encontrado")
    if not can_manage_festival(user, festival):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No puedes gestionar este festival")
    return festival
