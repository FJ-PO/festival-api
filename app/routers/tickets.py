from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbSession
from app.models import Ticket, TicketStatus, User
from app.schemas.common import Page
from app.schemas.ticket import TicketRead, TicketTransfer, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["Mis entradas"])


def _get_own_ticket(db, ticket_id: int, user: User) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrada no encontrada")
    return ticket


def _ensure_editable(ticket: Ticket) -> None:
    if ticket.status != TicketStatus.VALID:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La entrada está '{ticket.status}'")


@router.get("", response_model=Page[TicketRead])
def my_tickets(
    db: DbSession,
    user: CurrentUser,
    festival_id: int | None = None,
    status_filter: Annotated[TicketStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(Ticket).where(Ticket.owner_id == user.id)
    if festival_id:
        stmt = stmt.where(Ticket.festival_id == festival_id)
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Ticket.issued_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: DbSession, user: CurrentUser):
    """El campo `code` es lo que el front debe codificar en el QR."""
    return _get_own_ticket(db, ticket_id, user)


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, data: TicketUpdate, db: DbSession, user: CurrentUser):
    """Nominar la entrada (cambiar el nombre del asistente)."""
    ticket = _get_own_ticket(db, ticket_id, user)
    _ensure_editable(ticket)
    ticket.attendee_name = data.attendee_name
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/transfer", response_model=TicketRead)
def transfer_ticket(ticket_id: int, data: TicketTransfer, db: DbSession, user: CurrentUser):
    """Transfiere la entrada a otro usuario registrado. Se regenera el código por seguridad."""
    from app.models.ticket import generate_ticket_code

    ticket = _get_own_ticket(db, ticket_id, user)
    _ensure_editable(ticket)
    recipient = db.scalar(select(User).where(User.email == data.email.lower()))
    if recipient is None or not recipient.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ningún usuario con ese email")
    if recipient.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes transferirte una entrada a ti mismo")
    ticket.owner_id = recipient.id
    ticket.attendee_name = data.attendee_name or recipient.full_name
    ticket.code = generate_ticket_code()
    db.commit()
    db.refresh(ticket)
    return ticket
