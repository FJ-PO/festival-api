from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import AdminUser, DbSession, ManagerUser
from app.models import Artist, Performance
from app.schemas.artist import ArtistCreate, ArtistRead, ArtistUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/artists", tags=["Artistas"])


def _get(db, artist_id: int) -> Artist:
    artist = db.get(Artist, artist_id)
    if artist is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artista no encontrado")
    return artist


@router.get("", response_model=Page[ArtistRead])
def list_artists(
    db: DbSession,
    q: Annotated[str | None, Query(description="Busca por nombre")] = None,
    genre: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(Artist)
    if q:
        stmt = stmt.where(Artist.name.ilike(f"%{q}%"))
    if genre:
        stmt = stmt.where(Artist.genre.ilike(f"%{genre}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Artist.name).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{artist_id}", response_model=ArtistRead)
def get_artist(artist_id: int, db: DbSession):
    return _get(db, artist_id)


@router.post("", response_model=ArtistRead, status_code=status.HTTP_201_CREATED)
def create_artist(data: ArtistCreate, db: DbSession, _: ManagerUser):
    artist = Artist(**data.model_dump())
    db.add(artist)
    db.commit()
    db.refresh(artist)
    return artist


@router.patch("/{artist_id}", response_model=ArtistRead)
def update_artist(artist_id: int, data: ArtistUpdate, db: DbSession, _: ManagerUser):
    artist = _get(db, artist_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(artist, field, value)
    db.commit()
    db.refresh(artist)
    return artist


@router.delete("/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artist(artist_id: int, db: DbSession, _: AdminUser):
    artist = _get(db, artist_id)
    if db.scalar(select(Performance.id).where(Performance.artist_id == artist_id).limit(1)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El artista está en el cartel de algún festival")
    db.delete(artist)
    db.commit()
