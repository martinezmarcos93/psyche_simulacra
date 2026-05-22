"""
Suite de robustez — ejecuta N simulaciones con semillas distintas y reporta
estadísticas de emergencia colectiva.

Uso:
    python scripts/run_robustness.py
    python scripts/run_robustness.py --runs 20 --days 150
    python scripts/run_robustness.py --seeds 42,1337,9999 --days 200
    python scripts/run_robustness.py --output data/metrics/robustez_custom.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simulation import SimulationRunner
from core.metrics.emergence import EmergenceMetrics

_DEFAULT_RUNS     = 10
_DEFAULT_DAYS     = 100
_DEFAULT_SEEDS_F  = "data/seeds/initial_personas.yaml"
_DEFAULT_OUTPUT   = "data/metrics/robustez.json"


def _run_one(seed: int, n_days: int, seed_file: str) -> dict:
    """Lanza una simulación aislada y devuelve las métricas finales."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "sim.db")
        cp = os.path.join(tmpdir, "checkpoints")

        runner = SimulationRunner.new_session(
            seed_file=seed_file,
            seed=seed,
            db_path=db,
            checkpoint_dir=cp,
        )
        runner.run(n_days=n_days)

        m = EmergenceMetrics()
        snap = m.compute_day(
            dia=runner.current_dia,
            agents=runner.agents.agents,
            tribe_manager=runner.agents.tribe_manager,
            collective_field=runner.agents.collective_field,
            culture_engine=runner.agents.culture_engine,
        )
        return {
            "seed":        seed,
            "final_dia":   runner.current_dia,
            "n_alive":     runner.alive_count,
            "kl_mean":     snap.kl_mean,
            "kl_max":      snap.kl_max,
            "vfe_global":  snap.vfe_global,
            "vfe_tribe":   snap.vfe_tribe_mean,
            "imi":         snap.imi,
            "mig":         snap.mig,
            "n_tribes":    snap.n_tribes,
            "n_structs":   snap.n_structures,
        }


def _stats(values: list[float]) -> dict:
    if not values:
        return {}
    mean = sum(values) / len(values)
    std  = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
    return {
        "mean": round(mean, 5),
        "std":  round(std, 5),
        "min":  round(min(values), 5),
        "max":  round(max(values), 5),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Suite de robustez — emergencia colectiva")
    parser.add_argument("--runs",      type=int, default=_DEFAULT_RUNS,    help="Numero de ejecuciones")
    parser.add_argument("--days",      type=int, default=_DEFAULT_DAYS,    help="Dias simulados por ejecucion")
    parser.add_argument("--seed-file", default=_DEFAULT_SEEDS_F,           help="Archivo YAML de semillas")
    parser.add_argument("--output",    default=_DEFAULT_OUTPUT,            help="Archivo JSON de salida")
    parser.add_argument("--seeds",     default="",                         help="Semillas separadas por coma")
    args = parser.parse_args()

    if args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    else:
        import random
        rng = random.Random(0)
        seeds = [rng.randint(1, 99999) for _ in range(args.runs)]

    print(f"[Robustez] {len(seeds)} ejecuciones x {args.days} dias")
    results: list[dict] = []

    for i, seed in enumerate(seeds):
        print(f"  [{i+1}/{len(seeds)}] seed={seed} ...", end="", flush=True)
        try:
            r = _run_one(seed, args.days, args.seed_file)
            results.append(r)
            print(f"  KL={r['kl_mean']:.4f}  IMI={r['imi']:.4f}  tribus={r['n_tribes']}")
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    if not results:
        print("[Robustez] Ninguna ejecucion completada.")
        sys.exit(1)

    keys = ["kl_mean", "kl_max", "vfe_global", "vfe_tribe", "imi", "mig", "n_alive", "n_tribes", "n_structs"]
    aggregate = {k: _stats([r[k] for r in results if k in r]) for k in keys}

    report = {
        "config": {
            "n_runs":    len(results),
            "n_days":    args.days,
            "seeds":     seeds,
            "seed_file": args.seed_file,
        },
        "aggregate": aggregate,
        "runs":      results,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[Robustez] Resultados guardados en {out_path}")
    print(f"  KL divergencia:  media={aggregate['kl_mean'].get('mean', 0):.4f}  std={aggregate['kl_mean'].get('std', 0):.4f}")
    print(f"  IMI:             media={aggregate['imi'].get('mean', 0):.4f}  std={aggregate['imi'].get('std', 0):.4f}")
    print(f"  MIG:             media={aggregate['mig'].get('mean', 0):.4f}  std={aggregate['mig'].get('std', 0):.4f}")
    print(f"  VFE global:      media={aggregate['vfe_global'].get('mean', 0):.4f}")
    print(f"  Tribus formadas: media={aggregate['n_tribes'].get('mean', 0):.1f}")


if __name__ == "__main__":
    main()
