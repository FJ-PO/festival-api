"""Tareas de arranque: ajustes de esquema en BD existentes y creación del administrador inicial."""

from sqlalchemy import Engine, inspect, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserRole


def upgrade_schema(engine: Engine) -> None:
    """`create_all` no añade columnas a tablas que ya existen; las nuevas se añaden aquí.

    Sustituye a una migración de Alembic mientras el proyecto use SQLite en desarrollo.
    """
    columns = {c["name"] for c in inspect(engine).get_columns("users")}
    if "username" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(50)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
    if "github_id" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN github_id BIGINT"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_github_id ON users (github_id)"))


def ensure_admin(db: Session) -> User:
    """Crea el administrador de `ADMIN_USERNAME` si no existe. No toca la contraseña de uno existente."""
    admin = db.scalar(select(User).where(User.username == settings.admin_username))
    if admin is None:
        admin = User(
            username=settings.admin_username,
            email=settings.admin_email.lower(),
            full_name="Administrador",
            role=UserRole.ADMIN,
            hashed_password=hash_password(settings.admin_password),
        )
        db.add(admin)
        db.commit()
    return admin
