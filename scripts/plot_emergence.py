"""
plot_emergence.py — Reportes gráficos automatizados de emergencia colectiva.

Lee el JSON producido por run_robustness.py y genera un informe visual con 6 gráficas:
    1. KL divergence por ejecución (box + swarm)
    2. MIG (Mean Information Gain) por ejecución
    3. IMI (Índice de Modularidad de Información) por ejecución
    4. VFE global por ejecución
    5. Dispersión MIG vs n_tribes (¿más tribus → más diferenciación?)
    6. Supervivencia final (n_alive) por ejecución

Uso:
    python scripts/plot_emergence.py
    python scripts/plot_emergence.py --input data/metrics/robustez.json
    python scripts/plot_emergence.py --input data/metrics/robustez.json --output reports/emergence.png
    python scripts/plot_emergence.py --show   # abre ventana interactiva además de guardar
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_DEFAULT_INPUT  = "data/metrics/robustez.json"
_DEFAULT_OUTPUT = "data/metrics/emergence_report.png"


def _require_matplotlib() -> None:
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        print("[plot_emergence] ERROR: matplotlib no está instalado.")
        print("  Instálalo con:  pip install matplotlib")
        sys.exit(1)


def _load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"[plot_emergence] No se encontró el archivo: {p}")
        print("  Genera el reporte primero con:  python scripts/run_robustness.py")
        sys.exit(1)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def plot(input_path: str, output_path: str, show: bool = False) -> None:
    _require_matplotlib()
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    data    = _load(input_path)
    runs    = data.get("runs", [])
    cfg     = data.get("config", {})
    agg     = data.get("aggregate", {})

    if not runs:
        print("[plot_emergence] El archivo no contiene ejecuciones.")
        sys.exit(1)

    n_runs  = len(runs)
    seeds   = [str(r.get("seed", i)) for i, r in enumerate(runs)]

    # Extraer series
    kl_vals   = [r.get("kl_mean",  0.0) for r in runs]
    mig_vals  = [r.get("mig",      0.0) for r in runs]
    imi_vals  = [r.get("imi",      0.0) for r in runs]
    vfe_vals  = [r.get("vfe_global", 0.0) for r in runs]
    tribe_vals = [r.get("n_tribes", 0)  for r in runs]
    alive_vals = [r.get("n_alive",  0)  for r in runs]

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(16, 10), facecolor="#0d0d0d")
    fig.suptitle(
        f"PSYCHE SIMULACRA — Reporte de Emergencia Colectiva\n"
        f"{n_runs} ejecuciones × {cfg.get('n_days', '?')} días",
        color="white", fontsize=14, fontweight="bold", y=0.98,
    )

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)
    axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]

    _ACCENT = "#7ec8e3"
    _BAR    = "#c3a6ff"
    _SCAT   = "#ff9f7e"

    def _style_ax(ax: plt.Axes, title: str, ylabel: str) -> None:
        ax.set_facecolor("#1a1a2e")
        ax.set_title(title, color="white", fontsize=10, pad=6)
        ax.set_ylabel(ylabel, color="#aaaaaa", fontsize=8)
        ax.tick_params(colors="#888888", labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor("#444444")
        ax.title.set_fontweight("bold")

    # 1. KL divergencia
    ax = axes[0]
    _style_ax(ax, "KL Divergence inter-tribal", "KL simétrica")
    ax.bar(range(n_runs), kl_vals, color=_ACCENT, alpha=0.85, width=0.7)
    ax.axhline(
        sum(kl_vals) / n_runs, color="white", linestyle="--", linewidth=0.8,
        label=f"media {sum(kl_vals)/n_runs:.4f}"
    )
    ax.legend(fontsize=7, labelcolor="white", facecolor="#1a1a2e", edgecolor="#444")
    ax.set_xticks(range(n_runs))
    ax.set_xticklabels(seeds, rotation=45, ha="right", fontsize=6)

    # 2. MIG
    ax = axes[1]
    _style_ax(ax, "MIG — Mean Information Gain", "I(z;v) / H(z)")
    ax.bar(range(n_runs), mig_vals, color=_BAR, alpha=0.85, width=0.7)
    if any(v > 0 for v in mig_vals):
        ax.axhline(
            sum(mig_vals) / n_runs, color="white", linestyle="--", linewidth=0.8,
            label=f"media {sum(mig_vals)/n_runs:.4f}"
        )
        ax.legend(fontsize=7, labelcolor="white", facecolor="#1a1a2e", edgecolor="#444")
    ax.set_xticks(range(n_runs))
    ax.set_xticklabels(seeds, rotation=45, ha="right", fontsize=6)

    # 3. IMI
    ax = axes[2]
    _style_ax(ax, "IMI — Modularidad de Información", "R² arquetípico-tribal")
    ax.bar(range(n_runs), imi_vals, color="#78e08f", alpha=0.85, width=0.7)
    ax.axhline(
        sum(imi_vals) / n_runs, color="white", linestyle="--", linewidth=0.8,
        label=f"media {sum(imi_vals)/n_runs:.4f}"
    )
    ax.legend(fontsize=7, labelcolor="white", facecolor="#1a1a2e", edgecolor="#444")
    ax.set_xticks(range(n_runs))
    ax.set_xticklabels(seeds, rotation=45, ha="right", fontsize=6)

    # 4. VFE global
    ax = axes[3]
    _style_ax(ax, "VFE Global — Entropía del Campo Colectivo", "H(símbolos)")
    ax.bar(range(n_runs), vfe_vals, color="#ffd32a", alpha=0.85, width=0.7)
    ax.axhline(
        sum(vfe_vals) / n_runs, color="white", linestyle="--", linewidth=0.8,
        label=f"media {sum(vfe_vals)/n_runs:.4f}"
    )
    ax.legend(fontsize=7, labelcolor="white", facecolor="#1a1a2e", edgecolor="#444")
    ax.set_xticks(range(n_runs))
    ax.set_xticklabels(seeds, rotation=45, ha="right", fontsize=6)

    # 5. Dispersión MIG vs n_tribes
    ax = axes[4]
    _style_ax(ax, "MIG vs Tribus formadas", "MIG")
    ax.scatter(tribe_vals, mig_vals, color=_SCAT, alpha=0.85, s=60, zorder=3)
    ax.set_xlabel("n_tribes", color="#aaaaaa", fontsize=8)
    # Anotar semillas
    for i, (t, m) in enumerate(zip(tribe_vals, mig_vals)):
        ax.annotate(
            seeds[i], (t, m), textcoords="offset points",
            xytext=(4, 4), fontsize=6, color="#888888",
        )

    # 6. Supervivencia final
    ax = axes[5]
    _style_ax(ax, "Agentes Vivos al Final", "n_alive")
    ax.bar(range(n_runs), alive_vals, color="#ee5a24", alpha=0.85, width=0.7)
    ax.axhline(
        sum(alive_vals) / n_runs, color="white", linestyle="--", linewidth=0.8,
        label=f"media {sum(alive_vals)/n_runs:.1f}"
    )
    ax.legend(fontsize=7, labelcolor="white", facecolor="#1a1a2e", edgecolor="#444")
    ax.set_xticks(range(n_runs))
    ax.set_xticklabels(seeds, rotation=45, ha="right", fontsize=6)

    # ── Tabla resumen ──────────────────────────────────────────────────────────
    summary_lines = []
    for key, label in [
        ("kl_mean",   "KL media"),
        ("mig",       "MIG"),
        ("imi",       "IMI"),
        ("vfe_global","VFE global"),
        ("n_tribes",  "Tribus (media)"),
    ]:
        s = agg.get(key, {})
        if s:
            summary_lines.append(
                f"{label:16s}  μ={s.get('mean',0):.4f}  σ={s.get('std',0):.4f}"
                f"  [{s.get('min',0):.3f}, {s.get('max',0):.3f}]"
            )

    fig.text(
        0.5, 0.01, "  |  ".join(summary_lines[:3]) + "\n" + "  |  ".join(summary_lines[3:]),
        ha="center", va="bottom", fontsize=7, color="#888888",
        fontfamily="monospace",
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"[plot_emergence] Reporte guardado en: {out}")

    if show:
        plt.show()
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera reportes gráficos de emergencia colectiva"
    )
    parser.add_argument(
        "--input",  default=_DEFAULT_INPUT,
        help=f"JSON de run_robustness.py (default: {_DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--output", default=_DEFAULT_OUTPUT,
        help=f"PNG de salida (default: {_DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Abrir ventana interactiva además de guardar"
    )
    args = parser.parse_args()
    plot(args.input, args.output, show=args.show)


if __name__ == "__main__":
    main()
