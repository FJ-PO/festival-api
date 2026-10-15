from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.core.deps import AdminUser, DbSession
from app.models import User, UserRole
from app.schemas.common import Page
from app.core.security import hash_password
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserRead

router = APIRouter(prefix="/users", tags=["Usuarios (admin)"])


@router.get("", response_model=Page[UserRead])
def list_users(
    db: DbSession,
    _: AdminUser,
    role: UserRole | None = None,
    q: Annotated[str | None, Query(description="Busca por email o nombre")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like), User.username.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(User.id).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserAdminCreate, db: DbSession, _: AdminUser):
    """Alta de usuarios desde el panel (organizadores, personal de puerta, otros administradores...)."""
    email = data.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese email")
    if data.username and db.scalar(select(User.id).where(User.username == data.username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese nombre de usuario ya está en uso")
    user = User(
        email=email,
        username=data.username,
        full_name=data.full_name,
        role=data.role,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, data: UserAdminUpdate, db: DbSession, admin: AdminUser):
    """Cambia el rol de un usuario (p. ej. hacerlo organizador o staff) o lo activa/desactiva."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes modificar tu propia cuenta de admin")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
