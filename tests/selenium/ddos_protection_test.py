#!/usr/bin/env python3
"""
Pruebas de PROTECCIÓN frente a DDoS / abuso para Las Palomas Festival.
API: https://festival-apii.onrender.com   Web: https://festival-api-aucn.onrender.com

Objetivo: comprobar qué defensas existen contra ráfagas y abuso, SIN tumbar el
servicio (volúmenes acotados). Detecta:
  - Rate-limiting (HTTP 429 / Retry-After) en endpoints normales.
  - Autoprotección del backend bajo ráfaga (429/503 frente a degradación).
  - Protección contra abuso de LOGIN (credential stuffing / fuerza bruta).
  - Presencia de Cloudflare y cabeceras de mitigación.

NO es un ataque: son centenares de peticiones acotadas con fines de diagnóstico
sobre un servicio propio. Ajusta --scale con cabeza.

Uso: python ddos_protection_test.py [--scale 1.0]
"""
import argparse, json, random, string, time, urllib.request, urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

API = "https://festival-apii.onrender.com"
WEB = "https://festival-api-aucn.onrender.com"
UA = "festival-ddos-check/1.0 (authorized self-test)"

findings = []

def req(method, url, data=None, ctype=None, timeout=20):
    """Devuelve (status, latencia_ms, headers_dict) sin lanzar en 4xx/5xx."""
    headers = {"User-Agent": UA}
    body = None
    if data is not None:
        body = data.encode()
        headers["Content-Type"] = ctype or "application/x-www-form-urlencoded"
    r = urllib.request.Request(url, data=body, method=method, headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            ms = (time.time() - t0) * 1000
            return resp.status, ms, dict(resp.headers)
    except urllib.error.HTTPError as e:
        ms = (time.time() - t0) * 1000
        return e.code, ms, dict(e.headers)
    except Exception as e:
        ms = (time.time() - t0) * 1000
        return f"ERR:{type(e).__name__}", ms, {}

def burst(method, url, n, conc, data=None, ctype=None, randomize_login=False):
    """Lanza n peticiones con 'conc' concurrencia. Devuelve (counter, lat_list, headers_muestra)."""
    results = []
    def one(_i):
        d = data
        if randomize_login:
            u = "nouser_" + "".join(random.choices(string.ascii_lowercase, k=8)) + "@example.com"
            d = f"username={u}&password=WrongPass_{random.randint(1000,9999)}"
        return req(method, url, d, ctype)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=conc) as ex:
        for res in ex.map(one, range(n)):
            results.append(res)
    dur = time.time() - t0
    codes = Counter(str(s) for s, _, _ in results)
    lats = [ms for _, ms, _ in results]
    sample_headers = next((h for _, _, h in results if h), {})
    rps = n / dur if dur else 0
    return codes, lats, sample_headers, rps

def ratelimit_headers(h):
    keys = [k for k in h if k.lower() in (
        "retry-after", "ratelimit-limit", "ratelimit-remaining", "ratelimit-reset",
        "x-ratelimit-limit", "x-ratelimit-remaining", "cf-mitigated")]
    return {k: h[k] for k in keys}

