"""Carga los datos de ejemplo: ciclo de conciertos y humor en la Plaza de Toros de Algeciras.

Uso:
    python seed.py          # solo si la BD está vacía
    python seed.py --reset  # borra todo y vuelve a cargar
"""

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.config import settings
from app.core.security import hash_password
from app.core.utils import slugify, utcnow
from app.db.bootstrap import ensure_admin
from app.db.session import Base, SessionLocal, engine
from app.models import (
    Artist,
    ContentStatus,
    DiscountCode,
    Festival,
    FestivalStatus,
    Municipality,
    Page,
    Performance,
    Post,
    TicketType,
    User,
    UserRole,
    Venue,
)

PASSWORD = "Password123"
STAGE = "Escenario Las Palomas"

# Una noche por semana, todos los sábados desde FIRST_NIGHT
FIRST_NIGHT = date(2027, 5, 8)

# (artista, género, procedencia, bio, edad mínima, precios pista/grada/front stage)
LINEUP = [
    ("Melendi", "Pop", "Asturias", "Rumba, pop y canciones que se cantan de principio a fin.",
     0, ("39.00", "45.00", "75.00")),
    ("Niña Pastori", "Flamenco", "San Fernando (Cádiz)", "Una de las grandes voces del flamenco, en casa.",
     0, ("35.00", "42.00", "70.00")),
    ("Dellafuente", "Urbano", "Granada", "Flamenco, R&B y música urbana con sello propio.",
     0, ("32.00", "38.00", "65.00")),
    ("Dani Rovira", "Humor", "Málaga", "Monólogo y humor andaluz para toda la plaza.",
     12, ("25.00", "30.00", "45.00")),
    ("India Martínez", "Flamenco pop", "Córdoba", "Flamenco, pop y aires orientales en una voz inconfundible.",
     0, ("35.00", "40.00", "68.00")),
    ("Lola Índigo", "Pop urbano", "Granada", "Pop urbano, baile y uno de los directos más potentes del momento.",
     0, ("36.00", "42.00", "70.00")),
    ("Maka", "Flamenco urbano", "Andalucía", "Rumba, flamenco y calle: la voz del flamenco urbano.",
     0, ("28.00", "34.00", "55.00")),
    ("Los Morancos", "Humor", "Triana (Sevilla)", "Personajes, sketches y décadas de risas.",
     0, ("28.00", "33.00", "50.00")),
    ("Manuel Carrasco", "Pop", "Isla Cristina (Huelva)", "Pop de estadio con alma del sur.",
     0, ("42.00", "48.00", "80.00")),
    ("Ana Mena", "Pop urbano", "Estepona (Málaga)", "Hits de pop latino para bailar toda la noche.",
     0, ("32.00", "38.00", "60.00")),
    ("Andy & Lucas", "Pop", "Cádiz", "El dúo gaditano vuelve a la provincia con todos sus éxitos.",
     0, ("30.00", "35.00", "58.00")),
    ("Leo Harlem", "Humor", "Valladolid", "Humor blanco y observación de lo cotidiano.",
     0, ("25.00", "30.00", "45.00")),
    ("Estopa", "Rock", "Cornellà (Barcelona)", "Rumba-rock, guitarras y coros multitudinarios.",
     0, ("40.00", "46.00", "78.00")),
    ("Manu Sánchez", "Humor", "Dos Hermanas (Sevilla)", "Humor, música y mucha Andalucía.",
     0, ("24.00", "28.00", "42.00")),
    ("Antonio José", "Pop", "Córdoba", "Baladas y pop con raíz flamenca.",
     0, ("30.00", "36.00", "58.00")),
    ("Rels B", "Urbano", "Mallorca", "Música urbana, R&B y flow mediterráneo.",
     0, ("33.00", "39.00", "62.00")),
    ("Comandante Lara & Cía", "Humor", "Cádiz", "Humor gaditano de una de las voces más reconocibles de la provincia.",
     0, ("22.00", "26.00", "40.00")),
]


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
            (UserRole.ORGANIZER, "Producciones Las Palomas"),
            (UserRole.STAFF, "Personal de Puerta"),
            (UserRole.CUSTOMER, "Cliente de Prueba"),
        ]
    }
    db.add_all(users.values())
    organizer = users[UserRole.ORGANIZER]

    plaza = Venue(
        name="Plaza de Toros de Algeciras",
        address="Plaza de Toros de Las Palomas, Algeciras (Cádiz)",
        municipality=Municipality.ALGECIRAS,
        capacity=6000,
    )
    db.add(plaza)

    festivals = []
    for week, (name, genre, origin, bio, min_age, (pista, grada, front)) in enumerate(LINEUP):
        day = FIRST_NIGHT + timedelta(weeks=week)
        artist = Artist(name=name, genre=genre, country=origin, bio=bio)
        start = datetime.combine(day, datetime.min.time()).replace(hour=22)
        is_humor = genre == "Humor"
        festival = Festival(
            name=name,
            slug=slugify(f"{name} algeciras {day.year}"),
            description=(
                f"{bio} Una noche única en la Plaza de Toros de Algeciras dentro del ciclo Las Palomas Festival."
            ),
            genre=genre,
            start_date=day,
            end_date=day,
            min_age=min_age,
            status=FestivalStatus.PUBLISHED,
            venue=plaza,
            organizer=organizer,
        )
        festival.ticket_types = [
            TicketType(name="Pista", description="De pie, en el ruedo", price=Decimal(pista), quantity_total=3500,
                       max_per_order=8),
            TicketType(name="Grada", description="Asiento numerado en tendido", price=Decimal(grada),
                       quantity_total=2200, max_per_order=8),
            TicketType(name="Primera fila" if is_humor else "Front Stage",
                       description="Zona preferente junto al escenario con acceso exclusivo",
                       price=Decimal(front), quantity_total=300, max_per_order=4),
        ]
        festival.performances = [
            Performance(artist=artist, stage=STAGE, start_time=start,
                        end_time=start + timedelta(minutes=90 if is_humor else 120)),
        ]
        festivals.append(festival)

    # Una noche aún en borrador, para ver cómo funciona la publicación desde el panel
    last_day = FIRST_NIGHT + timedelta(weeks=len(LINEUP))
    draft = Festival(
        name="Noche de Carnaval de Cádiz", slug="noche-de-carnaval-cadiz-2027",
        description="Chirigotas y comparsas de Cádiz en Algeciras. Agrupaciones por confirmar.",
        genre="Humor", start_date=last_day, end_date=last_day,
        status=FestivalStatus.DRAFT, venue=plaza, organizer=organizer,
    )
    draft.ticket_types = [TicketType(name="Entrada general", price=Decimal("18.00"), quantity_total=5000)]
    festivals.append(draft)

    db.add_all(festivals)
    db.flush()
    db.add(DiscountCode(festival_id=festivals[0].id, code="PALOMAS10", percent_off=10, max_uses=300))
    db.commit()

    admin = ensure_admin(db)
    seed_cms(db, admin.id, festivals[0].id)

    print(f"Administrador del panel: usuario '{settings.admin_username}' / contraseña '{settings.admin_password}'")
    print(f"{len(festivals)} noches cargadas en la Plaza de Toros de Algeciras. Código de descuento: PALOMAS10")
    print("Usuarios de ejemplo (contraseña:", PASSWORD + "):")
    for user in users.values():
        print(f"  - {user.email:32} rol={user.role.value}")


