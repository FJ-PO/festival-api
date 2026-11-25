#!/usr/bin/env python3
"""
Pruebas FUNCIONALES con Selenium para Las Palomas Festival (SPA React).
Web: https://festival-api-aucn.onrender.com/

Diseño:
  - Un solo navegador Chromium headless reutilizado entre tests (rápido).
  - Esperas explícitas (WebDriverWait) en vez de sleeps fijos -> robusto.
  - No contamina datos: login con credenciales inválidas, registro/newsletter
    solo valida (contraseñas que no coinciden, email vacío). No crea cuentas.
  - Revisa errores graves de consola del navegador en la home.

Salida: informe por consola + resultados.json
Uso:    python functional_tests.py [--base URL] [--headful]
"""
import argparse, json, sys, time, traceback
from datetime import datetime, timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "https://festival-api-aucn.onrender.com"
TIMEOUT = 25

results = []

def make_driver(headful=False):
    opts = Options()
    if not headful:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1366,900")
    opts.add_argument("--lang=es-ES")
    opts.binary_location = "/usr/bin/chromium"
    d = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)
    d.set_page_load_timeout(60)
    return d

def wait(driver):
    return WebDriverWait(driver, TIMEOUT)

def go(driver, path):
    driver.get(BASE + path)
    # React: esperar a que #root tenga contenido
    wait(driver).until(lambda d: d.find_element(By.ID, "root").text.strip() != "")

def nav_header(driver):
    return driver.find_element(By.TAG_NAME, "header")

# ---- framework mínimo -------------------------------------------------------
def test(name):
    def deco(fn):
        def run(driver):
            t0 = time.time()
            try:
                detail = fn(driver) or ""
                ok = True
                err = ""
            except AssertionError as e:
                ok, err, detail = False, f"ASSERT: {e}", ""
            except Exception as e:
                ok, err, detail = False, f"{type(e).__name__}: {e}", ""
                traceback.print_exc()
            dt = round((time.time() - t0) * 1000)
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}  ({dt} ms)  {detail if ok else err}")
            results.append({"name": name, "status": status, "ms": dt,
                            "detail": detail if ok else err})
        run._name = name
        return run
    return deco

# ---- TESTS ------------------------------------------------------------------
@test("Home carga: título, nav y secciones")
def t_home(driver):
    go(driver, "/")
    assert "Palomas" in driver.title, f"título inesperado: {driver.title!r}"
    for label in ["Programación", "Artistas", "Plazas", "Noticias", "Entrar"]:
        el = driver.find_elements(By.XPATH, f"//header//a[normalize-space()='{label}']")
        assert el, f"falta enlace de nav '{label}'"
    h2s = [h.text for h in driver.find_elements(By.TAG_NAME, "h2")]
    assert any("CARTEL" in t.upper() for t in h2s), "no se ve sección EL CARTEL"
    return f"título OK, nav OK, {len(h2s)} h2"

@test("Sin errores SEVERE en consola (home)")
def t_console(driver):
    go(driver, "/")
    time.sleep(2)
    logs = driver.get_log("browser")
    severe = [l for l in logs if l.get("level") == "SEVERE"
              and "favicon" not in l.get("message", "").lower()]
    assert not severe, f"{len(severe)} errores SEVERE: {severe[:2]}"
    return "sin errores SEVERE relevantes"

@test("Navegación por el menú principal")
def t_nav(driver):
    go(driver, "/")
    expected = {"Programación": "/programacion", "Artistas": "/artistas",
                "Plazas": "/plazas", "Noticias": "/noticias"}
    for label, path in expected.items():
        link = wait(driver).until(EC.element_to_be_clickable(
            (By.XPATH, f"//header//a[normalize-space()='{label}']")))
        link.click()
        wait(driver).until(EC.url_contains(path))
        assert path in driver.current_url, f"'{label}' no fue a {path}"
    return "4 secciones navegadas"

