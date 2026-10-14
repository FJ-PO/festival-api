from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.utils import slugify
from app.models import Festival, FestivalStatus, Order, OrderStatus
from app.services.orders import release_discount, release_stock, refund_order


def unique_slug(db: Session, name: str, exclude_id: int | None = None) -> str:
    base = slugify(name)
    slug, n = base, 2
    while True:
        existing = db.scalar(select(Festival.id).where(Festival.slug == slug))
        if existing is None or existing == exclude_id:
            return slug
        slug = f"{base}-{n}"
        n += 1


def cancel_festival(db: Session, festival: Festival) -> Festival:
    """Cancela el festival: anula pedidos pendientes y reembolsa todos los pagados."""
    festival.status = FestivalStatus.CANCELLED
    orders = db.scalars(select(Order).where(Order.festival_id == festival.id)).all()
    for order in orders:
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            release_stock(order)
            release_discount(order)
        elif order.status == OrderStatus.PAID:
            refund_order(order)
    db.commit()
    db.refresh(festival)
    return festival
