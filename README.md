# Las Palomas Festival · Algeciras

Plataforma completa para el ciclo de conciertos y humor **Las Palomas Festival**, repartido entre tres plazas de toros del
Campo de Gibraltar: **Algeciras**, **La Línea** y **Los Barrios**. Hay una noche cada sábado, rotando de plaza, de mayo a agosto de
2027, y algunos viernes en los que un artista repite en otra plaza.

| Parte | Carpeta | Tecnología | Puerto |
|---|---|---|---|
| API REST | `app/` | FastAPI · SQLAlchemy 2 · Pydantic 2 · JWT | 8000 |
| Web pública | `frontend/` | React 19 · Vite · TypeScript | 5173 |
| Panel de administración | `admin/` | React 19 · Vite · TypeScript | 5174 |

Cartel de ejemplo: Melendi, Niña Pastori, Dellafuente, India Martínez, Lola Índigo, Maka, Manuel Carrasco, Ana Mena,
Andy & Lucas, Estopa, Antonio José, Rels B y las noches de humor de Dani Rovira, Los Morancos, Leo Harlem, Manu Sánchez y
Comandante Lara & Cía. Melendi, Niña Pastori, Dellafuente, Maka y Dani Rovira tienen doble fecha en dos plazas distintas.

## Puesta en marcha

Requisitos: Python 3.12 o superior y Node 20 o superior.

```bash
# 1. API
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # cambia SECRET_KEY y ADMIN_PASSWORD en producción
python seed.py --reset          # carga la programación de ejemplo (borra la BD)
uvicorn app.main:app --reload   # http://localhost:8000/docs

# 2. Web pública
cd frontend && npm install && npm run dev    # http://localhost:5173

# 3. Panel de administración
cd admin && npm install && npm run dev       # http://localhost:5174
```

En desarrollo, Vite redirige `/api` y `/uploads` al backend, así que no hace falta configurar CORS. Para apuntar a otra API:
`VITE_BACKEND=http://host:puerto npm run dev`. En producción se usa `VITE_API_URL` (URL pública de la API) y, en el
panel, `VITE_PUBLIC_SITE` (URL de la web, para los enlaces de "Ver en la web").

### Accesos

| Dónde | Usuario | Contraseña | Rol |
|---|---|---|---|
| Panel | `admin` | `admin123` | Administrador (se crea solo al arrancar la API) |
| Web / panel | `organizer@example.com` | `Password123` | Organizador |
| Panel (puerta) | `staff@example.com` | `Password123` | Personal de puerta |
| Web | `customer@example.com` | `Password123` | Cliente |

Código de descuento de ejemplo: `PALOMAS10` (Melendi en Algeciras, 8 de mayo). Pago simulado: una tarjeta que termina en `0000` se rechaza.

> ⚠️ `admin` / `admin123` es la cuenta de desarrollo. En producción define `ADMIN_PASSWORD` en el `.env` **antes del primer
> arranque**, o cambia la contraseña desde *Mi perfil* en el panel.

## Autenticación: JWT, sin cookies ni sesiones

```
Cliente                                   API
  │ POST /api/v1/auth/login                │
  │ username=admin&password=…  ──────────► │ verifica el hash bcrypt
  │ ◄────────── { access_token, expires_in, user }   (sin Set-Cookie)
  │                                         │
  │ GET /api/v1/admin/dashboard             │
  │ Authorization: Bearer eyJhbGciOi… ────► │ valida firma HS256 + exp, carga el usuario y comprueba su rol
```

- El token es un **JWT HS256** con `sub` (id del usuario), `role`, `iat` y `exp`. Caduca a los
  `ACCESS_TOKEN_EXPIRE_MINUTES` (60 por defecto).
- **No hay cookies ni sesiones de servidor**. La API es *stateless*: CORS con `allow_credentials=False`, y los
  frontends hacen `fetch` con `credentials: 'omit'` y envían el token en la cabecera `Authorization`.
- Cada frontend guarda su token en `localStorage` con su propia clave (`festival.token` en la web y
  `festival.admin.token` en el panel). Lo borra al cerrar sesión, al recibir un `401` o al llegar a su `exp`.
- El login acepta **email o nombre de usuario**. Al panel solo entran los roles `admin`, `organizer` y `staff`, y el menú
  se adapta a cada rol. La autorización real la hace siempre la API.

## Panel de administración

Equivalente a un WordPress hecho a medida:

- **Escritorio**: ingresos, entradas vendidas y validadas, noches por estado, ventas de 30 días y últimos pedidos.
- **Noches**: crear, editar, publicar, finalizar o cancelar (con reembolso automático). Cada noche tiene pestañas de zonas de
  entrada (Pista, Grada, Front Stage…), cartel y horarios, descuentos, pedidos y estadísticas.
