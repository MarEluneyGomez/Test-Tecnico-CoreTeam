import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--umbral_p90", type=float, default=300)
    return parser.parse_args()

def generar_graficos(df, out_dir: Path):
    plt.figure()
    df.groupby("endpoint_base")["requests_total"].sum().plot(kind="barh")
    plt.title("Requests por endpoint")
    plt.tight_layout()
    plt.savefig(out_dir / "requests.png")
    plt.close()

    plt.figure()
    df.groupby("endpoint_base")["p90_elapsed_ms"].mean().plot(kind="bar")
    plt.title("P90 elapsed ms por endpoint")
    plt.tight_layout()
    plt.savefig(out_dir / "p90_por_endpoint.png")
    plt.close()

def render_template(template_path: str, context: dict) -> str:
    base_dir = Path(__file__).resolve().parent
    html = (base_dir / template_path).read_text(encoding="utf-8")

    for k, v in context.items():
        html = html.replace(f"{{{{{k}}}}}", v)

    return html


def generar_html(df, output):
    tabla_html = df.to_html(index=False)

    html = render_template(
        "templates/reporte.html",
        {
            "TABLA_KPI": tabla_html,
            "IMG_REQUESTS": "requests.png",
            "IMG_P90": "p90_por_endpoint.png",
        }
    )

    Path(output).write_text(html, encoding="utf-8")


def main():
    args = parse_args()

    df = pd.read_csv(args.input)

    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    generar_graficos(df, output_dir)

    generar_html(df, args.output)

if __name__ == "__main__":
    main()
