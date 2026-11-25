#!/usr/bin/env python3
"""
Prueba de ESTRÉS / CARGA con Selenium para Las Palomas Festival.
Web: https://festival-api-aucn.onrender.com/

Lanza N navegadores Chromium headless concurrentes. Cada worker reutiliza su
navegador y recorre en bucle un conjunto de páginas reales (que a su vez
disparan llamadas a la API). Mide:
  - latencia de reloj de pared (get + render + datos API hasta #root con contenido)
  - Navigation Timing del navegador (evento load)
  - throughput (cargas/seg), errores y percentiles p50/p90/p95/p99/max

NOTA: Render free tier es modesto; los valores por defecto son conservadores
para estresar sin tumbar un servicio propio. Sube --workers/--iters con cabeza.

Uso: python stress_test.py [--workers 6] [--iters 8] [--base URL]
"""
import argparse, json, statistics, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = "https://festival-api-aucn.onrender.com"
PAGES = ["/", "/programacion", "/artistas", "/plazas", "/noticias",
         "/festivales/melendi-algeciras-2027", "/noticias/programacion-2027",
         "/p/preguntas-frecuentes"]
PAGE_TIMEOUT = 45

_print_lock = threading.Lock()
samples = []          # dicts: worker, path, wall_ms, load_ms, ok, err
samples_lock = threading.Lock()

def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--blink-settings=imagesEnabled=false")  # menos ancho de banda local
    opts.binary_location = "/usr/bin/chromium"
    d = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)
    d.set_page_load_timeout(PAGE_TIMEOUT)
    return d

def load_once(driver, path):
    t0 = time.time()
    driver.get(BASE + path)
    WebDriverWait(driver, PAGE_TIMEOUT).until(
        lambda d: d.find_element(By.ID, "root").text.strip() != "")
    wall = (time.time() - t0) * 1000
    try:
        load_ms = driver.execute_script(
            "var n=performance.getEntriesByType('navigation')[0];"
            "return n? Math.round(n.loadEventEnd - n.startTime): null;")
    except Exception:
        load_ms = None
    return wall, load_ms

def worker(wid, iters, pages):
    try:
        driver = make_driver()
    except Exception as e:
        with samples_lock:
            samples.append({"worker": wid, "path": "-", "wall_ms": None,
                            "load_ms": None, "ok": False, "err": f"driver: {e}"})
        return
    try:
        for i in range(iters):
            path = pages[(wid + i) % len(pages)]
            try:
                wall, load_ms = load_once(driver, path)
                rec = {"worker": wid, "path": path, "wall_ms": round(wall),
                       "load_ms": load_ms, "ok": True, "err": ""}
            except Exception as e:
                rec = {"worker": wid, "path": path, "wall_ms": None,
                       "load_ms": None, "ok": False, "err": f"{type(e).__name__}"}
            with samples_lock:
                samples.append(rec)
            with _print_lock:
                st = f"{rec['wall_ms']}ms" if rec["ok"] else f"ERR {rec['err']}"
                print(f"  w{wid} it{i} {path:<42} {st}")
    finally:
        driver.quit()

def pct(data, p):
    if not data:
        return None
    data = sorted(data)
    k = (len(data) - 1) * p / 100
    f = int(k)
    if f + 1 < len(data):
        return round(data[f] + (data[f+1] - data[f]) * (k - f))
    return round(data[f])

def warmup():
    import urllib.request
    print("Warm-up (Render free puede estar hibernando)...")
    for u in [BASE + "/", "https://festival-apii.onrender.com/health"]:
        try:
            t0 = time.time()
            urllib.request.urlopen(u, timeout=90).read()
            print(f"  {u} -> {round((time.time()-t0)*1000)}ms")
        except Exception as e:
            print(f"  {u} -> {e}")

def main():
    global BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--iters", type=int, default=8, help="cargas por worker")
    ap.add_argument("--ramp", type=float, default=0.4, help="seg entre arranque de workers")
    args = ap.parse_args()
    BASE = args.base.rstrip("/")

    pages = PAGES
    total_expected = args.workers * args.iters
    print(f"\n=== PRUEBA DE ESTRÉS — {BASE} ===")
    print(f"{args.workers} workers × {args.iters} iters = {total_expected} cargas "
          f"| inicio {datetime.now(timezone.utc).isoformat()}\n")
    warmup()
    print()

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = []
        for wid in range(args.workers):
            futs.append(ex.submit(worker, wid, args.iters, pages))
            time.sleep(args.ramp)  # ramp-up escalonado
        for f in as_completed(futs):
            f.result()
    wall_total = time.time() - t0

    ok = [s for s in samples if s["ok"]]
    bad = [s for s in samples if not s["ok"]]
    walls = [s["wall_ms"] for s in ok]
    loads = [s["load_ms"] for s in ok if s["load_ms"] is not None]

    print(f"\n--- RESULTADOS ---")
    print(f"Cargas OK:     {len(ok)}/{len(samples)}  ({len(bad)} errores)")
    print(f"Duración total:{wall_total:8.1f} s")
    if ok:
        print(f"Throughput:    {len(ok)/wall_total:8.2f} cargas/seg")
        print(f"Reloj de pared (ms) — contenido usable (#root + datos API):")
        print(f"   min={min(walls)}  p50={pct(walls,50)}  p90={pct(walls,90)}"
              f"  p95={pct(walls,95)}  p99={pct(walls,99)}  max={max(walls)}  media={round(statistics.mean(walls))}")
        if loads:
            print(f"Navigation Timing loadEventEnd (ms):")
            print(f"   p50={pct(loads,50)}  p95={pct(loads,95)}  max={max(loads)}")
        # peor página
        by_page = {}
        for s in ok:
            by_page.setdefault(s["path"], []).append(s["wall_ms"])
        print("Por página (p95 ms):")
        for p, vals in sorted(by_page.items(), key=lambda kv: -pct(kv[1], 95)):
            print(f"   {p:<42} n={len(vals):<2} p50={pct(vals,50):<6} p95={pct(vals,95)}")
    if bad:
        from collections import Counter
        print("Errores:", dict(Counter(s["err"] for s in bad)))

    with open("resultados_estres.json", "w") as f:
        json.dump({"base": BASE, "workers": args.workers, "iters": args.iters,
                   "seconds": round(wall_total, 1), "ok": len(ok), "errors": len(bad),
                   "throughput_rps": round(len(ok)/wall_total, 3) if ok else 0,
                   "wall_ms": {"min": min(walls) if ok else None, "p50": pct(walls,50),
                               "p90": pct(walls,90), "p95": pct(walls,95),
                               "p99": pct(walls,99), "max": max(walls) if ok else None},
                   "samples": samples}, f, ensure_ascii=False, indent=2)
    print("\nGuardado: resultados_estres.json")

if __name__ == "__main__":
    main()
