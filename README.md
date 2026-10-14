# Festival Tickets API · Campo de Gibraltar

Backend en **FastAPI** para gestionar y vender entradas de festivales de música en el Campo de Gibraltar
(Algeciras, La Línea de la Concepción, San Roque, Los Barrios, Tarifa, Jimena y Castellar de la Frontera).

## Puesta en marcha

```bash
cd ~/festival-api
python -m venv .venv && source .venv/bin/activate   # ya creado
pip install -r requirements.txt
cp .env.example .env                                # cambia SECRET_KEY
python seed.py --reset                              # datos de ejemplo
uvicorn app.main:app --reload
```

- Documentación interactiva: http://localhost:8000/docs (Swagger) · http://localhost:8000/redoc
- Tests: `pytest -q`

Usuarios de ejemplo (contraseña `Password123`): `admin@example.com`, `organizer@example.com`,
`staff@example.com`, `customer@example.com`. Código de descuento de ejemplo: `CAMPO10`.

## Pruebas con Postman

En `postman/` están la colección (`festival-api.postman_collection.json`) y el entorno local
(`festival-api.local.postman_environment.json`). Impórtalos en Postman, selecciona el entorno
**Festival API · Local** y ejecuta la colección completa con el **Runner** (las peticiones van encadenadas
y guardan los ids que usan las siguientes). Necesita los datos de ejemplo (`python seed.py --reset`).

Desde terminal: `npx newman run postman/festival-api.postman_collection.json -e postman/festival-api.local.postman_environment.json`

Si cambia la API, edita y vuelve a ejecutar `python postman/generar_coleccion.py`.

## Roles

| Rol | Puede |
|---|---|
| `customer` | Ver catálogo, comprar, pagar, cancelar/reembolsar, nominar y transferir sus entradas |
| `organizer` | Todo lo anterior + crear y gestionar **sus** festivales, cartel, tipos de entrada, descuentos, pedidos, estadísticas y validar entradas de sus festivales |
| `staff` | Validar entradas en la puerta (check-in) |
| `admin` | Todo, incluida la gestión de usuarios y roles |

## Endpoints (prefijo `/api/v1`)

| Área | Endpoints |
|---|---|
| Auth | `POST /auth/register` · `POST /auth/login` (form OAuth2, devuelve JWT) · `GET/PATCH /auth/me` |
| Usuarios (admin) | `GET /users` · `PATCH /users/{id}` (rol, activo) |
| Recintos | `GET /venues?municipality=` · `GET /venues/municipalities` · `GET/POST/PATCH/DELETE /venues/{id}` |
| Artistas | `GET /artists?q=&genre=` · `GET/POST/PATCH/DELETE /artists/{id}` |
| Festivales | `GET /festivals?q=&municipality=&genre=&date_from=&date_to=` · `GET /festivals/{id}` · `GET /festivals/slug/{slug}` · `GET /festivals/manage` · `POST/PATCH/DELETE /festivals/{id}` · `POST /festivals/{id}/publish\|cancel\|finish` |
| Cartel | `GET/POST /festivals/{id}/lineup` · `DELETE /festivals/{id}/lineup/{perf_id}` |
| Tipos de entrada | `GET/POST /festivals/{id}/ticket-types` · `PATCH/DELETE /ticket-types/{id}` |
| Descuentos | `GET/POST /festivals/{id}/discount-codes` · `GET /festivals/{id}/discount-codes/check?code=` · `PATCH /discount-codes/{id}` |
| Pedidos | `POST /orders` · `GET /orders` · `GET /orders/{id}` · `POST /orders/{id}/pay` · `POST /orders/{id}/cancel` · `GET /festivals/{id}/orders` |
| Entradas | `GET /tickets` · `GET /tickets/{id}` · `PATCH /tickets/{id}` (nominar) · `POST /tickets/{id}/transfer` |
| Puerta | `GET /checkin/{code}` (verificar) · `POST /checkin` (validar y marcar como usada) |
| Estadísticas | `GET /festivals/{id}/stats` |

## Reglas de negocio

- **Ciclo del festival**: `draft` → `published` → `finished`, o bien `cancelled`. Los borradores no son públicos
  y solo se publican si tienen algún tipo de entrada activo.
- **Reserva de stock**: al crear un pedido (`pending`) se reservan las entradas durante
  `ORDER_EXPIRATION_MINUTES` (15 por defecto). Si no se paga a tiempo pasa a `expired` y se liberan.
- **Pago simulado**: `POST /orders/{id}/pay`. Una tarjeta acabada en `0000` simula un rechazo (402).
  Aquí se integraría la pasarela real (Stripe, Redsys…).
- Al pagar se emite una entrada por unidad con un **código único** (`code`), que el front debe pintar como QR.
- **Cancelación**: un pedido pendiente se cancela; uno pagado se reembolsa si el festival no ha empezado
  y ninguna entrada se ha usado. Cancelar un festival reembolsa automáticamente todos sus pedidos.
- **Transferencia**: al transferir una entrada a otro usuario se regenera su código (el QR anterior deja de valer).
- **Check-in**: devuelve `accepted` y `reason` (`ok`, `not_found`, `already_used`, `cancelled`, `wrong_festival`)
  para que la app de puerta muestre verde/rojo.
- Los recintos solo admiten los 7 municipios de la comarca.
- Importes en euros como `Decimal` (en JSON se serializan como texto: `"45.00"`).

## Estructura

```
app/
  core/       config, seguridad (JWT + bcrypt), dependencias de auth/roles, utilidades
  db/         motor y sesión de SQLAlchemy
  models/     tablas: users, venues, artists, festivals, performances, ticket_types,
              discount_codes, orders, order_items, tickets
  schemas/    modelos Pydantic de entrada/salida
  routers/    endpoints por área
  services/   lógica de pedidos (reserva, pago, reembolso) y festivales
seed.py       datos de ejemplo del Campo de Gibraltar
tests/        tests del flujo completo
```

## Siguientes pasos sugeridos

- Migraciones con Alembic y PostgreSQL en producción (ahora SQLite y `create_all` al arrancar).
- Pasarela de pago real con webhooks.
- Envío de entradas por email (PDF + QR).
- Asignar el staff a festivales concretos.
