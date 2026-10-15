from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, ManagerUser, OptionalUser, can_manage_festival, get_managed_festival
from app.models import OrderItem, TicketType
from app.routers.festivals import get_visible_festival
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeRead, TicketTypeUpdate

router = APIRouter(tags=["Tipos de entrada"])


def _get_managed(db, ticket_type_id: int, user) -> TicketType:
    tt = db.get(TicketType, ticket_type_id)
    if tt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tipo de entrada no encontrado")
    get_managed_festival(db, tt.festival_id, user)
    return tt


@router.get("/festivals/{festival_id}/ticket-types", response_model=list[TicketTypeRead])
def list_ticket_types(festival_id: int, db: DbSession, user: OptionalUser):
    """El público ve solo los tipos activos; el organizador ve todos."""
    festival = get_visible_festival(db, festival_id, user)
    if can_manage_festival(user, festival):
        return festival.ticket_types
    return [tt for tt in festival.ticket_types if tt.is_active]


@router.post(
    "/festivals/{festival_id}/ticket-types",
    response_model=TicketTypeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_type(festival_id: int, data: TicketTypeCreate, db: DbSession, user: ManagerUser):
    get_managed_festival(db, festival_id, user)
    tt = TicketType(festival_id=festival_id, **data.model_dump())
    db.add(tt)
    db.commit()
    db.refresh(tt)
    return tt


@router.patch("/ticket-types/{ticket_type_id}", response_model=TicketTypeRead)
def update_ticket_type(ticket_type_id: int, data: TicketTypeUpdate, db: DbSession, user: ManagerUser):
    tt = _get_managed(db, ticket_type_id, user)
    changes = data.model_dump(exclude_unset=True)
    if "quantity_total" in changes and changes["quantity_total"] < tt.quantity_sold:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Ya hay {tt.quantity_sold} entradas vendidas/reservadas de este tipo"
        )
    for field, value in changes.items():
        setattr(tt, field, value)
    db.commit()
    db.refresh(tt)
    return tt


@router.delete("/ticket-types/{ticket_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_type(ticket_type_id: int, db: DbSession, user: ManagerUser):
    """Solo si nunca se ha pedido; si no, desactívalo con PATCH is_active=false."""
    tt = _get_managed(db, ticket_type_id, user)
    if db.scalar(select(OrderItem.id).where(OrderItem.ticket_type_id == tt.id).limit(1)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este tipo de entrada ya tiene pedidos; desactívalo en su lugar")
    db.delete(tt)
    db.commit()
