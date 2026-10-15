from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select

from app.core.deps import AdminUser, DbSession
from app.models import Subscriber
from app.schemas.cms import SubscriberCreate, SubscriberRead
from app.schemas.common import Message, Page

router = APIRouter(prefix="/newsletter", tags=["CMS · Newsletter"])


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED)
def subscribe(data: SubscriberCreate, db: DbSession, response: Response):
    """Alta pública. Si el email ya estaba suscrito responde 200 sin revelar nada más."""
    email = data.email.lower()
    if db.scalar(select(Subscriber.id).where(Subscriber.email == email)):
        response.status_code = status.HTTP_200_OK
    else:
        db.add(Subscriber(email=email, name=data.name))
        db.commit()
    return Message(detail="¡Gracias! Te avisaremos de las novedades.")


@router.get("", response_model=Page[SubscriberRead])
def list_subscribers(
    db: DbSession,
    _: AdminUser,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(Subscriber)
    if q:
        stmt = stmt.where(Subscriber.email.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Subscriber.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.delete("/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(subscriber_id: int, db: DbSession, _: AdminUser):
    subscriber = db.get(Subscriber, subscriber_id)
    if subscriber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suscriptor no encontrado")
    db.delete(subscriber)
    db.commit()
