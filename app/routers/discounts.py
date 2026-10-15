from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.deps import DbSession, ManagerUser, OptionalUser, get_managed_festival
from app.models import DiscountCode
from app.routers.festivals import get_visible_festival
from app.schemas.discount import DiscountCodeCreate, DiscountCodeRead, DiscountCodeUpdate
from app.services.orders import find_valid_discount

router = APIRouter(tags=["Códigos de descuento"])


class DiscountCheck(BaseModel):
    code: str
    percent_off: int


@router.get("/festivals/{festival_id}/discount-codes", response_model=list[DiscountCodeRead])
def list_discount_codes(festival_id: int, db: DbSession, user: ManagerUser):
    get_managed_festival(db, festival_id, user)
    return db.scalars(select(DiscountCode).where(DiscountCode.festival_id == festival_id)).all()


@router.post(
    "/festivals/{festival_id}/discount-codes",
    response_model=DiscountCodeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_discount_code(festival_id: int, data: DiscountCodeCreate, db: DbSession, user: ManagerUser):
    get_managed_festival(db, festival_id, user)
    discount = DiscountCode(festival_id=festival_id, **data.model_dump())
    db.add(discount)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe ese código para este festival")
    db.refresh(discount)
    return discount


@router.patch("/discount-codes/{discount_id}", response_model=DiscountCodeRead)
def update_discount_code(discount_id: int, data: DiscountCodeUpdate, db: DbSession, user: ManagerUser):
    discount = db.get(DiscountCode, discount_id)
    if discount is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Código no encontrado")
    get_managed_festival(db, discount.festival_id, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(discount, field, value)
    db.commit()
    db.refresh(discount)
    return discount


@router.get("/festivals/{festival_id}/discount-codes/check", response_model=DiscountCheck)
def check_discount_code(festival_id: int, code: str, db: DbSession, user: OptionalUser):
    """Permite al front validar un código antes de crear el pedido."""
    get_visible_festival(db, festival_id, user)
    discount = find_valid_discount(db, festival_id, code)
    return DiscountCheck(code=discount.code, percent_off=discount.percent_off)