def seed_cms(db, author_id: int, featured_festival_id: int) -> None:
    """Ajustes del sitio, páginas y noticias de ejemplo para la web pública."""
    from app.schemas.cms import SiteSettings
    from app.services.cms import get_site_config

    config = get_site_config(db)
    config.data = SiteSettings(
        featured_festival_id=featured_festival_id,
        social={"instagram": "https://instagram.com/", "facebook": "https://facebook.com/",
                "tiktok": "https://tiktok.com/", "youtube": "https://youtube.com/"},
    ).model_dump()

    published = {"status": ContentStatus.PUBLISHED, "published_at": utcnow(), "author_id": author_id}
    db.add_all([
        Page(title="Info de interés", slug="info-de-interes", show_in_menu=True, menu_order=1,
             excerpt="Accesos, horarios, edades y todo lo que necesitas saber.", **published, content=INFO_MD),
        Page(title="Preguntas frecuentes", slug="preguntas-frecuentes", show_in_menu=True, menu_order=2,
             excerpt="Entradas, devoluciones, menores, transferencias...", **published, content=FAQ_MD),
        Page(title="Cómo llegar", slug="como-llegar", show_in_menu=True, menu_order=3,
             excerpt="Autobús, tren, barco y coche hasta la Plaza de Toros.", **published, content=TRAVEL_MD),
        Page(title="Aviso legal y privacidad", slug="aviso-legal", **published, content=LEGAL_MD),
        Post(title="Las Palomas Festival presenta su programación 2027", slug="programacion-2027",
             excerpt="Una noche cada sábado, de mayo a agosto, en la Plaza de Toros de Algeciras.", **published,
             content="Melendi abre el ciclo el **sábado 8 de mayo** y, cada sábado hasta finales de agosto, por la plaza pasarán Niña Pastori, Dellafuente, "
                     "India Martínez, Lola Índigo, Maka, Manuel Carrasco y muchos más.\n\n"
                     "Las entradas ya están a la venta en esta web."),
        Post(title="Llegan las noches de humor", slug="noches-de-humor",
             excerpt="Dani Rovira, Los Morancos, Leo Harlem, Manu Sánchez y Comandante Lara.", **published,
             content="Este verano el humor también tiene su sitio en la plaza: **cinco noches** para reír a lo grande."),
        Post(title="Nuevas confirmaciones muy pronto", slug="nuevas-confirmaciones",
             excerpt="Aún quedan fechas por anunciar. Suscríbete para enterarte antes que nadie.", **published,
             content="Estamos cerrando los últimos nombres del cartel. ¡Atento a nuestras redes!"),
    ])
    db.commit()


