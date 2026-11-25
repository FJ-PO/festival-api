# Informe de pruebas y DevOps — Las Palomas Festival

**Proyecto:** festival-api · **Web pública:** `https://festival-api-aucn.onrender.com/`
**Fecha del informe:** 2026-11-19
**Autor:** QA / Selenium 4 + Chromium headless
**Repositorio:** https://github.com/FJ-PO/festival-api (rama `main`)

---

## 1. Resumen ejecutivo

Se han ejecutado **pruebas funcionales** y de **estrés/carga** con Selenium sobre
la web pública de Las Palomas Festival, y se ha auditado el **despliegue (DevOps)**
en Render de los tres servicios del proyecto.

| Área | Veredicto |
|------|-----------|
| **Funcional** | ✅ 14/14 pruebas superadas. Sin errores de JavaScript relevantes. |
| **Estrés** | ✅ 0 errores / 0 timeouts bajo carga concurrente; el servicio es **estable** pero **no escala** (instancia única). |
| **DevOps** | 🟡 Despliegue correcto y seguro en lo esencial (TLS/HSTS/CORS), con mejoras pendientes de **caché de estáticos**, **persistencia (Postgres)** y **cabeceras de seguridad**. |

**Riesgos principales:** datos en SQLite efímero (se borran en cada redeploy),
**login sin rate-limit** (fuerza bruta) y **DoS de capa 7** por falta de
rate-limiting de aplicación, assets hasheados sin caché de larga duración, y cold
start del plan gratuito.

---

## 2. Alcance y entorno

- **Objeto de prueba:** SPA React/Vite servida como *Static Site* en Render, que
  consume la API FastAPI en `https://festival-apii.onrender.com/api/v1`.
- **Herramientas:** Selenium 4.53, Chromium 155 headless, Python 3.12.
- **Tipo de pruebas:** caja negra, contra el entorno de **producción**.
- **Ética de datos:** no se crearon cuentas ni suscripciones reales; login,
  registro y newsletter se validaron con credenciales inválidas y validación de
  formulario. La carga se limitó a ≤10 navegadores concurrentes para no degradar
  un servicio propio en plan gratuito.

---

## 3. Arquitectura y DevOps

### 3.1 Topología de servicios (Render)

| Parte | Carpeta | Tipo Render | URL | Estado |
|-------|---------|-------------|-----|:------:|
| API (FastAPI, Docker) | `app/` | Web Service `festival-apii` | https://festival-apii.onrender.com (`/docs`) | 🟢 200 |
| Web pública (React/Vite) | `frontend/` | Static Site `festival-api` | https://festival-api-aucn.onrender.com | 🟢 200 |
| Panel admin (React/Vite) | `admin/` | Static Site `festival-api-paneladmin` | https://festival-api-paneladmin.onrender.com | 🟢 200 |

Operativos de forma continua desde el 29/10/2026.

### 3.2 Pipeline de build y despliegue
- **Estáticos:** `Root Directory` = `frontend`/`admin`, build `npm install && npm run build`,
  publicación de `dist/`, con **regla Rewrite `/*` → `/index.html`** (imprescindible
  para que el deep-link a rutas como `/login` no dé 404 — **verificado OK** en las pruebas).
- **API:** imagen Docker; el `Dockerfile` ejecuta `seed.py` (carga la programación de
  ejemplo) antes de arrancar `uvicorn`.
- Variable build-time `VITE_API_URL=https://festival-apii.onrender.com` inyectada en los
  estáticos; `CORS_ORIGINS` en la API apunta a las dos webs.

### 3.3 Red, CDN y entrega (medido)
| Aspecto | Observación |
|---------|-------------|
| CDN / proxy | **Cloudflare** delante de los tres servicios (`server: cloudflare`). |
| Protocolo | **HTTP/2** y **HTTP/3** disponible (`alt-svc: h3`). |
| Compresión | **Brotli** en los assets (`content-encoding: br`). ✅ |
| TLS / HSTS | `strict-transport-security: max-age=315360000; includeSubdomains; preload`. ✅ fuerte. |
| Origen API | `x-render-origin-server: uvicorn`; respuestas `cf-cache-status: DYNAMIC`. |

### 3.4 Seguridad
- **CORS** correctamente **restringido** al origen del front (no `*`):
  `access-control-allow-origin: https://festival-api-aucn.onrender.com`. ✅
