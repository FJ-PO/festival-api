from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, GateUser
from app.core.utils import utcnow
from app.models import Ticket, TicketStatus, User, UserRole
from app.schemas.ticket import CheckInRequest, CheckInResult, TicketRead

router = APIRouter(prefix="/checkin", tags=["Control de acceso"])


def _evaluate(db, user: User, code: str, festival_id: int | None) -> tuple[Ticket | None, CheckInResult]:
    ticket = db.scalar(select(Ticket).where(Ticket.code == code.strip().upper()))
    if ticket is None:
        return None, CheckInResult(accepted=False, reason="not_found", message="Entrada no encontrada")

    # Un organizador solo puede validar entradas de sus propios festivales
    if user.role == UserRole.ORGANIZER and ticket.festival.organizer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta entrada pertenece a un festival que no gestionas")

    data = TicketRead.model_validate(ticket)
    if festival_id is not None and ticket.festival_id != festival_id:
        return ticket, CheckInResult(
            accepted=False, reason="wrong_festival", message=f"Entrada de otro festival ({ticket.festival.name})", ticket=data
        )
    if ticket.status == TicketStatus.CANCELLED:
        return ticket, CheckInResult(accepted=False, reason="cancelled", message="Entrada anulada", ticket=data)
    if ticket.status == TicketStatus.USED:
        return ticket, CheckInResult(
            accepted=False,
            reason="already_used",
            message=f"Entrada ya utilizada el {ticket.checked_in_at:%d/%m/%Y a las %H:%M} UTC",
            ticket=data,
        )
    return ticket, CheckInResult(accepted=True, reason="ok", message="Entrada válida", ticket=data)


@router.get("/{code}", response_model=CheckInResult)
def verify_ticket(code: str, db: DbSession, user: GateUser, festival_id: int | None = None):
    """Comprueba una entrada SIN marcarla como usada."""
    _, result = _evaluate(db, user, code, festival_id)
    return result


@router.post("", response_model=CheckInResult)
def check_in(data: CheckInRequest, db: DbSession, user: GateUser):
    """Escanea una entrada en la puerta y, si es válida, la marca como usada."""
    ticket, result = _evaluate(db, user, data.code, data.festival_id)
    if result.accepted and ticket is not None:
        ticket.status = TicketStatus.USED
        ticket.checked_in_at = utcnow()
        ticket.checked_in_by_id = user.id
        db.commit()
        db.refresh(ticket)
        result.ticket = TicketRead.model_validate(ticket)
        result.message = f"Acceso permitido: {ticket.attendee_name} ({ticket.ticket_type.name})"
    return result
