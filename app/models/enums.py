from enum import StrEnum

from sqlalchemy import Enum


class UserRole(StrEnum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    STAFF = "staff"
    CUSTOMER = "customer"


class FestivalStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    FINISHED = "finished"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class TicketStatus(StrEnum):
    VALID = "valid"
    USED = "used"
    CANCELLED = "cancelled"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


def enum_column(enum_cls: type[StrEnum]) -> Enum:
    """Guarda en BD el valor del enum ('admin') en lugar del nombre ('ADMIN')."""
    return Enum(enum_cls, values_callable=lambda e: [m.value for m in e], native_enum=False, length=40)


class Municipality(StrEnum):
    """Municipios de la comarca del Campo de Gibraltar (Cádiz)."""

    ALGECIRAS = "Algeciras"
    LA_LINEA = "La Línea de la Concepción"
    SAN_ROQUE = "San Roque"
    LOS_BARRIOS = "Los Barrios"
    TARIFA = "Tarifa"
    JIMENA = "Jimena de la Frontera"
    CASTELLAR = "Castellar de la Frontera"
