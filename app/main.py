from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401  (registra los modelos en Base.metadata)
from app.core.config import settings
from app.db.bootstrap import ensure_admin, upgrade_schema
from app.db.session import Base, SessionLocal, engine
from app.routers import (
    admin,
    artists,
    auth,
    checkin,
    cms,
    discounts,
    festivals,
    media,
    newsletter,
    orders,
    ticket_types,
    tickets,
    users,
    venues,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    upgrade_schema(engine)
    with SessionLocal() as db:
        ensure_admin(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "API para la gestión y venta de entradas de festivales de música del Campo de Gibraltar: catálogo de festivales, "
        "cartel de artistas, tipos de entrada, pedidos con reserva temporal, pago, entradas con código QR, "
        "transferencias, códigos de descuento, control de acceso en puerta y estadísticas."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Autenticación solo con JWT en la cabecera Authorization: sin cookies ni sesiones
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    # Evita que el navegador "adivine" el tipo de los archivos subidos
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response


for router in (
    auth.router,
    users.router,
    venues.router,
    artists.router,
    festivals.router,
    ticket_types.router,
    discounts.router,
    orders.router,
    tickets.router,
    checkin.router,
    cms.site_router,
    cms.pages_router,
    cms.posts_router,
    media.router,
    newsletter.router,
    admin.router,
):
    app.include_router(router, prefix=settings.api_prefix)

# Archivos subidos desde la biblioteca de medios del panel
app.mount("/uploads", StaticFiles(directory=media.upload_path(), check_dir=False), name="uploads")


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
