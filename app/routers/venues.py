from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import AdminUser, DbSession, ManagerUser
from app.models import Festival, Municipality, Venue
from app.schemas.common import Page
from app.schemas.venue import VenueCreate, VenueRead, VenueUpdate

router = APIRouter(prefix="/venues", tags=["Recintos"])


def _get(db, venue_id: int) -> Venue:
    venue = db.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recinto no encontrado")
    return venue


@router.get("", response_model=Page[VenueRead])
def list_venues(
    db: DbSession,
    municipality: Municipality | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(Venue)
    if municipality:
        stmt = stmt.where(Venue.municipality == municipality)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Venue.name).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/municipalities", response_model=list[str])
def list_municipalities():
    """Municipios del Campo de Gibraltar disponibles (para desplegables del front)."""
    return [m.value for m in Municipality]


@router.get("/{venue_id}", response_model=VenueRead)
def get_venue(venue_id: int, db: DbSession):
    return _get(db, venue_id)


@router.post("", response_model=VenueRead, status_code=status.HTTP_201_CREATED)
def create_venue(data: VenueCreate, db: DbSession, _: ManagerUser):
    venue = Venue(**data.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


@router.patch("/{venue_id}", response_model=VenueRead)
def update_venue(venue_id: int, data: VenueUpdate, db: DbSession, _: AdminUser):
    venue = _get(db, venue_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(venue, field, value)
    db.commit()
    db.refresh(venue)
    return venue


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(venue_id: int, db: DbSession, _: AdminUser):
    venue = _get(db, venue_id)
    if db.scalar(select(Festival.id).where(Festival.venue_id == venue_id).limit(1)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El recinto tiene festivales asociados")
    db.delete(venue)
    db.commit()
