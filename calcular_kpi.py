import argparse
import json
import csv
from collections import defaultdict
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()

def normalizar_endpoint(endpoint: str) -> str:
    if endpoint.startswith("/status"):
        return "/status"
    if endpoint.startswith("/basic-auth"):
        return "/basic-auth"
    return endpoint.split("?")[0]

def leer_datos(path: str):
    with open(path, encoding="utf-8") as f:
        for linea in f:
            yield json.loads(linea)

def calcular_kpis(registros):
    grupos = defaultdict(list)

    for r in registros:
        fecha = r["timestamp_utc"][:10]
        endpoint = normalizar_endpoint(r["endpoint"])
        grupos[(fecha, endpoint)].append(r)

    resultados = []

    for (fecha, endpoint), items in grupos.items():
        elapsed = [i["elapsed_ms"] for i in items]

        resultados.append({
            "date_utc": fecha,
            "endpoint_base": endpoint,
            "requests_total": len(items),
            "success_2xx": sum(200 <= i["status_code"] < 300 for i in items),
            "client_4xx": sum(400 <= i["status_code"] < 500 for i in items),
            "server_5xx": sum(500 <= i["status_code"] < 600 for i in items),
            "parse_errors": sum(i["parse_result"] != "ok" for i in items),
            "avg_elapsed_ms": round(sum(elapsed) / len(elapsed), 2),
            "p90_elapsed_ms": round(np.percentile(elapsed, 90), 2),
        })

    return resultados

def escribir_csv(path: str, filas: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=filas[0].keys())
        writer.writeheader()
        writer.writerows(filas)

def main():
    args = parse_args()
    registros = list(leer_datos(args.input))
    kpis = calcular_kpis(registros)
    escribir_csv(args.output, kpis)

if __name__ == "__main__":
    main()
