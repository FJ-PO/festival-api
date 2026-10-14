"""Carga datos de ejemplo del Campo de Gibraltar.

Uso:
    python seed.py          # solo si la BD está vacía
    python seed.py --reset  # borra todo y vuelve a cargar
"""

import sys
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import (
    Artist,
    DiscountCode,
    Festival,
    FestivalStatus,
    Municipality,
    Performance,
    TicketType,
    User,
    UserRole,
    Venue,
)

PASSWORD = "Password123"


def seed() -> None:
    if "--reset" in sys.argv:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    if db.scalar(select(User.id).limit(1)):
        print("La base de datos ya tiene datos. Usa --reset para recargarla.")
        return

    users = {
        role: User(email=f"{role.value}@example.com", full_name=name, role=role, hashed_password=hash_password(PASSWORD))
        for role, name in [
            (UserRole.ADMIN, "Administración"),
            (UserRole.ORGANIZER, "Producciones del Estrecho"),
            (UserRole.STAFF, "Personal de Puerta"),
            (UserRole.CUSTOMER, "Cliente de Prueba"),
        ]
    }
    db.add_all(users.values())

    venues = {
        "algeciras": Venue(name="Recinto Ferial de Algeciras", address="Av. de la Feria s/n",
                           municipality=Municipality.ALGECIRAS, capacity=20000, latitude=36.1408, longitude=-5.4562),
        "linea": Venue(name="Recinto Ferial de La Línea", address="Av. Príncipe de Asturias s/n",
                       municipality=Municipality.LA_LINEA, capacity=15000, latitude=36.1680, longitude=-5.3450),
        "tarifa": Venue(name="Explanada Playa de Los Lances", address="Playa de Los Lances",
                        municipality=Municipality.TARIFA, capacity=12000, latitude=36.0250, longitude=-5.6200),
        "jimena": Venue(name="Explanada del Castillo de Jimena", address="Calle Sevilla s/n",
                        municipality=Municipality.JIMENA, capacity=3000, latitude=36.4350, longitude=-5.4530),
    }
    db.add_all(venues.values())

    artists = [
        Artist(name="Levante Eléctrico", genre="Electrónica", country="España"),
        Artist(name="Los del Peñón", genre="Rock", country="España"),
        Artist(name="Marea Baja", genre="Indie", country="España"),
        Artist(name="Duna Flamenca", genre="Flamenco fusión", country="España"),
        Artist(name="Sur Sound System", genre="Reggae", country="España"),
        Artist(name="Atlas Beats", genre="Electrónica", country="Marruecos"),
    ]
    db.add_all(artists)
    organizer = users[UserRole.ORGANIZER]

    estrecho = Festival(
        name="Estrecho Sound Festival", description="Música electrónica y fusión frente a África.",
        genre="Electrónica", start_date=date(2027, 7, 16), end_date=date(2027, 7, 18), min_age=18,
        status=FestivalStatus.PUBLISHED, venue=venues["tarifa"], organizer=organizer, slug="estrecho-sound-festival",
    )
    estrecho.ticket_types = [
        TicketType(name="Abono 3 días", price=Decimal("75.00"), quantity_total=8000, max_per_order=6),
        TicketType(name="Abono VIP", description="Zona VIP con barra propia", price=Decimal("140.00"),
                   quantity_total=500, max_per_order=4),
        TicketType(name="Entrada de día", price=Decimal("35.00"), quantity_total=3000),
    ]
    estrecho.performances = [
        Performance(artist=artists[0], stage="Escenario Levante", start_time=datetime(2027, 7, 16, 22), end_time=datetime(2027, 7, 17, 0)),
        Performance(artist=artists[5], stage="Escenario Levante", start_time=datetime(2027, 7, 17, 0, 30), end_time=datetime(2027, 7, 17, 2)),
        Performance(artist=artists[3], stage="Escenario Poniente", start_time=datetime(2027, 7, 17, 21), end_time=datetime(2027, 7, 17, 22, 30)),
    ]

    bahia = Festival(
        name="Bahía Rock Algeciras", description="Rock e indie en el corazón de la bahía.",
        genre="Rock", start_date=date(2027, 6, 25), end_date=date(2027, 6, 26),
        status=FestivalStatus.PUBLISHED, venue=venues["algeciras"], organizer=organizer, slug="bahia-rock-algeciras",
    )
    bahia.ticket_types = [
        TicketType(name="Abono general", price=Decimal("45.00"), quantity_total=10000),
        TicketType(name="Abono + camping", price=Decimal("65.00"), quantity_total=1500),
    ]
    bahia.performances = [
        Performance(artist=artists[1], stage="Principal", start_time=datetime(2027, 6, 25, 23), end_time=datetime(2027, 6, 26, 0, 30)),
        Performance(artist=artists[2], stage="Principal", start_time=datetime(2027, 6, 26, 21), end_time=datetime(2027, 6, 26, 22, 30)),
    ]

    castillo = Festival(
        name="Noches del Castillo", description="Ciclo íntimo de música de raíz en Jimena.",
        genre="Flamenco", start_date=date(2027, 8, 6), end_date=date(2027, 8, 7),
        status=FestivalStatus.DRAFT, venue=venues["jimena"], organizer=organizer, slug="noches-del-castillo",
    )
    castillo.ticket_types = [TicketType(name="Entrada general", price=Decimal("20.00"), quantity_total=2500)]

    db.add_all([estrecho, bahia, castillo])
    db.flush()
    db.add(DiscountCode(festival_id=estrecho.id, code="CAMPO10", percent_off=10, max_uses=200))
    db.commit()

    print("Datos de ejemplo cargados. Usuarios (contraseña:", PASSWORD + "):")
    for user in users.values():
        print(f"  - {user.email:32} rol={user.role.value}")


if __name__ == "__main__":
    seed()