@test("Programación: filtro por plaza reduce/ajusta las tarjetas")
def t_prog_filter(driver):
    go(driver, "/programacion")
    cards = driver.find_elements(By.XPATH, "//a[contains(@href,'/festivales/')]")
    total = len(cards)
    assert total > 10, f"esperaba muchas noches, hay {total}"
    btn = wait(driver).until(EC.element_to_be_clickable(
        (By.XPATH, "//button[normalize-space()='Algeciras']")))
    btn.click()
    time.sleep(1)
    filtered = driver.find_elements(By.XPATH, "//a[contains(@href,'/festivales/')]")
    assert 0 < len(filtered) < total, f"filtro no redujo: {total}->{len(filtered)}"
    return f"{total} noches -> {len(filtered)} en Algeciras"

@test("Programación: buscador de artista filtra resultados")
def t_prog_search(driver):
    go(driver, "/programacion")
    box = wait(driver).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "input[type='search']")))
    box.clear(); box.send_keys("Melendi")
    time.sleep(1)
    cards = driver.find_elements(By.XPATH, "//a[contains(@href,'/festivales/')]")
    txt = " ".join(c.text.upper() for c in cards)
    assert cards, "el buscador no dejó resultados para 'Melendi'"
    assert "MELENDI" in txt, "los resultados no contienen Melendi"
    return f"{len(cards)} resultados para 'Melendi'"

@test("Artistas: hay tarjetas y abren el detalle del festival")
def t_artist_detail(driver):
    go(driver, "/artistas")
    cards = wait(driver).until(lambda d: d.find_elements(
        By.XPATH, "//a[contains(@href,'/festivales/')]") or False)
    assert len(cards) >= 5, f"pocas tarjetas de artista: {len(cards)}"
    href = cards[0].get_attribute("href")
    cards[0].click()
    wait(driver).until(EC.url_contains("/festivales/"))
    assert driver.find_element(By.ID, "root").text.strip(), "detalle vacío"
    return f"{len(cards)} artistas; detalle {href.split('/')[-1]} OK"

@test("Noticias: lista y detalle de una noticia")
def t_news(driver):
    go(driver, "/noticias")
    cards = driver.find_elements(By.XPATH, "//a[contains(@href,'/noticias/')]")
    assert len(cards) >= 2, f"pocas noticias: {len(cards)}"
    cards[0].click()
    wait(driver).until(EC.url_matches(r".*/noticias/[^/]+$"))
    body = driver.find_element(By.ID, "root").text
    assert len(body) > 200, "detalle de noticia parece vacío"
    return f"{len(cards)} noticias; detalle OK"

@test("Plazas: 3 plazas y enlace a programación filtrada")
def t_plazas(driver):
    go(driver, "/plazas")
    # las tarjetas de plaza se cargan async desde la API: esperar a que aparezcan
    wait(driver).until(lambda d: len(d.find_elements(
        By.XPATH, "//a[contains(@href,'/programacion?municipality=')]")) >= 3)
    links = driver.find_elements(By.XPATH, "//a[contains(@href,'/programacion?municipality=')]")
    assert len(links) >= 3, f"esperaba 3 plazas, hay {len(links)}"
    links[0].click()
    wait(driver).until(EC.url_contains("municipality="))
    return f"{len(links)} plazas; filtro por municipio OK"

@test("Login: formulario presente y rechaza credenciales inválidas")
def t_login(driver):
    go(driver, "/login")
    user = wait(driver).until(EC.presence_of_element_located((By.NAME, "username")))
    pwd = driver.find_element(By.NAME, "password")
    user.send_keys("noexiste_usuario_test@example.com")
    pwd.send_keys("contraseña-incorrecta-123")
    driver.find_element(By.XPATH, "//button[normalize-space()='Entrar']").click()
    time.sleep(3)
    # No debe autenticar: sigue en /login y no aparece zona de cuenta
    assert "/login" in driver.current_url, f"redirigió inesperadamente a {driver.current_url}"
    return "credenciales inválidas rechazadas (sigue en /login)"

