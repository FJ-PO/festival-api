#!/usr/bin/env python3
"""
Estrés de la API comparando DESPLIEGUE LOCAL vs PRODUCCIÓN.

Lanza ráfagas HTTP concurrentes contra el mismo endpoint en ambos despliegues y
compara throughput y latencias (p50/p95/p99). Aísla el rendimiento del backend
(el local no tiene red ni Cloudflare delante), por lo que sirve para distinguir
"lentitud del código" de "lentitud de la infraestructura/red".

Requisitos:
  - API local corriendo:  uvicorn app.main:app --port 8000   (desde la raíz del repo)
  - Conexión a producción.

Uso: python stress_local_vs_prod.py [--local URL] [--prod URL] [--n 100] [--conc 20]

NOTA: la comparación NO es "igualdad de condiciones" (local = tu máquina sin red;
prod = instancia Render free + red + Cloudflare). El objetivo es justamente ver
cuánto del tiempo de producción es infraestructura y no código.
"""
import argparse, json, statistics, time, urllib.request, urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

LOCAL = "http://127.0.0.1:8000"
PROD = "https://festival-apii.onrender.com"
PATH = "/api/v1/festivals"
UA = "festival-stress-local-vs-prod/1.0 (authorized self-test)"

def one(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            resp.read()
            return resp.status, (time.time() - t0) * 1000
    except urllib.error.HTTPError as e:
        return e.code, (time.time() - t0) * 1000
    except Exception as e:
        return f"ERR:{type(e).__name__}", (time.time() - t0) * 1000

def pct(data, p):
    data = sorted(data)
    if not data:
        return None
    k = (len(data) - 1) * p / 100
    f = int(k)
    return round(data[f] + (data[f+1]-data[f])*(k-f)) if f+1 < len(data) else round(data[f])

def run(label, base, path, n, conc):
    url = base + path
    print(f"\n--- {label}: {url}  ({n} req, {conc} concurrentes) ---")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=conc) as ex:
        res = list(ex.map(lambda _: one(url), range(n)))
    dur = time.time() - t0
    codes = Counter(str(s) for s, _ in res)
    lats = [ms for s, ms in res if str(s) == "200"]
    rps = n / dur if dur else 0
    out = {"label": label, "url": url, "n": n, "conc": conc, "codes": dict(codes),
           "rps": round(rps, 1), "dur_s": round(dur, 2)}
    if lats:
        out.update({"min": round(min(lats)), "p50": pct(lats, 50), "p95": pct(lats, 95),
                    "p99": pct(lats, 99), "max": round(max(lats)), "mean": round(statistics.mean(lats))})
        print(f"  códigos: {dict(codes)} | throughput: {rps:.1f} req/s")
        print(f"  latencia ms: min={out['min']} p50={out['p50']} p95={out['p95']} "
              f"p99={out['p99']} max={out['max']} media={out['mean']}")
    else:
        print(f"  códigos: {dict(codes)} (sin 200)")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", default=LOCAL)
    ap.add_argument("--prod", default=PROD)
    ap.add_argument("--path", default=PATH)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--conc", type=int, default=20)
    args = ap.parse_args()

    print("=== ESTRÉS API: LOCAL vs PRODUCCIÓN ===")
    print(f"endpoint: {args.path} | {args.n} req @ {args.conc} concurrentes por despliegue")
    # calentar prod (Render free puede hibernar)
    one(args.prod + "/health")
    local = run("LOCAL", args.local, args.path, args.n, args.conc)
    prod = run("PRODUCCIÓN", args.prod, args.path, args.n, args.conc)

    print("\n=== COMPARATIVA ===")
    if local.get("p50") and prod.get("p50"):
        print(f"  throughput:  local {local['rps']:.1f} req/s  vs  prod {prod['rps']:.1f} req/s "
              f"(x{local['rps']/prod['rps']:.1f})")
        print(f"  p50:         local {local['p50']} ms      vs  prod {prod['p50']} ms "
              f"(x{prod['p50']/local['p50']:.1f} más lento en prod)")
        print(f"  p95:         local {local['p95']} ms      vs  prod {prod['p95']} ms")
    report = {"endpoint": args.path, "n": args.n, "conc": args.conc,
              "local": local, "prod": prod}
    with open("resultados_local_vs_prod.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nGuardado: resultados_local_vs_prod.json")

if __name__ == "__main__":
    main()
