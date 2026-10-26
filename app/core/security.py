from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    # Las cuentas creadas con un proveedor externo (GitHub) no tienen hash: no se puede entrar con contraseña.
    if not hashed:
        return False
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(subject: str | int, role: str) -> str:
    """JWT firmado (HS256). Viaja siempre en la cabecera `Authorization: Bearer`; nunca en cookies."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "role": role, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