- Cabeceras de seguridad en la web:

| Cabecera | Estado |
|----------|:------:|
| `strict-transport-security` | ✅ presente |
| `x-content-type-options: nosniff` | ✅ presente |
| `x-frame-options` | ❌ ausente |
| `content-security-policy` | ❌ ausente |
| `referrer-policy` | ❌ ausente |
| `permissions-policy` | ❌ ausente |

- La documentación interactiva de la API (`/docs`) y `/openapi.json` son
  **públicas** (200). Aceptable en un proyecto académico, pero expone toda la
  superficie de la API en producción.

### 3.5 Persistencia (riesgo conocido)
- La API usa **SQLite en disco efímero** → **los datos se borran en cada redeploy**.
  Las imágenes de `uploads/` también son efímeras.
- El código ya tiene soporte para **PostgreSQL** (`psycopg2-binary`, normalización
  `postgres://`→`postgresql://`, `pool_pre_ping`); solo falta crear el Postgres en
  Render y fijar `DATABASE_URL`.

---

## 4. Pruebas funcionales — 14/14 ✅

**Metodología:** un navegador reutilizado entre casos, esperas explícitas
(`WebDriverWait`) sobre el DOM hidratado de React. Script: `functional_tests.py`.

| # | Prueba | Resultado |
|---|--------|-----------|
| 1 | Home: título, nav y secciones | ✅ |
| 2 | Sin errores SEVERE en consola | ✅ (solo favicon, ignorado) |
| 3 | Navegación del menú (4 secciones) | ✅ |
| 4 | Programación: filtro por plaza | ✅ 22 → 8 noches (Algeciras) |
| 5 | Programación: buscador de artista | ✅ 2 resultados "Melendi" |
| 6 | Artistas → detalle del festival | ✅ 17 artistas |
| 7 | Noticias: lista y detalle | ✅ 4 noticias |
| 8 | Plazas + filtro por municipio | ✅ 3 plazas |
| 9 | Login rechaza credenciales inválidas | ✅ |
| 10 | Registro valida contraseñas distintas | ✅ |
| 11 | Newsletter valida email (`required`) | ✅ |
| 12 | Páginas estáticas `/p/:slug` | ✅ 4 páginas |
| 13 | Página 404 estable | ✅ |
| 14 | Deep-link SPA (fallback `index.html`) | ✅ |

Duración total ≈ 26 s. La aplicación renderiza datos reales de la API y la
navegación cliente funciona sin recargas ni fallos.

---

## 5. Pruebas de estrés / carga

**Metodología:** N navegadores Chromium headless concurrentes recorren en bucle
un conjunto de páginas reales (que disparan llamadas a la API). Se mide la
latencia de **reloj de pared hasta contenido usable** (`#root` poblado con datos
de la API) y el `loadEventEnd` del Navigation Timing. Incluye *warm-up*.
Script: `stress_test.py`.

### 5.1 Escenarios

| Escenario | Cargas | Errores | Throughput | p50 | p90 | p95 | p99 | max |
|-----------|-------:|--------:|-----------:|----:|----:|----:|----:|----:|
| 6 workers × 8  | 48 | **0** | 1,71 /s | 1 550 ms | 5 194 ms | 6 098 ms | 10 967 ms | 11 111 ms |
| 10 workers × 6 | 60 | **0** | 1,60 /s | 2 876 ms | 9 946 ms | 12 614 ms | 13 795 ms | 14 550 ms |

*Navigation Timing (shell estático): p50 ≈ 230–320 ms, p95 ≈ 2,3–3,9 s.*

### 5.2 Latencia por página (p95, escenario 10 workers)

| Página | p50 | p95 |
|--------|----:|----:|
| `/programacion` | 4 196 ms | 13 870 ms |
| `/` (home) | 7 542 ms | 12 558 ms |
| `/artistas` | 3 136 ms | 10 447 ms |
| `/plazas` | 2 286 ms | 7 899 ms |
| `/noticias` | 2 616 ms | 7 531 ms |
| `/festivales/:slug` | 2 368 ms | 7 209 ms |
| `/p/:slug` (estática) | 2 462 ms | 7 461 ms |

### 5.3 Análisis
- **Robustez:** 0 errores y 0 timeouts en ambos escenarios → el servicio **no se
  cae** bajo presión y devuelve contenido correcto siempre.
