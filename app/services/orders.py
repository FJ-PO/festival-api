"""Lógica de negocio de pedidos: reserva de stock, descuentos, pago, cancelación y reembolso."""

import secrets
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.utils import utcnow
from app.models import (
    DiscountCode,
    Festival,
    FestivalStatus,
    Order,
    OrderItem,
    OrderStatus,
    Ticket,
    TicketStatus,
    TicketType,
    User,
)
from app.schemas.order import OrderCreate, OrderPay

CENT = Decimal("0.01")


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail)


def release_stock(order: Order) -> None:
    for item in order.items:
        item.ticket_type.quantity_sold = max(item.ticket_type.quantity_sold - item.quantity, 0)


def release_discount(order: Order) -> None:
    if order.discount_code is not None:
        order.discount_code.times_used = max(order.discount_code.times_used - 1, 0)


def expire_pending_orders(db: Session, festival_id: int | None = None) -> int:
    """Marca como expirados los pedidos pendientes caducados y libera sus entradas reservadas."""
    stmt = select(Order).where(Order.status == OrderStatus.PENDING, Order.expires_at < utcnow())
    if festival_id is not None:
        stmt = stmt.where(Order.festival_id == festival_id)
    expired = db.scalars(stmt).all()
    for order in expired:
        order.status = OrderStatus.EXPIRED
        release_stock(order)
        release_discount(order)
    return len(expired)


def find_valid_discount(db: Session, festival_id: int, code: str) -> DiscountCode:
    discount = db.scalar(
        select(DiscountCode).where(
            DiscountCode.festival_id == festival_id, DiscountCode.code == code.strip().upper()
        )
    )
    if discount is None or not discount.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Código de descuento no válido")
    if discount.valid_until and discount.valid_until < utcnow():
        raise _conflict("El código de descuento ha caducado")
    if discount.max_uses is not None and discount.times_used >= discount.max_uses:
        raise _conflict("El código de descuento ha alcanzado su límite de usos")
    return discount


def create_order(db: Session, user: User, data: OrderCreate) -> Order:
    festival = db.get(Festival, data.festival_id)
    if festival is None or festival.status != FestivalStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Festival no disponible")
    if festival.end_date < date.today():
        raise _conflict("El festival ya ha terminado")

    expire_pending_orders(db, festival.id)
    now = utcnow()

    # Agrupa líneas repetidas del mismo tipo de entrada
    quantities: dict[int, int] = {}
    for item in data.items:
        quantities[item.ticket_type_id] = quantities.get(item.ticket_type_id, 0) + item.quantity

    items: list[OrderItem] = []
    subtotal = Decimal("0.00")
    for ticket_type_id, quantity in quantities.items():
        tt = db.get(TicketType, ticket_type_id, with_for_update=True)
        if tt is None or tt.festival_id != festival.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Tipo de entrada {ticket_type_id} no encontrado")
        if not tt.is_active:
            raise _conflict(f"'{tt.name}' no está a la venta")
        if tt.sale_start and now < tt.sale_start:
            raise _conflict(f"La venta de '{tt.name}' aún no ha comenzado")
        if tt.sale_end and now > tt.sale_end:
            raise _conflict(f"La venta de '{tt.name}' ha finalizado")
        if quantity > tt.max_per_order:
            raise _conflict(f"Máximo {tt.max_per_order} entradas '{tt.name}' por pedido")
        if quantity > tt.quantity_available:
            raise _conflict(f"Solo quedan {tt.quantity_available} entradas '{tt.name}'")

        tt.quantity_sold += quantity  # reserva
        subtotal += tt.price * quantity
        items.append(OrderItem(ticket_type=tt, quantity=quantity, unit_price=tt.price))

    discount = None
    discount_amount = Decimal("0.00")
    if data.discount_code:
        discount = find_valid_discount(db, festival.id, data.discount_code)
        discount_amount = (subtotal * discount.percent_off / 100).quantize(CENT, ROUND_HALF_UP)
        discount.times_used += 1

    order = Order(
        user=user,
        festival=festival,
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        discount_amount=discount_amount,
        total=subtotal - discount_amount,
        discount_code=discount,
        expires_at=now + timedelta(minutes=settings.order_expiration_minutes),
        items=items,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def pay_order(db: Session, order: Order, data: OrderPay) -> Order:
    if order.status != OrderStatus.PENDING:
        raise _conflict(f"El pedido está en estado '{order.status}' y no se puede pagar")
    if order.expires_at < utcnow():
        order.status = OrderStatus.EXPIRED
        release_stock(order)
        release_discount(order)
        db.commit()
        raise _conflict("El pedido ha caducado; las entradas se han liberado")

    # --- Pago simulado: aquí se integraría la pasarela real ---
    if data.payment_method == "card" and data.card_number and data.card_number.endswith("0000"):
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Pago rechazado por la entidad")

    order.status = OrderStatus.PAID
    order.paid_at = utcnow()
    order.payment_method = data.payment_method
    order.payment_reference = f"PAY-{secrets.token_hex(8).upper()}"

    for item in order.items:
        for _ in range(item.quantity):
            db.add(
                Ticket(
                    order=order,
                    ticket_type_id=item.ticket_type_id,
                    festival_id=order.festival_id,
                    owner_id=order.user_id,
                    attendee_name=order.user.full_name,
                )
            )
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: Order) -> Order:
    """Cancela un pedido pendiente o reembolsa uno pagado (si el festival no ha empezado)."""
    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.CANCELLED
        release_stock(order)
        release_discount(order)
    elif order.status == OrderStatus.PAID:
        if order.festival.start_date <= date.today():
            raise _conflict("No se pueden reembolsar pedidos una vez comenzado el festival")
        if any(t.status == TicketStatus.USED for t in order.tickets):
            raise _conflict("El pedido tiene entradas ya utilizadas")
        refund_order(order)
    else:
        raise _conflict(f"El pedido está en estado '{order.status}' y no se puede cancelar")
    db.commit()
    db.refresh(order)
    return order


def refund_order(order: Order) -> None:
    order.status = OrderStatus.REFUNDED
    for ticket in order.tickets:
        ticket.status = TicketStatus.CANCELLED
    release_stock(order)
