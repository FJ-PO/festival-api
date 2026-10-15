"""Contenido editable de la web: ajustes del sitio, páginas y noticias."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.core.deps import AdminUser, DbSession, OptionalUser
from app.core.utils import utcnow
from app.models import ContentStatus, Festival, Page, Post, UserRole
from app.schemas.cms import (
    PageCreate,
    PageRead,
    PageUpdate,
    PostCreate,
    PostRead,
    PostUpdate,
    SiteSettings,
    SiteSettingsRead,
)
from app.schemas.common import Page as PageOf
from app.services.cms import get_site_config, read_site_settings, unique_slug_for

# ---------- Ajustes del sitio ----------

site_router = APIRouter(prefix="/site", tags=["CMS · Ajustes del sitio"])


@site_router.get("", response_model=SiteSettingsRead)
def get_site_settings(db: DbSession):
    """Ajustes públicos de la web (portada, textos, redes sociales...)."""
    return read_site_settings(db)


@site_router.put("", response_model=SiteSettingsRead)
def update_site_settings(data: SiteSettings, db: DbSession, _: AdminUser):
    if data.featured_festival_id is not None and db.get(Festival, data.featured_festival_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Festival destacado no encontrado")
    config = get_site_config(db)
    config.data = data.model_dump()
    db.commit()
    return read_site_settings(db)


# ---------- Páginas y noticias ----------


def build_content_router(model, prefix: str, tag: str, label: str, schemas: dict) -> APIRouter:
    """Crea el CRUD de un tipo de contenido. Lectura pública de lo publicado; edición solo admin."""
    create_schema, update_schema, read_schema = schemas["create"], schemas["update"], schemas["read"]
    router = APIRouter(prefix=prefix, tags=[tag])
    not_found = f"{label} no encontrada"
    is_page = model is Page

    def _get(db, item_id: int):
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, not_found)
        return item

    def _apply(db, item, changes: dict) -> None:
        if "festival_id" in changes and changes["festival_id"] is not None:
            if db.get(Festival, changes["festival_id"]) is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Festival no encontrado")
        slug = changes.pop("slug", None)
        for field, value in changes.items():
            setattr(item, field, value)
        if slug or "title" in changes or not item.slug:
            item.slug = unique_slug_for(db, model, slug or item.title, exclude_id=item.id)
        if item.status == ContentStatus.PUBLISHED and item.published_at is None:
            item.published_at = utcnow()

    @router.get("", response_model=PageOf[read_schema])
    def list_published(
        db: DbSession,
        menu: Annotated[bool, Query(description="Solo las que aparecen en el menú")] = False,
        festival_id: int | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        stmt = select(model).where(model.status == ContentStatus.PUBLISHED)
        if is_page:
            if menu:
                stmt = stmt.where(model.show_in_menu.is_(True))
            order = (model.menu_order, model.title)
        else:
            if festival_id:
                stmt = stmt.where(model.festival_id == festival_id)
            order = (model.published_at.desc(),)
        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        items = db.scalars(stmt.order_by(*order).limit(limit).offset(offset)).all()
        return PageOf(items=items, total=total, limit=limit, offset=offset)

    @router.get("/manage", response_model=PageOf[read_schema])
    def list_all(
        db: DbSession,
        _: AdminUser,
        status_filter: Annotated[ContentStatus | None, Query(alias="status")] = None,
        q: str | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        """Listado para el panel: borradores y publicadas."""
        stmt = select(model)
        if status_filter:
            stmt = stmt.where(model.status == status_filter)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(model.title.ilike(like), model.content.ilike(like)))
        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        items = db.scalars(stmt.order_by(model.updated_at.desc()).limit(limit).offset(offset)).all()
        return PageOf(items=items, total=total, limit=limit, offset=offset)

    @router.get("/slug/{slug}", response_model=read_schema)
    def get_by_slug(slug: str, db: DbSession, user: OptionalUser):
        """Los borradores solo los ve el administrador (para previsualizarlos)."""
        item = db.scalar(select(model).where(model.slug == slug))
        if item is None or (
            item.status != ContentStatus.PUBLISHED and (user is None or user.role != UserRole.ADMIN)
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, not_found)
        return item

    @router.get("/{item_id}", response_model=read_schema)
    def get_one(item_id: int, db: DbSession, _: AdminUser):
        return _get(db, item_id)

    @router.post("", response_model=read_schema, status_code=status.HTTP_201_CREATED)
    def create(data: create_schema, db: DbSession, admin: AdminUser):
        item = model(author_id=admin.id, slug="")
        _apply(db, item, data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.patch("/{item_id}", response_model=read_schema)
    def update(item_id: int, data: update_schema, db: DbSession, _: AdminUser):
        item = _get(db, item_id)
        _apply(db, item, data.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete(item_id: int, db: DbSession, _: AdminUser):
        db.delete(_get(db, item_id))
        db.commit()

    return router


pages_router = build_content_router(
    Page, "/pages", "CMS · Páginas", "Página",
    {"create": PageCreate, "update": PageUpdate, "read": PageRead},
)
posts_router = build_content_router(
    Post, "/posts", "CMS · Noticias", "Noticia",
    {"create": PostCreate, "update": PostUpdate, "read": PostRead},
)