- **Saturación:** al pasar de 6 a 10 workers el **throughput no sube**
  (1,71 → 1,60 /s) y la latencia casi se **duplica**. Es el patrón de una
  **instancia única modesta** (Render free ≈ 1 vCPU / 512 MB, baja concurrencia):
  el cuello de botella es el cómputo/concurrencia del backend, no la entrega del
  estático (que Cloudflare sirve en ~230 ms).
- **Páginas pesadas:** `/` y `/programacion` son las más lentas porque cargan el
  cartel completo + próximas noches + noticias (más datos de API por render).

### 5.4 Pruebas anti-DDoS / abuso

Ráfagas HTTP controladas (volumen acotado, servicio propio) para comprobar qué
**defensas** existen frente a DDoS y abuso. Script: `ddos_protection_test.py`.

| Prueba | Carga | Resultado | ¿Throttle (429/503)? |
|--------|-------|-----------|:--------------------:|
| Borde / cabeceras | — | **Cloudflare** delante (`cf-ray`); API sin cabeceras `RateLimit-*` | — |
| A) Ráfaga `/health` | 150 req / 30 conc | 150×200 a **104 req/s** | ❌ No |
| B) Ráfaga `/api/v1/festivals` (BD) | 100 req / 20 conc | 100×200 pero **3,9 req/s**, p95 6,8 s | ❌ No |
| C) Abuso de login | 40 logins fallidos / 10 conc | 40×401 a **44 intentos/s** | ❌ No |
| D) Spoofing `X-Forwarded-For` | 1 req | 200 con y sin XFF (informativo) | — |

**Checklist de defensas:**

| Defensa | Estado |
|---------|:------:|
| Cloudflare (DDoS L3/L4 + challenge de bots) | ✅ |
| Rate-limit declarado en la API (`RateLimit-*`/`Retry-After`) | ❌ |
| Throttle bajo ráfaga en endpoint ligero | ❌ |
| Autoprotección del backend bajo ráfaga | ❌ |
| Rate-limit / lockout en login | ❌ |

**Lectura:** Cloudflare cubre el DDoS **volumétrico** (capa 3/4), pero **no hay
ninguna defensa de capa de aplicación**:
- El **login no limita intentos** → fuerza bruta / credential stuffing viables.
- `/api/v1/festivals` cae a **~4 req/s** con solo 20 conexiones: un **único
  atacante** puede provocar un **DoS de capa 7** saturando el backend sin volumen
  (Cloudflare no lo ve como ataque porque son peticiones "legítimas").

### 5.5 Estrés local vs producción (API)

Para separar "lentitud de infraestructura" de "lentitud de código", se repitió la
ráfaga sobre `/api/v1/festivals` contra la **API local** (uvicorn en `:8000`, sin
red ni Cloudflare) y contra **producción**. Script: `stress_local_vs_prod.py`.

| Métrica (100 req / 20 conc) | Local | Producción |
|-----------------------------|------:|-----------:|
| Throughput | **11,0 req/s** | 3,4 req/s |
| Latencia p50 | 1 656 ms | 5 292 ms |
| Latencia p95 | 3 011 ms | 9 283 ms |
| Errores | 0 | 0 |

**Lectura (clave):**
- Producción es **~3,2× más lenta** que local → ese factor es **infraestructura**
  (instancia Render free + red + Cloudflare).
- **Pero local también es lento**: con solo 20 conexiones no pasa de ~11 req/s y
  la p50 ya es 1,6 s. Es decir, **buena parte del coste está en el propio
  endpoint**, no en Render: `/api/v1/festivals` es pesado (probable **N+1** al
  cargar por cada noche su `venue`, `organizer` y calcular `price_from`), y con
  **SQLite + 1 worker** las peticiones se serializan.
- **Conclusión:** la lentitud es *mitad infraestructura, mitad código/consulta*.
  Optimizar la consulta subiría el techo **en ambos** despliegues.

> Caveat: no es comparación en igualdad de condiciones (local = esta máquina sin
> red; prod = Render free + red + CDN). Justamente por eso aísla el peso de cada
> factor.

---

## 6. Hallazgos priorizados

