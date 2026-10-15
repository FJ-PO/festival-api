from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbSession, ManagerUser, can_manage_festival, get_managed_festival
from app.models import Order, OrderStatus, UserRole
from app.schemas.common import Page
from app.schemas.order import OrderCreate, OrderPay, OrderRead
from app.services import orders as order_service

router = APIRouter(tags=["Pedidos"])


def _get_order(db, order_id: int, user) -> Order:
    order = db.get(Order, order_id)
    if order is None or (
        order.user_id != user.id
        and user.role != UserRole.ADMIN
        and not can_manage_festival(user, order.festival)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return order


@router.post("/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, db: DbSession, user: CurrentUser):
    """Crea un pedido pendiente y reserva las entradas durante unos minutos hasta que se pague."""
    return order_service.create_order(db, user, data)


@router.get("/orders", response_model=Page[OrderRead])
def my_orders(
    db: DbSession,
    user: CurrentUser,
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    order_service.expire_pending_orders(db)
    db.commit()
    stmt = select(Order).where(Order.user_id == user.id)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: DbSession, user: CurrentUser):
    return _get_order(db, order_id, user)


@router.post("/orders/{order_id}/pay", response_model=OrderRead)
def pay_order(order_id: int, data: OrderPay, db: DbSession, user: CurrentUser):
    """Pago simulado. Una tarjeta acabada en 0000 simula un pago rechazado."""
    order = _get_order(db, order_id, user)
    if order.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el comprador puede pagar el pedido")
    return order_service.pay_order(db, order, data)


@router.post("/orders/{order_id}/cancel", response_model=OrderRead)
def cancel_order(order_id: int, db: DbSession, user: CurrentUser):
    """Cancela un pedido pendiente, o solicita el reembolso de uno pagado antes del festival."""
    return order_service.cancel_order(db, _get_order(db, order_id, user))


@router.get("/festivals/{festival_id}/orders", response_model=Page[OrderRead])
def festival_orders(
    festival_id: int,
    db: DbSession,
    user: ManagerUser,
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Listado de pedidos de un festival para el organizador."""
    get_managed_festival(db, festival_id, user)
    stmt = select(Order).where(Order.festival_id == festival_id)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=items, total=total, limit=limit, offset=offset)