def section(title):
    print(f"\n{'='*64}\n{title}\n{'='*64}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiplica el volumen de cada ráfaga (1.0 = por defecto)")
    args = ap.parse_args()
    s = args.scale

    print(f"PRUEBAS ANTI-DDoS / ABUSO — {API}")
    print("Volúmenes acotados, servicio propio, fines de diagnóstico.\n")
    report = {"api": API, "tests": {}}

    # --- Cloudflare / cabeceras ---
    section("0) Capa de borde y cabeceras")
    st, ms, h = req("GET", API + "/health")
    cf = "cf-ray" in {k.lower() for k in h}
    print(f"/health -> HTTP {st} ({round(ms)}ms)  Cloudflare delante: {'SÍ' if cf else 'NO'}")
    print(f"cf-ray: {h.get('cf-ray') or h.get('CF-RAY','-')}")
    rl = ratelimit_headers(h)
    print(f"Cabeceras de rate-limit declaradas: {rl or 'NINGUNA'}")
    if cf:
        findings.append(("INFO", "Cloudflare delante: ofrece mitigación DDoS L3/L4 básica y challenge."))
    if not rl:
        findings.append(("MEDIA", "La API no declara cabeceras de rate-limit (RateLimit-* / Retry-After)."))
    report["tests"]["edge"] = {"cloudflare": cf, "ratelimit_headers": rl}

    # --- A) Ráfaga endpoint ligero (/health) ---
    section("A) Ráfaga sobre endpoint ligero  /health")
    n, c = int(150*s), 30
    codes, lats, hh, rps = burst("GET", API + "/health", n, c)
    lats_ok = sorted(l for l in lats)
    print(f"{n} peticiones, {c} concurrentes -> {dict(codes)}")
    print(f"throughput: {rps:.1f} req/s | lat p50={round(lats_ok[len(lats_ok)//2])}ms "
          f"p95={round(lats_ok[int(len(lats_ok)*0.95)-1])}ms max={round(max(lats))}ms")
    throttled = any(k in codes for k in ("429", "503"))
    print(f"¿Rate-limit/throttle (429/503)?: {'SÍ' if throttled else 'NO'}")
    report["tests"]["burst_health"] = {"n": n, "conc": c, "codes": dict(codes), "rps": round(rps,1), "throttled": throttled}

    # --- B) Ráfaga endpoint con BD (/api/v1/festivals) ---
    section("B) Ráfaga sobre endpoint con BD  /api/v1/festivals")
    n, c = int(100*s), 20
    codes, lats, hh, rps = burst("GET", API + "/api/v1/festivals", n, c)
    lats_ok = sorted(lats)
    print(f"{n} peticiones, {c} concurrentes -> {dict(codes)}")
    print(f"throughput: {rps:.1f} req/s | lat p50={round(lats_ok[len(lats_ok)//2])}ms "
          f"p95={round(lats_ok[int(len(lats_ok)*0.95)-1])}ms max={round(max(lats))}ms")
    throttled = any(k in codes for k in ("429", "503"))
    errs = sum(v for k, v in codes.items() if k.startswith("ERR") or k.startswith("5"))
    print(f"¿Autoprotección (429/503)?: {'SÍ' if throttled else 'NO'}  | errores/5xx: {errs}")
    report["tests"]["burst_db"] = {"n": n, "conc": c, "codes": dict(codes), "rps": round(rps,1), "throttled": throttled}

    # --- C) Abuso de LOGIN (credential stuffing / fuerza bruta) ---
    section("C) Protección de LOGIN  POST /api/v1/auth/login (credenciales inválidas)")
    n, c = int(40*s), 10
    codes, lats, hh, rps = burst("POST", API + "/api/v1/auth/login", n, c,
                                 data="x", ctype="application/x-www-form-urlencoded",
                                 randomize_login=True)
    print(f"{n} intentos fallidos, {c} concurrentes -> {dict(codes)}")
    print(f"ritmo: {rps:.1f} intentos/s")
    locked = "429" in codes
    print(f"¿Aparece rate-limit/bloqueo (429)?: {'SÍ' if locked else 'NO'}")
    if not locked:
        findings.append(("ALTA", "El login NO limita intentos fallidos (sin 429/lockout): "
                         "vulnerable a fuerza bruta / credential stuffing."))
    report["tests"]["login_abuse"] = {"n": n, "conc": c, "codes": dict(codes), "rate_limited": locked}

    # --- D) Métodos/headers abusivos sencillos ---
    section("D) Cabeceras de spoofing de IP (bypass de rate-limit por XFF)")
    # Si hubiera rate-limit por IP, un atacante probaría rotar X-Forwarded-For.
    st1, _, _ = req("GET", API + "/health")
    r = urllib.request.Request(API + "/health",
                               headers={"User-Agent": UA, "X-Forwarded-For": "1.2.3.4"})
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            st2 = resp.status
    except urllib.error.HTTPError as e:
        st2 = e.code
    print(f"Sin XFF: HTTP {st1}  |  con X-Forwarded-For falso: HTTP {st2}")
    print("(Informativo: si el rate-limit fuese por IP de app y confiara en XFF, sería eludible.)")

    # --- Resumen ---
    section("RESUMEN DE DEFENSAS")
    defenses = {
        "Cloudflare (DDoS L3/L4 + challenge)": report["tests"]["edge"]["cloudflare"],
        "Rate-limit declarado en API": bool(report["tests"]["edge"]["ratelimit_headers"]),
        "Throttle bajo ráfaga (/health)": report["tests"]["burst_health"]["throttled"],
        "Autoprotección BD bajo ráfaga": report["tests"]["burst_db"]["throttled"],
        "Rate-limit en login": report["tests"]["login_abuse"]["rate_limited"],
    }
    for k, v in defenses.items():
        print(f"  [{'✓' if v else '✗'}] {k}")
    print("\nHallazgos:")
    for sev, msg in findings:
        print(f"  ({sev}) {msg}")

    report["defenses"] = defenses
    report["findings"] = [{"sev": s, "msg": m} for s, m in findings]
    with open("resultados_ddos.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nGuardado: resultados_ddos.json")

if __name__ == "__main__":
    main()
