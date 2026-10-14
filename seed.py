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
from app.core.config import settings
from app.db.bootstrap import ensure_admin
from app.db.session import Base, SessionLocal, engine
from app.core.utils import utcnow
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
        "sanroque": Venue(name="Alameda Alfonso XI", address="Alameda Alfonso XI s/n",
                          municipality=Municipality.SAN_ROQUE, capacity=6000, latitude=36.2110, longitude=-5.3860),
        "barrios": Venue(name="Parque de los Alcornocales · Área recreativa", address="Ctra. A-381 km 8",
                         municipality=Municipality.LOS_BARRIOS, capacity=5000, latitude=36.1840, longitude=-5.4920),
        "castellar": Venue(name="Patio de Armas del Castillo", address="Castellar Viejo",
                           municipality=Municipality.CASTELLAR, capacity=1200, latitude=36.3170, longitude=-5.4560),
    }
    db.add_all(venues.values())

    artists = [
        Artist(name="Levante Eléctrico", genre="Electrónica", country="España"),
        Artist(name="Los del Peñón", genre="Rock", country="España"),
        Artist(name="Marea Baja", genre="Indie", country="España"),
        Artist(name="Duna Flamenca", genre="Flamenco fusión", country="España"),
        Artist(name="Sur Sound System", genre="Reggae", country="España"),
        Artist(name="Atlas Beats", genre="Electrónica", country="Marruecos"),
        Artist(name="La Bruma", genre="Pop", country="España", bio="Dream pop gaditano de sintetizadores y guitarras brillantes."),
        Artist(name="Poniente Brass Band", genre="Jazz", country="España", bio="Metales, swing y segunda línea de Nueva Orleans con acento andaluz."),
        Artist(name="Noa Calima", genre="Soul", country="Gibraltar", bio="Voz soul con raíces a ambos lados de la Verja."),
        Artist(name="Corcho y Alcornoque", genre="Folk", country="España", bio="Folk de sierra: gaita, bouzouki y coplas del Parque Natural."),
        Artist(name="Kilómetro Cero", genre="Urbano", country="España", bio="Rap, trap y bases latinas desde Los Barrios."),
        Artist(name="Hassan & The Strait", genre="Fusión", country="Marruecos", bio="Gnawa, rock y electrónica cruzando el Estrecho."),
        Artist(name="Las Mareas Vivas", genre="Indie", country="España", bio="Guitarras de playa y estribillos para cantar a coro."),
        Artist(name="Viento de Levante", genre="Flamenco", country="España", bio="Cante y toque flamenco con raíces en la comarca."),
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

    alameda = Festival(
        name="Alameda Pop San Roque", description="Pop e indie bajo los árboles de la Alameda Alfonso XI.",
        genre="Pop", start_date=date(2027, 5, 21), end_date=date(2027, 5, 22),
        status=FestivalStatus.PUBLISHED, venue=venues["sanroque"], organizer=organizer, slug="alameda-pop-san-roque",
    )
    alameda.ticket_types = [
        TicketType(name="Abono 2 días", price=Decimal("38.00"), quantity_total=4500),
        TicketType(name="Entrada de día", price=Decimal("22.00"), quantity_total=1500),
    ]
    alameda.performances = [
        Performance(artist=artists[6], stage="Escenario Alameda", start_time=datetime(2027, 5, 21, 22), end_time=datetime(2027, 5, 21, 23, 30)),
        Performance(artist=artists[12], stage="Escenario Alameda", start_time=datetime(2027, 5, 22, 21, 30), end_time=datetime(2027, 5, 22, 23)),
        Performance(artist=artists[2], stage="Escenario Alameda", start_time=datetime(2027, 5, 22, 23, 30), end_time=datetime(2027, 5, 23, 1)),
    ]

    alcornocales = Festival(
        name="Alcornocales Folk & Raíz", description="Folk, músicas del mundo y talleres en pleno Parque Natural.",
        genre="Folk", start_date=date(2027, 9, 10), end_date=date(2027, 9, 12),
        status=FestivalStatus.PUBLISHED, venue=venues["barrios"], organizer=organizer, slug="alcornocales-folk-raiz",
    )
    alcornocales.ticket_types = [
        TicketType(name="Abono 3 días", price=Decimal("55.00"), quantity_total=3500),
        TicketType(name="Abono + acampada", description="Zona de acampada señalizada", price=Decimal("75.00"), quantity_total=800),
    ]
    alcornocales.performances = [
        Performance(artist=artists[9], stage="Claro del Bosque", start_time=datetime(2027, 9, 10, 20), end_time=datetime(2027, 9, 10, 21, 30)),
        Performance(artist=artists[11], stage="Claro del Bosque", start_time=datetime(2027, 9, 11, 22), end_time=datetime(2027, 9, 11, 23, 30)),
        Performance(artist=artists[13], stage="Claro del Bosque", start_time=datetime(2027, 9, 12, 21), end_time=datetime(2027, 9, 12, 22, 30)),
    ]

    jazz = Festival(
        name="Noches de Jazz en La Línea", description="Jazz, soul y swing junto al mar en La Línea de la Concepción.",
        genre="Jazz", start_date=date(2027, 7, 30), end_date=date(2027, 7, 31),
        status=FestivalStatus.PUBLISHED, venue=venues["linea"], organizer=organizer, slug="noches-de-jazz-la-linea",
    )
    jazz.ticket_types = [
        TicketType(name="Abono 2 noches", price=Decimal("40.00"), quantity_total=5000),
        TicketType(name="Mesa VIP (4 pax)", description="Mesa reservada junto al escenario", price=Decimal("180.00"), quantity_total=40, max_per_order=2),
    ]
    jazz.performances = [
        Performance(artist=artists[7], stage="Escenario del Mar", start_time=datetime(2027, 7, 30, 22), end_time=datetime(2027, 7, 30, 23, 30)),
        Performance(artist=artists[8], stage="Escenario del Mar", start_time=datetime(2027, 7, 31, 22), end_time=datetime(2027, 7, 31, 23, 30)),
    ]

    db.add_all([estrecho, bahia, castillo, alameda, alcornocales, jazz])
    db.flush()
    db.add(DiscountCode(festival_id=estrecho.id, code="CAMPO10", percent_off=10, max_uses=200))
    db.commit()
    admin = ensure_admin(db)
    seed_cms(db, admin.id, estrecho.id)

    print(f"Administrador del panel: usuario '{settings.admin_username}' / contraseña '{settings.admin_password}'")
    print("Datos de ejemplo cargados. Usuarios (contraseña:", PASSWORD + "):")
    for user in users.values():
        print(f"  - {user.email:32} rol={user.role.value}")


def seed_cms(db, author_id: int, featured_festival_id: int) -> None:
    """Páginas y noticias de ejemplo para la web pública."""
    from app.services.cms import get_site_config
    from app.schemas.cms import SiteSettings

    config = get_site_config(db)
    config.data = SiteSettings(
        featured_festival_id=featured_festival_id,
        announcement="Ya a la venta los abonos de la temporada 2027 · Código CAMPO10 en el Estrecho Sound",
        social={"instagram": "https://instagram.com/", "facebook": "https://facebook.com/",
                "youtube": "https://youtube.com/", "spotify": "https://spotify.com/"},
    ).model_dump()

    now = utcnow()
    published = {"status": ContentStatus.PUBLISHED, "published_at": now, "author_id": author_id}
    db.add_all([
        Page(title="Información", slug="informacion", show_in_menu=True, menu_order=1,
             excerpt="Todo lo que necesitas saber antes de venir.", **published, content=INFO_MD),
        Page(title="Preguntas frecuentes", slug="preguntas-frecuentes", show_in_menu=True, menu_order=2,
             excerpt="Entradas, accesos, menores, devoluciones...", **published, content=FAQ_MD),
        Page(title="Cómo llegar", slug="como-llegar", show_in_menu=True, menu_order=3,
             excerpt="Autobús, tren, coche y barco.", **published, content=TRAVEL_MD),
        Page(title="Aviso legal y privacidad", slug="aviso-legal", **published,
             content="## Aviso legal\n\nTexto legal de ejemplo. **Sustitúyelo desde el panel de administración.**"),
        Post(title="Arranca la temporada 2027 en el Campo de Gibraltar", slug="arranca-temporada-2027",
             excerpt="Seis festivales, siete municipios y más de cuarenta conciertos.", **published,
             content="La temporada 2027 llega con **seis festivales** repartidos por la comarca. "
                     "Del pop de la Alameda de San Roque al folk del Parque de los Alcornocales.\n\n"
                     "Los abonos ya están a la venta en esta web."),
        Post(title="Estrecho Sound confirma a Atlas Beats", slug="estrecho-sound-atlas-beats",
             excerpt="El productor marroquí cerrará la noche del viernes en Tarifa.", festival_id=featured_festival_id,
             **published, content="**Atlas Beats** se suma al cartel del Estrecho Sound Festival en la playa de Los Lances."),
        Post(title="Nueva zona de acampada en Alcornocales Folk", slug="acampada-alcornocales",
             excerpt="Plazas limitadas con el abono + acampada.", **published,
             content="Este año habilitamos una zona de acampada señalizada a 5 minutos del escenario."),
    ])
    db.commit()


INFO_MD = """## Entradas

Las entradas se compran **solo en esta web**. Tras el pago recibirás tus entradas con un **código QR**
en el apartado *Mis entradas*. Puedes nominarlas o transferirlas a otra persona registrada.

## Acceso

- Lleva el QR en el móvil (o impreso) y tu DNI.
- Cada QR solo es válido una vez.
- Consulta la edad mínima de cada festival en su ficha.

## Accesibilidad

Todos los recintos cuentan con plataforma reservada para personas con movilidad reducida.
"""

FAQ_MD = """### ¿Puedo devolver mi entrada?
Sí, mientras el festival no haya empezado y la entrada no se haya usado, desde *Mis pedidos*.

### ¿Y si se cancela el festival?
Se reembolsan automáticamente todos los pedidos.

### ¿Puedo regalar una entrada?
Sí: transfiérela desde *Mis entradas* al email de otra persona registrada. El QR anterior deja de valer.

### ¿Pueden entrar menores?
Depende del festival. La edad mínima aparece en la ficha de cada uno.
"""

TRAVEL_MD = """## En autobús
Líneas interurbanas del Consorcio de Transportes del Campo de Gibraltar entre todos los municipios.

## En tren
Estación de **Algeciras** (línea Algeciras – Bobadilla) y estación de **San Roque – La Línea**.

## En barco
Conexiones diarias desde **Tánger** y **Ceuta** al puerto de Algeciras y desde Tánger a Tarifa.

## En coche
A-7 y A-381. Habilitamos aparcamientos disuasorios en cada recinto.
"""


if __name__ == "__main__":
    seed()
