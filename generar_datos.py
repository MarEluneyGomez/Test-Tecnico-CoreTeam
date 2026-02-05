import argparse
import json
import random
from datetime import datetime, timedelta, timezone
import sys

ENDPOINTS = ["/get", "/post", "/status/403", "/basic-auth", "/cookies", "/xml", "/html"]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_registros", type=int, required=True)
    parser.add_argument("--salida", type=str, required=True)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()

def generar_timestamp() -> str:
    """
    Genera un timestamp UTC en formato ISO 8601.
    El timestamp se ubica aleatoriamente dentro de los últimos 3 días.
    """
    ahora = datetime.now(timezone.utc)
    delta = timedelta(
        days=random.randint(0, 3),
        seconds=random.randint(0, 86400)
    )
    return (ahora - delta).isoformat() + "Z"

def generar_status(endpoint: str) -> int:
    """
    Genera un status code coherente con el endpoint:
    - /status/403 siempre devuelve 403
    - El resto devuelve 200 en el 90% de los casos
    - El 10% restante se reparte entre errores 4xx y 5xx
    """
    if endpoint == "/status/403":
        return 403
    return 200 if random.random() < 0.9 else random.choice([400,500])

def generar_registro() -> dict:
    endpoint = random.choice(ENDPOINTS)
    return {
        "timestamp_utc": generar_timestamp(),
        "endpoint": endpoint,
        "status_code": generar_status(endpoint),
        "elapsed_ms": round(random.uniform(50, 800), 2),
        "parse_result": "error" if random.random() < 0.05 else "ok"
    }

def generar_archivo(n:int, salida:str):
    with open(salida, "w") as f:
        for _ in range(n):
            f.write(json.dumps(generar_registro()) + "\n")

def main():
    try:
        args = parse_args()

        if args.seed is not None:
            # Permite reproducir exactamente los mismos datos
            random.seed(args.seed)

        generar_archivo(args.n_registros, args.salida)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()