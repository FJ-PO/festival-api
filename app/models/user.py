from datetime import datetime

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utcnow
from app.db.session import Base
from app.models.enums import UserRole, enum_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Nombre de usuario opcional para iniciar sesión sin email (p. ej. "admin")
    username: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    # Cadena vacía en las cuentas creadas con un proveedor externo (GitHub): no tienen contraseña local.
    hashed_password: Mapped[str] = mapped_column(String(255), default="")
    # Identificador numérico de la cuenta de GitHub vinculada (login con OAuth2), si la hay.
    github_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, default=None)
    role: Mapped[UserRole] = mapped_column(enum_column(UserRole), default=UserRole.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
