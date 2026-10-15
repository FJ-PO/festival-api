from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.utils import slugify
from app.models import SiteConfig
from app.schemas.cms import SiteSettings, SiteSettingsRead


def unique_slug_for(db: Session, model, text: str, exclude_id: int | None = None) -> str:
    """Slug único dentro de la tabla de `model` (páginas, noticias...)."""
    base = slugify(text)
    slug, n = base, 2
    while True:
        existing = db.scalar(select(model.id).where(model.slug == slug))
        if existing is None or existing == exclude_id:
            return slug
        slug = f"{base}-{n}"
        n += 1


def get_site_config(db: Session) -> SiteConfig:
    config = db.get(SiteConfig, 1)
    if config is None:
        config = SiteConfig(id=1, data=SiteSettings().model_dump())
        db.add(config)
        db.commit()
    return config


def read_site_settings(db: Session) -> SiteSettingsRead:
    config = get_site_config(db)
    # Los valores guardados se mezclan con los por defecto, así los campos nuevos siempre tienen valor
    return SiteSettingsRead(**{**SiteSettings().model_dump(), **config.data}, updated_at=config.updated_at)
