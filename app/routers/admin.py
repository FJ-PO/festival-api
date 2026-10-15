"""Datos agregados para el escritorio del panel de administración."""

from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.deps import DbSession, ManagerUser
from app.core.utils import utcnow
from app.models import (
    Artist,
    Festival,
    FestivalStatus,
    Order,
    OrderStatus,
    Page,
    Post,
    Ticket,
    TicketStatus,
    User,
    UserRole,
    Venue,
)
from app.schemas.cms import Dashboard, RecentOrder, SalesPoint

router = APIRouter(prefix="/admin", tags=["Panel de administración"])


@router.get("/dashboard", response_model=Dashboard)
def dashboard(db: DbSession, user: ManagerUser):
    """Resumen de actividad. El admin ve todo; un organizador, solo sus festivales."""
    festival_ids = select(Festival.id)
    if user.role != UserRole.ADMIN:
        festival_ids = festival_ids.where(Festival.organizer_id == user.id)

    festivals_by_status = {s.value: 0 for s in FestivalStatus}
    for st, count in db.execute(
        select(Festival.status, func.count()).where(Festival.id.in_(festival_ids)).group_by(Festival.status)
    ):
        festivals_by_status[st.value] = count

    users_by_role = {r.value: 0 for r in UserRole}
    if user.role == UserRole.ADMIN:
        for role, count in db.execute(select(User.role, func.count()).group_by(User.role)):
            users_by_role[role.value] = count

    paid = select(Order).where(Order.status == OrderStatus.PAID, Order.festival_id.in_(festival_ids)).subquery()
    revenue = db.scalar(select(func.coalesce(func.sum(paid.c.total), 0)))
    orders_paid = db.scalar(select(func.count()).select_from(paid))

    tickets = dict(
        db.execute(
            select(Ticket.status, func.count()).where(Ticket.festival_id.in_(festival_ids)).group_by(Ticket.status)
        ).all()
    )

    since = utcnow() - timedelta(days=29)
    day = func.date(Order.paid_at)
    per_day = {
        str(d): (Decimal(str(total)), n)
        for d, total, n in db.execute(
            select(day, func.sum(Order.total), func.count())
            .where(Order.status == OrderStatus.PAID, Order.paid_at >= since, Order.festival_id.in_(festival_ids))
            .group_by(day)
        )
    }
    sales = []
    for i in range(30):
        key = (since + timedelta(days=i)).date().isoformat()
        total, n = per_day.get(key, (Decimal("0"), 0))
        sales.append(SalesPoint(day=key, revenue=total, orders=n))

    recent = db.scalars(
        select(Order).where(Order.festival_id.in_(festival_ids)).order_by(Order.created_at.desc()).limit(8)
    ).all()

    return Dashboard(
        festivals_by_status=festivals_by_status,
        users_by_role=users_by_role,
        revenue=revenue,
        orders_paid=orders_paid,
        tickets_sold=tickets.get(TicketStatus.VALID, 0) + tickets.get(TicketStatus.USED, 0),
        tickets_checked_in=tickets.get(TicketStatus.USED, 0),
        artists=db.scalar(select(func.count(Artist.id))),
        venues=db.scalar(select(func.count(Venue.id))),
        pages=db.scalar(select(func.count(Page.id))),
        posts=db.scalar(select(func.count(Post.id))),
        sales_last_30_days=sales,
        recent_orders=[
            RecentOrder(
                id=o.id,
                festival_name=o.festival.name,
                customer=o.user.full_name,
                total=o.total,
                status=o.status.value,
                created_at=o.created_at,
            )
            for o in recent
        ],
    )