@test("Registro: valida contraseñas que no coinciden (sin crear cuenta)")
def t_register_validation(driver):
    go(driver, "/registro")
    wait(driver).until(EC.presence_of_element_located((By.NAME, "full_name"))).send_keys("Test QA")
    driver.find_element(By.NAME, "email").send_keys("qa+noenviar@example.com")
    driver.find_element(By.NAME, "password").send_keys("Password123!")
    driver.find_element(By.NAME, "password2").send_keys("DIFERENTE456!")
    driver.find_element(By.XPATH, "//button[normalize-space()='Crear cuenta']").click()
    time.sleep(2)
    assert "/registro" in driver.current_url, "no debería avanzar con contraseñas distintas"
    return "registro bloqueado con contraseñas distintas"

@test("Newsletter: valida email (no suscribe vacío)")
def t_newsletter(driver):
    go(driver, "/")
    btn = driver.find_element(By.XPATH, "//button[normalize-space()='Suscribirme']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.5)
    email = driver.find_element(By.CSS_SELECTOR, "form input[type='email']")
    # click vía JS para evitar intercepción por elementos fijos (footer/contador)
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)
    # El input email HTML5 required debe bloquear el envío vacío
    required = email.get_attribute("required") is not None
    valid = driver.execute_script("return arguments[0].checkValidity();", email)
    assert required and valid is False, f"email vacío debería ser inválido (required={required}, valid={valid})"
    return "envío vacío bloqueado por validación HTML5 (required)"

@test("Páginas estáticas /p/:slug cargan")
def t_static_pages(driver):
    for slug in ["info-de-interes", "preguntas-frecuentes", "como-llegar", "aviso-legal"]:
        go(driver, f"/p/{slug}")
        body = driver.find_element(By.ID, "root").text
        assert len(body) > 150, f"/p/{slug} parece vacía"
    return "4 páginas estáticas con contenido"

@test("404: ruta inexistente muestra página de error (no se rompe)")
def t_404(driver):
    go(driver, "/ruta-que-no-existe-xyz")
    body = driver.find_element(By.ID, "root").text.upper()
    assert "NO ESTÁ EN EL CARTEL" in body or "404" in body, "no se ve página 404"
    # El menú sigue visible (la app no ha crasheado)
    assert driver.find_elements(By.TAG_NAME, "header"), "sin header en 404"
    return "página 404 correcta y app estable"

@test("Deep-link directo a ruta interna (fallback SPA)")
def t_deeplink(driver):
    # Cargar directamente sin pasar por la home: el hosting debe servir index.html
    go(driver, "/programacion")
    assert "PROGRAMACIÓN" in driver.find_element(By.ID, "root").text.upper()
    return "deep-link /programacion servido correctamente"


ALL = [t_home, t_console, t_nav, t_prog_filter, t_prog_search, t_artist_detail,
       t_news, t_plazas, t_login, t_register_validation, t_newsletter,
       t_static_pages, t_404, t_deeplink]

def main():
    global BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--headful", action="store_true")
    args = ap.parse_args()
    BASE = args.base.rstrip("/")

    print(f"\n=== PRUEBAS FUNCIONALES — {BASE} ===")
    print(f"Inicio: {datetime.now(timezone.utc).isoformat()}  ({len(ALL)} tests)\n")
    t0 = time.time()
    driver = make_driver(args.headful)
    try:
        for t in ALL:
            t(driver)
    finally:
        driver.quit()

    total = round(time.time() - t0, 1)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    print(f"\n--- RESUMEN: {passed} PASS / {failed} FAIL  en {total}s ---")
    with open("resultados_funcional.json", "w") as f:
        json.dump({"base": BASE, "passed": passed, "failed": failed,
                   "seconds": total, "tests": results}, f, ensure_ascii=False, indent=2)
    print("Guardado: resultados_funcional.json")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
