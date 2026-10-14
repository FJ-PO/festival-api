from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import ContentStatus
from app.schemas.common import ORMModel
from app.schemas.user import UserBrief

# ---------- Ajustes del sitio ----------


class SocialLinks(BaseModel):
    instagram: str | None = None
    facebook: str | None = None
    x: str | None = None
    youtube: str | None = None
    tiktok: str | None = None
    spotify: str | None = None


class SiteSettings(BaseModel):
    """Todo lo que el administrador puede cambiar de la web pública sin tocar código."""

    site_name: str = Field(default="Las Palomas Festival", max_length=100)
    tagline: str = Field(default="Música y humor en la Plaza de Toros de Algeciras", max_length=200)
    hero_kicker: str = Field(default="Algeciras · Verano 2027", max_length=80)
    hero_title: str = Field(default="Un sábado. Una estrella. Todo el verano.", max_length=200)
    hero_subtitle: str = Field(
        default="Cada sábado de mayo a agosto, los grandes nombres de la música y el humor en la Plaza de Toros de Algeciras.",
        max_length=400,
    )
    hero_image_url: str | None = Field(default=None, max_length=500)
    hero_cta_text: str = Field(default="Ver programación", max_length=60)
    hero_cta_link: str = Field(default="/programacion", max_length=300)
    featured_festival_id: int | None = None
    announcement: str | None = Field(
        default="Nuevas confirmaciones muy pronto · Entradas ya a la venta", max_length=200,
        description="Banda superior de aviso",
    )
    about_title: str = Field(default="Sobre nosotros", max_length=120)
    about_text: str = Field(
        default=(
            "Las Palomas Festival convierte la Plaza de Toros de Algeciras en el gran escenario del verano "
            "en el Campo de Gibraltar: pop, flamenco, música urbana y humor, una noche cada semana."
        ),
        max_length=4000,
    )
    contact_email: str | None = Field(default="info@laspalomasfestival.es", max_length=200)
    contact_phone: str | None = Field(default=None, max_length=50)
    accent_color: str = Field(default="#ff3366", pattern=r"^#[0-9a-fA-F]{6}$")
    social: SocialLinks = SocialLinks()
    footer_text: str = Field(default="© Las Palomas Festival · Algeciras", max_length=300)


class SiteSettingsRead(SiteSettings):
    updated_at: datetime | None = None


# ---------- Páginas y noticias ----------


class ContentBase(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(default=None, max_length=220, pattern=r"^[a-z0-9-]*$",
                             description="Si se omite se genera a partir del título")
    excerpt: str | None = Field(default=None, max_length=500)
    content: str = ""
    cover_image_url: str | None = Field(default=None, max_length=500)
    status: ContentStatus = ContentStatus.DRAFT


class ContentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, max_length=220, pattern=r"^[a-z0-9-]*$")
    excerpt: str | None = Field(default=None, max_length=500)
    content: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    status: ContentStatus | None = None


class ContentRead(ORMModel):
    id: int
    title: str
    slug: str
    excerpt: str | None
    content: str
    cover_image_url: str | None
    status: ContentStatus
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    author: UserBrief | None


class PageCreate(ContentBase):
    show_in_menu: bool = False
    menu_order: int = 0


class PageUpdate(ContentUpdate):
    show_in_menu: bool | None = None
    menu_order: int | None = None


class PageRead(ContentRead):
    show_in_menu: bool
    menu_order: int


class PostCreate(ContentBase):
    festival_id: int | None = None


class PostUpdate(ContentUpdate):
    festival_id: int | None = None


class PostRead(ContentRead):
    festival_id: int | None


# ---------- Medios ----------


class MediaRead(ORMModel):
    id: int
    url: str
    filename: str
    original_name: str
    content_type: str
    size: int
    alt: str | None
    created_at: datetime


class MediaUpdate(BaseModel):
    alt: str | None = Field(default=None, max_length=255)


# ---------- Dashboard ----------


class RecentOrder(BaseModel):
    id: int
    festival_name: str
    customer: str
    total: Decimal
    status: str
    created_at: datetime


class SalesPoint(BaseModel):
    day: str
    revenue: Decimal
    orders: int


class Dashboard(BaseModel):
    festivals_by_status: dict[str, int]
    users_by_role: dict[str, int]
    revenue: Decimal
    orders_paid: int
    tickets_sold: int
    tickets_checked_in: int
    artists: int
    venues: int
    pages: int
    posts: int
    sales_last_30_days: list[SalesPoint]
    recent_orders: list[RecentOrder]


# ---------- Newsletter ----------


class SubscriberCreate(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=150)


class SubscriberRead(ORMModel):
    id: int
    email: str
    name: str | None
    created_at: datetime