INFO_MD = """## Entradas

Las entradas se compran **solo en esta web**. Tras el pago tendrás tus entradas con **código QR**
en *Mi cuenta → Mis entradas*. Puedes ponerlas a nombre de otra persona o transferirlas.

## Zonas

- **Pista**: de pie, en el ruedo.
- **Grada**: asiento numerado en tendido.
- **Front Stage / Primera fila**: zona preferente junto al escenario, con acceso exclusivo.

## Horarios

Apertura de puertas a las **20:30**. Los espectáculos empiezan a las **22:00**.

## Acceso

Lleva el QR en el móvil (o impreso) y tu DNI. Cada QR solo es válido una vez.
"""

FAQ_MD = """### ¿Puedo devolver mi entrada?
Sí, mientras el espectáculo no haya empezado y la entrada no se haya usado, desde *Mi cuenta → Mis pedidos*.

### ¿Y si se cancela un concierto?
Se reembolsan automáticamente todos los pedidos.

### ¿Puedo regalar una entrada?
Sí: transfiérela desde *Mis entradas* al email de otra persona registrada. El QR anterior deja de valer.

### ¿Pueden entrar menores?
Sí, acompañados de un adulto, salvo en los espectáculos con edad mínima indicada en su ficha.
"""

TRAVEL_MD = """## En autobús
Líneas urbanas de Algeciras y autobuses interurbanos del Consorcio de Transportes del Campo de Gibraltar.

## En tren
Estación de **Algeciras** (línea Algeciras – Bobadilla), a pocos minutos del recinto.

## En barco
Conexiones diarias desde **Tánger** y **Ceuta** al puerto de Algeciras.

## En coche
Por la A-7 o la A-381. Recomendamos usar los aparcamientos públicos de la ciudad.
"""

LEGAL_MD = """## Aviso legal

Texto legal de ejemplo. **Sustitúyelo desde el panel de administración.**

## Privacidad

Esta web no usa cookies. La sesión se mantiene con un token que se guarda en tu navegador
y se elimina al cerrar sesión.
"""


if __name__ == "__main__":
    seed()