- **Artistas** y **recintos**.
- **Páginas** y **noticias**: editor Markdown con barra de herramientas y vista previa, borradores, slug, menú e imagen destacada.
- **Medios**: biblioteca de imágenes con subida por arrastre.
- **Usuarios**, **newsletter** (exportación CSV), **control de acceso** en puerta y **apariencia**: textos de portada, banda de
  avisos, color de marca, redes sociales y pie.

## API (prefijo `/api/v1`)

Documentación interactiva en `/docs` (Swagger) y `/redoc`.

| Área | Endpoints |
|---|---|
| Auth | `POST /auth/register` · `POST /auth/login` · `GET/PATCH /auth/me` |
| Usuarios (admin) | `GET /users` · `POST /users` · `PATCH /users/{id}` |
| Recintos | `GET /venues` · `GET /venues/municipalities` · `GET/POST/PATCH/DELETE /venues/{id}` |
| Artistas | `GET /artists` · `GET/POST/PATCH/DELETE /artists/{id}` |
| Festivales (noches) | `GET /festivals` · `GET /festivals/{id}` · `GET /festivals/slug/{slug}` · `GET /festivals/manage` · `POST/PATCH/DELETE` · `POST /{id}/publish\|cancel\|finish` |
| Cartel | `GET/POST /festivals/{id}/lineup` · `DELETE /festivals/{id}/lineup/{perf_id}` |
| Tipos de entrada | `GET/POST /festivals/{id}/ticket-types` · `PATCH/DELETE /ticket-types/{id}` |
| Descuentos | `GET/POST /festivals/{id}/discount-codes` · `GET …/check?code=` · `PATCH /discount-codes/{id}` |
| Pedidos | `POST /orders` · `GET /orders` · `GET /orders/{id}` · `POST /orders/{id}/pay\|cancel` · `GET /festivals/{id}/orders` |
| Entradas | `GET /tickets` · `GET/PATCH /tickets/{id}` · `POST /tickets/{id}/transfer` |
| Puerta | `GET /checkin/{code}` · `POST /checkin` |
| Estadísticas | `GET /festivals/{id}/stats` · `GET /admin/dashboard` |
| CMS | `GET/PUT /site` · `/pages` y `/posts` (`GET` público, `GET /manage`, `GET /slug/{slug}`, `POST/PATCH/DELETE`) |
| Medios | `GET/POST /media` · `PATCH/DELETE /media/{id}` (los archivos se sirven en `/uploads/…`) |
| Newsletter | `POST /newsletter` (público) · `GET /newsletter` · `DELETE /newsletter/{id}` |

### Reglas de negocio

- **Ciclo de una noche**: `draft` → `published` → `finished`, o bien `cancelled`. Solo se publica si tiene algún tipo de
  entrada activo. Cancelarla reembolsa todos sus pedidos.
- **Reserva**: al crear el pedido se reservan las entradas durante `ORDER_EXPIRATION_MINUTES` (15 por defecto).
- **Entradas**: una por unidad, cada una con un código único que se pinta como QR. Al transferir una entrada se genera un código
  nuevo.
- **Check-in**: devuelve `accepted` y `reason` (`ok`, `not_found`, `already_used`, `cancelled`, `wrong_festival`).
- **Subidas**: se comprueba la firma real del archivo (JPG, PNG, GIF, WEBP o PDF; SVG no), máximo 8 MB, nombre aleatorio y
  cabecera `X-Content-Type-Options: nosniff`.

## Estructura

```
app/
  core/       configuración, seguridad (JWT + bcrypt) y dependencias de auth/roles
  db/         sesión de SQLAlchemy y arranque (migración ligera + administrador inicial)
  models/     tablas: usuarios, recintos, artistas, festivales, entradas, pedidos, CMS (site_config, pages, posts, media, subscribers)
  schemas/    modelos Pydantic de entrada y salida
  routers/    endpoints por área (incluidos cms, media, newsletter y admin)
  services/   lógica de pedidos, festivales y CMS
frontend/     web pública (React)
admin/        panel de administración (React)
postman/      colección de Postman y entorno local
tests/        tests de la API (pytest)
seed.py       programación de ejemplo de Las Palomas Festival
```

## Tests y calidad

```bash
pytest -q                                   # API
cd frontend && npm run lint && npm run build
cd admin && npm run lint && npm run build
```

Cada push y cada pull request ejecutan lo mismo en GitHub Actions (`.github/workflows/ci.yml`).

## Flujo de trabajo con Git

Ramas, convenciones de commits y cómo abrir un pull request: [CONTRIBUTING.md](CONTRIBUTING.md).

## Siguientes pasos

- Migraciones con Alembic y PostgreSQL en producción (ahora SQLite y `create_all` con un ajuste ligero al arrancar).
- Pasarela de pago real (Redsys o Stripe) con webhooks.
- Envío de las entradas por email (PDF con QR).
- Lector de QR por cámara en el control de acceso.
- Rate limiting en `/auth/login` y rotación de tokens con *refresh token*.
