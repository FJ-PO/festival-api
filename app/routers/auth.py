from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.schemas.user import (
    AuthProviders,
    GithubCallback,
    Token,
    UserRead,
    UserRegister,
    UserUpdateMe,
)
from app.services import github as github_service

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
    """Login con formulario OAuth2 (campo `username` = email o nombre de usuario). Devuelve un JWT Bearer.

    No se crea ninguna cookie ni sesión: el cliente guarda el token y lo envía en `Authorization: Bearer <token>`.
    """
    identifier = form.username.strip()
    user = db.scalar(select(User).where(or_(User.email == identifier.lower(), User.username == identifier)))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cuenta desactivada")
    return _token_for(user)


@router.post("/refresh", response_model=Token)
def refresh(user: CurrentUser):
    """Renovación deslizante: con un JWT todavía válido devuelve otro nuevo, con el rol actual del usuario.

    Un token caducado o de una cuenta desactivada no se puede renovar (401): hay que volver a iniciar sesión.
    """
    return _token_for(user)


def _token_for(user: User) -> Token:
    return Token(
        access_token=create_access_token(user.id, user.role),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )


@router.get("/providers", response_model=AuthProviders)
def providers():
    """Métodos de inicio de sesión externos activos. El frontend muestra el botón de GitHub solo si está `true`."""
    return AuthProviders(github=settings.github_enabled)


@router.get("/github/authorize")
def github_authorize(
    redirect_uri: Annotated[str, Query(max_length=512)],
    state: Annotated[str, Query(min_length=8, max_length=256)],
):
    """Devuelve la URL de GitHub a la que redirigir al usuario.

    El `state` lo genera y guarda el navegador para comprobarlo al volver (protección CSRF del flujo OAuth2).
    """
    if not settings.github_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El inicio de sesión con GitHub no está disponible")
    return {"url": github_service.build_authorize_url(redirect_uri, state)}


@router.post("/github", response_model=Token)
def github_login(data: GithubCallback, db: DbSession):
    """Completa el login/registro con GitHub: canjea el `code` y devuelve el JWT propio del proyecto.

    Igual que el login normal, no crea cookies ni sesiones: el cliente guarda el token y lo envía en
    `Authorization: Bearer`. Si el email de GitHub ya tiene cuenta local, se vincula; si no, se crea una nueva.
    """
    if not settings.github_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El inicio de sesión con GitHub no está disponible")

    profile = github_service.fetch_profile(data.code, data.redirect_uri)

    user = db.scalar(select(User).where(User.github_id == profile.github_id))
    if user is None:
        # Sin cuenta vinculada: se enlaza con la cuenta local de ese email o se crea una nueva.
        user = db.scalar(select(User).where(User.email == profile.email))
        if user is None:
            user = User(
                email=profile.email,
                full_name=profile.full_name,
                hashed_password="",
                github_id=profile.github_id,
                role=UserRole.CUSTOMER,
            )
            db.add(user)
        else:
            user.github_id = profile.github_id
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cuenta desactivada")
    return _token_for(user)


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
