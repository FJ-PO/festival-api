from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.core.deps import (
    DbSession,
    ManagerUser,
    OptionalUser,
    can_manage_festival,
    get_managed_festival,
)
from app.models import (
    Artist,
    Festival,
    FestivalStatus,
    Municipality,
    Order,
    OrderStatus,
    Performance,
    Ticket,
    TicketStatus,
    UserRole,
    Venue,
)
from app.schemas.common import Page
from app.schemas.festival import (
    FestivalCreate,
    FestivalDetail,
    FestivalRead,
    FestivalUpdate,
    PerformanceCreate,
    PerformanceRead,
)
from app.schemas.stats import FestivalStats, TicketTypeStats
from app.services.festivals import cancel_festival, unique_slug

router = APIRouter(prefix="/festivals", tags=["Festivales"])


def get_visible_festival(db, festival_id: int, user) -> Festival:
    """Los borradores solo son visibles para quien puede gestionarlos."""
    festival = db.get(Festival, festival_id)
    if festival is None or (
        festival.status == FestivalStatus.DRAFT and not can_manage_festival(user, festival)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Festival no encontrado")
    return festival


# ---------- Consulta pública ----------


@router.get("", response_model=Page[FestivalRead])
def list_festivals(
    db: DbSession,
    q: Annotated[str | None, Query(description="Texto libre: nombre, descripción o artista")] = None,
    municipality: Municipality | None = None,
    genre: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    include_past: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Catálogo público de festivales publicados, ordenados por fecha."""
    stmt = select(Festival).join(Festival.venue).where(Festival.status == FestivalStatus.PUBLISHED)
    if not include_past:
        stmt = stmt.where(Festival.end_date >= date.today())
    if q:
        like = f"%{q}%"
        artist_match = (
            select(Performance.festival_id)
            .join(Performance.artist)
            .where(Artist.name.ilike(like))
        )
        stmt = stmt.where(
            or_(Festival.name.ilike(like), Festival.description.ilike(like), Festival.id.in_(artist_match))
        )
    if municipality:
        stmt = stmt.where(Venue.municipality == municipality)
    if genre:
        stmt = stmt.where(Festival.genre.ilike(f"%{genre}%"))
    if date_from:
        stmt = stmt.where(Festival.end_date >= date_from)
    if date_to:
        stmt = stmt.where(Festival.start_date <= date_to)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Festival.start_date).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/manage", response_model=Page[FestivalRead])
def list_managed_festivals(
    db: DbSession,
    user: ManagerUser,
    status_filter: Annotated[FestivalStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Festivales del organizador (todos los estados). El admin ve todos."""
    stmt = select(Festival)
    if user.role != UserRole.ADMIN:
        stmt = stmt.where(Festival.organizer_id == user.id)
    if status_filter:
        stmt = stmt.where(Festival.status == status_filter)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Festival.start_date.desc()).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/slug/{slug}", response_model=FestivalDetail)
def get_festival_by_slug(slug: str, db: DbSession, user: OptionalUser):
    festival_id = db.scalar(select(Festival.id).where(Festival.slug == slug))
    if festival_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Festival no encontrado")
    return get_visible_festival(db, festival_id, user)


@router.get("/{festival_id}", response_model=FestivalDetail)
def get_festival(festival_id: int, db: DbSession, user: OptionalUser):
    return get_visible_festival(db, festival_id, user)


# ---------- Gestión (organizador / admin) ----------


@router.post("", response_model=FestivalRead, status_code=status.HTTP_201_CREATED)
def create_festival(data: FestivalCreate, db: DbSession, user: ManagerUser):
    if db.get(Venue, data.venue_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recinto no encontrado")
    festival = Festival(**data.model_dump(), slug=unique_slug(db, data.name), organizer_id=user.id)
    db.add(festival)
    db.commit()
    db.refresh(festival)
    return festival


@router.patch("/{festival_id}", response_model=FestivalRead)
def update_festival(festival_id: int, data: FestivalUpdate, db: DbSession, user: ManagerUser):
    festival = get_managed_festival(db, festival_id, user)
    if festival.status in (FestivalStatus.CANCELLED, FestivalStatus.FINISHED):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede editar un festival cancelado o finalizado")
    changes = data.model_dump(exclude_unset=True)
    if "venue_id" in changes and db.get(Venue, changes["venue_id"]) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recinto no encontrado")
    start = changes.get("start_date", festival.start_date)
    end = changes.get("end_date", festival.end_date)
    if end < start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "end_date no puede ser anterior a start_date")
    for field, value in changes.items():
        setattr(festival, field, value)
    if "name" in changes:
        festival.slug = unique_slug(db, festival.name, exclude_id=festival.id)
    db.commit()
    db.refresh(festival)
    return festival


@router.delete("/{festival_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_festival(festival_id: int, db: DbSession, user: ManagerUser):
    """Solo se pueden borrar borradores sin pedidos. Para el resto, usa /cancel."""
    festival = get_managed_festival(db, festival_id, user)
    has_orders = db.scalar(select(Order.id).where(Order.festival_id == festival_id).limit(1))
    if festival.status != FestivalStatus.DRAFT or has_orders:
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se pueden eliminar festivales en borrador sin pedidos")
    db.delete(festival)
    db.commit()


@router.post("/{festival_id}/publish", response_model=FestivalRead)
def publish_festival(festival_id: int, db: DbSession, user: ManagerUser):
    festival = get_managed_festival(db, festival_id, user)
    if festival.status != FestivalStatus.DRAFT:
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se pueden publicar festivales en borrador")
    if not any(tt.is_active for tt in festival.ticket_types):
        raise HTTPException(status.HTTP_409_CONFLICT, "Añade al menos un tipo de entrada activo antes de publicar")
    festival.status = FestivalStatus.PUBLISHED
    db.commit()
    db.refresh(festival)
    return festival


@router.post("/{festival_id}/cancel", response_model=FestivalRead)
def cancel(festival_id: int, db: DbSession, user: ManagerUser):
    """Cancela el festival y reembolsa automáticamente todos los pedidos pagados."""
    festival = get_managed_festival(db, festival_id, user)
    if festival.status in (FestivalStatus.CANCELLED, FestivalStatus.FINISHED):
        raise HTTPException(status.HTTP_409_CONFLICT, f"El festival ya está '{festival.status}'")
    return cancel_festival(db, festival)


@router.post("/{festival_id}/finish", response_model=FestivalRead)
def finish_festival(festival_id: int, db: DbSession, user: ManagerUser):
    festival = get_managed_festival(db, festival_id, user)
    if festival.status != FestivalStatus.PUBLISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se pueden finalizar festivales publicados")
    festival.status = FestivalStatus.FINISHED
    db.commit()
    db.refresh(festival)
    return festival


# ---------- Cartel (line-up) ----------


@router.get("/{festival_id}/lineup", response_model=list[PerformanceRead])
def get_lineup(festival_id: int, db: DbSession, user: OptionalUser):
    return get_visible_festival(db, festival_id, user).performances


@router.post("/{festival_id}/lineup", response_model=PerformanceRead, status_code=status.HTTP_201_CREATED)
def add_performance(festival_id: int, data: PerformanceCreate, db: DbSession, user: ManagerUser):
    festival = get_managed_festival(db, festival_id, user)
    if db.get(Artist, data.artist_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artista no encontrado")
    # Se permite que los conciertos acaben de madrugada del día siguiente al último día
    last_allowed = festival.end_date + timedelta(days=1)
    if not (festival.start_date <= data.start_time.date() <= festival.end_date) or data.end_time.date() > last_allowed:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La actuación está fuera de las fechas del festival")
    overlap = db.scalar(
        select(Performance.id).where(
            Performance.festival_id == festival_id,
            Performance.stage == data.stage,
            Performance.start_time < data.end_time,
            Performance.end_time > data.start_time,
        )
    )
    if overlap:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya hay una actuación en '{data.stage}' en ese horario")
    performance = Performance(festival_id=festival_id, **data.model_dump())
    db.add(performance)
    db.commit()
    db.refresh(performance)
    return performance


@router.delete("/{festival_id}/lineup/{performance_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_performance(festival_id: int, performance_id: int, db: DbSession, user: ManagerUser):
    get_managed_festival(db, festival_id, user)
    performance = db.get(Performance, performance_id)
    if performance is None or performance.festival_id != festival_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Actuación no encontrada")
    db.delete(performance)
    db.commit()


# ---------- Estadísticas ----------


@router.get("/{festival_id}/stats", response_model=FestivalStats)
def festival_stats(festival_id: int, db: DbSession, user: ManagerUser):
    festival = get_managed_festival(db, festival_id, user)

    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.festival_id == festival_id, Order.status == OrderStatus.PAID
        )
    )
    orders_by_status = {s.value: 0 for s in OrderStatus}
    for st, count in db.execute(
        select(Order.status, func.count()).where(Order.festival_id == festival_id).group_by(Order.status)
    ):
        orders_by_status[st.value] = count

    ticket_counts = dict(
        db.execute(
            select(Ticket.status, func.count()).where(Ticket.festival_id == festival_id).group_by(Ticket.status)
        ).all()
    )
    issued = ticket_counts.get(TicketStatus.VALID, 0) + ticket_counts.get(TicketStatus.USED, 0)
    checked_in = ticket_counts.get(TicketStatus.USED, 0)

    return FestivalStats(
        festival_id=festival.id,
        festival_name=festival.name,
        revenue=revenue,
        orders_by_status=orders_by_status,
        tickets_issued=issued,
        tickets_checked_in=checked_in,
        attendance_rate=round(checked_in / issued, 4) if issued else 0.0,
        ticket_types=[
            TicketTypeStats(
                ticket_type_id=tt.id,
                name=tt.name,
                price=tt.price,
                quantity_total=tt.quantity_total,
                quantity_sold=tt.quantity_sold,
                quantity_available=tt.quantity_available,
            )
            for tt in festival.ticket_types
        ],
    )
