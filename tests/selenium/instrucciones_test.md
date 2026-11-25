# Pruebas Selenium — Las Palomas Festival

Suite de pruebas **funcionales** y de **estrés/carga** con Selenium para la SPA
`https://festival-api-aucn.onrender.com/` (React + Vite; consume la API en
`https://festival-apii.onrender.com/api/v1`).

## Requisitos
- `chromium` + `chromedriver` (en el sistema: `/usr/bin/chromium`, `/usr/bin/chromedriver`)
- Python 3.12+ con `selenium`

```bash
# entorno (con uv o venv estándar)
python -m venv .venv && . .venv/bin/activate
pip install selenium
```

## Ejecutar
```bash
# Funcionales (14 tests)
python functional_tests.py
python functional_tests.py --headful          # ver el navegador

# Estrés (por defecto 6 workers × 8 cargas)
python stress_test.py
python stress_test.py --workers 10 --iters 6  # más presión

# Anti-DDoS / abuso (detección de rate-limiting; HTTP, no Selenium)
python ddos_protection_test.py
python ddos_protection_test.py --scale 1.5    # más volumen (con cabeza)
```

Salidas: `resultados_funcional.json`, `resultados_estres.json`, `resultados_ddos.json`.

## Qué cubre lo funcional
Carga de home, errores de consola, navegación del menú, filtros y buscador de
Programación, tarjetas de Artistas → detalle, lista/detalle de Noticias, Plazas,
login con credenciales inválidas, validación de registro y newsletter, páginas
estáticas `/p/:slug`, página 404 y deep-link (fallback SPA).

> No contamina datos: no crea cuentas ni suscripciones reales; login/registro/
> newsletter se prueban con credenciales inválidas y validación de formulario.

## Qué mide el estrés
N navegadores headless concurrentes cargan en bucle un set de páginas reales
(que disparan llamadas a la API). Reporta throughput, errores y percentiles
(p50/p90/p95/p99) de latencia de reloj de pared hasta contenido usable, más el
Navigation Timing del navegador. Incluye warm-up (Render free hiberna).

## Qué comprueba lo anti-DDoS (`ddos_protection_test.py`)
Ráfagas HTTP acotadas para detectar defensas: presencia de Cloudflare,
rate-limiting declarado, throttle (429/503) bajo ráfaga en endpoints ligero y de
BD, y protección del login frente a fuerza bruta. Pensado también como **test de
regresión**: debe empezar a ver 429 cuando se aplique rate-limiting.
