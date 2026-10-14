from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  (registra los modelos en Base.metadata)
from app.core.config import settings
from app.db.session import Base, engine
from app.routers import artists, auth, checkin, discounts, festivals, orders, ticket_types, tickets, users, venues


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
