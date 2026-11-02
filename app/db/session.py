from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

database_url = settings.database_url
# Render entrega la URL como "postgres://"; SQLAlchemy 2.0 exige "postgresql://".
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

is_sqlite = database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
# pool_pre_ping evita errores por conexiones que el Postgres gratuito cierra por inactividad.
engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=not is_sqlite)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
