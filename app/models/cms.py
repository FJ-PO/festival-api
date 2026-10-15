"""Contenido editable desde el panel de administración (estilo CMS)."""

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.session import Base
from app.models.enums import ContentStatus, enum_column
from app.models.user import User


class SiteConfig(Base):
    """Fila única (id=1) con los ajustes globales de la web: portada, textos, redes, colores..."""

    __tablename__ = "site_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)


class ContentMixin:
    """Campos comunes a páginas y noticias. El cuerpo se guarda en Markdown."""

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    excerpt: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, default="")
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ContentStatus] = mapped_column(enum_column(ContentStatus), default=ContentStatus.DRAFT, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    published_at: Mapped[datetime | None]


class Page(ContentMixin, Base):
    """Página estática: "Información", "Cómo llegar", "Preguntas frecuentes"..."""

    __tablename__ = "pages"

    show_in_menu: Mapped[bool] = mapped_column(default=False)
    menu_order: Mapped[int] = mapped_column(default=0)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    author: Mapped[User | None] = relationship()


class Post(ContentMixin, Base):
    """Noticia del blog, opcionalmente vinculada a un festival."""

    __tablename__ = "posts"

    festival_id: Mapped[int | None] = mapped_column(ForeignKey("festivals.id"), index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    author: Mapped[User | None] = relationship()


class Media(Base):
    """Archivo subido a la biblioteca de medios."""

    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True)
    original_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int]
    alt: Mapped[str | None] = mapped_column(String(255))
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    @property
    def url(self) -> str:
        return f"/uploads/{self.filename}"


class Subscriber(Base):
    """Suscripción a la newsletter desde la web pública."""

    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