| # | Severidad | Hallazgo | Evidencia |
|---|:---------:|----------|-----------|
| H1 | 🔴 Alta | **Datos no persistentes:** SQLite en disco efímero; se pierden en cada redeploy | Config + memoria del proyecto |
| H7 | 🔴 Alta | **Login sin rate-limit:** 40 intentos fallidos → 0 bloqueos; fuerza bruta / credential stuffing | §5.4-C |
| H8 | 🟠 Media | **DoS de capa 7:** `/api/v1/festivals` cae a ~4 req/s con 20 conexiones; sin rate-limit un solo atacante satura el backend | §5.4-B |
| H2 | 🟠 Media | **No escala con la concurrencia:** throughput plano y p95 >12 s a 10 workers | §5.1 |
| H9 | 🟠 Media | **Endpoint `/api/v1/festivals` lento incluso en local** (~11 req/s, p50 1,6 s): probable N+1 + SQLite + 1 worker | §5.5 |
| H3 | 🟠 Media | **Assets hasheados sin caché larga:** `cache-control: public, max-age=0, s-maxage=300` en `index-*.js` (deberían ser inmutables) | cabeceras del asset |
| H4 | 🟡 Baja | **Faltan cabeceras de seguridad:** sin CSP, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` | §3.4 |
| H5 | 🟡 Baja | **Cold start** del plan gratuito tras hibernación | §3.3 / warm-up |
| H6 | ⚪ Info | `/docs` y `/openapi.json` públicos en producción | §3.4 |

---

## 7. Recomendaciones

0. **(H7/H8) Añadir rate-limiting de aplicación** (lo más urgente para DDoS/abuso):
   - En la API: `slowapi` o `fastapi-limiter` (+ Redis) con límites por IP; límite
     estricto en `/auth/login` (p. ej. 5/min por IP) y lockout/CAPTCHA tras fallos.
   - En Cloudflare: **Rate Limiting Rules** y **Bot Fight Mode** para `/api/v1/*`.
   - `ddos_protection_test.py` sirve de **test de regresión**: debe pasar a ver 429
     en el login y en las ráfagas una vez aplicada la mitigación.
1. **(H1) Migrar a PostgreSQL** en Render y fijar `DATABASE_URL` (el código ya lo
   soporta). Para `uploads/`, usar disco persistente o almacenamiento tipo S3.
2. **(H3) Cachear estáticos hasheados** con `Cache-Control: public, max-age=31536000, immutable`.
   Los nombres llevan hash de contenido, así que es seguro y reduce la p95 de las
   páginas pesadas. Dejar `index.html` con `max-age=0`.
3. **(H2) Subir el techo de concurrencia:** plan con ≥1 vCPU real o varios workers
   de uvicorn/gunicorn; **cachear** las respuestas de catálogo (festivales,
   artistas, plazas cambian poco) en memoria/CDN.
4. **(H2 front) Reducir time-to-content** de la home: lazy-load de secciones no
   críticas y paginación/`limit` en las listas largas.
8. **(H9) Optimizar `/api/v1/festivals`:** carga ansiosa (`selectinload`/`joinedload`)
   de `venue`/`organizer` para evitar N+1, precálculo o anotación de `price_from`,
   y varios workers de uvicorn. Con Postgres (H1) desaparece la serialización de
   SQLite. Mejora el techo tanto en local como en producción.
5. **(H4) Añadir cabeceras de seguridad** (CSP adaptada a la SPA, `X-Frame-Options:
   DENY`, `Referrer-Policy: strict-origin-when-cross-origin`).
6. **(H5) Evitar hibernación** con un ping programado o un plan sin cold start.
7. **(H6)** Valorar proteger/ocultar `/docs` en producción.

---

## 8. Anexos — reproducir

```bash
cd ~/Projects/festival-selenium
python -m venv .venv && . .venv/bin/activate && pip install selenium
python functional_tests.py                   # 14 pruebas funcionales
python stress_test.py --workers 6 --iters 8  # estrés (Selenium)
python ddos_protection_test.py               # anti-DDoS / abuso (HTTP)

# Estrés local vs producción (requiere la API local en :8000)
#   (desde la raíz del repo, en otra terminal:)
#   uvicorn app.main:app --port 8000
python stress_local_vs_prod.py --n 100 --conc 20
```

**Artefactos:** `functional_tests.py`, `stress_test.py`, `ddos_protection_test.py`,
`stress_local_vs_prod.py`, `instrucciones_test.md`, `resultados_funcional.json`,
`resultados_estres.json`, `resultados_estres_10w.json`, `resultados_ddos.json`,
`resultados_local_vs_prod.json`.
