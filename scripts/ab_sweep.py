"""
Orquestador del experimento A/B de la Fase 1 (InterpretiveFilter) con más
semillas — repite el diseño de docs/experiments/2026-09-21-fase1-ecuacion-personal.md
pero con n configurable (pending item: "repetir con n>=15-20 semillas antes de
descartar la hipótesis", ver docs/handoffs/2026-09-21.md §7).

Lanza scripts/ab_interpretive.py como subproceso por cada combinación
(semilla, condición) — necesario porque INTERPRETIVE_FILTER_ENABLED se lee al
importar core.agents, así que cada condición debe correr en su propio proceso.
Corre combinaciones en paralelo (--workers) para acortar el tiempo de pared.

Uso:
    python scripts/ab_sweep.py --seeds 42-56 --days 300 --workers 3
    python scripts/ab_sweep.py --seeds 42,43,44 --weight 0.30 --output data/metrics/ab_sensibilidad.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SCRIPT = str(_ROOT / "scripts" / "ab_interpretive.py")

_CONDITIONS = {
    "OFF":           {"INTERPRETIVE_FILTER_ENABLED": "0", "MENTAL_VAULT_ENABLED": "0"},
    "FILTER":        {"INTERPRETIVE_FILTER_ENABLED": "1", "MENTAL_VAULT_ENABLED": "0"},
    "FILTER_VAULT":  {"INTERPRETIVE_FILTER_ENABLED": "1", "MENTAL_VAULT_ENABLED": "1"},
}


def _parse_seeds(spec: str) -> list[int]:
    seeds: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-")
            seeds.extend(range(int(lo), int(hi) + 1))
        else:
            seeds.append(int(part))
    return seeds


def _run_one(seed: int, condition: str, days: int, seed_file: str, weight: float) -> dict:
    env = os.environ.copy()
    env.update(_CONDITIONS[condition])
    env["AB_SEED"] = str(seed)
    env["AB_DAYS"] = str(days)
    env["AB_SEED_FILE"] = seed_file
    env["INTERPRETIVE_WEIGHT"] = str(weight)

    proc = subprocess.run(
        [sys.executable, _SCRIPT],
        cwd=str(_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    line = next((l for l in proc.stdout.splitlines() if l.startswith("AB_RESULT ")), None)
    if line is None:
        raise RuntimeError(
            f"seed={seed} condition={condition}: sin AB_RESULT en stdout.\n"
            f"stdout={proc.stdout[-2000:]}\nstderr={proc.stderr[-2000:]}"
        )
    result = json.loads(line[len("AB_RESULT "):])
    result["condition"] = condition
    result["weight"] = weight
    return result


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5


_METRICS = [
    "kl_mean_q4", "mig_q4", "imi_q4", "behavioral_kl_q4", "field_kl_q4",
    "valence_std_q4", "arousal_std_q4", "worldview_coh_q4",
    "behavioral_entropy_intra_q4",
    "valence_std_intra_q4", "valence_std_inter_q4",
    "arousal_std_intra_q4", "arousal_std_inter_q4",
]


def _paired_analysis(results: list[dict], seeds: list[int]) -> None:
    by_key = {(r["seed"], r["condition"]): r for r in results}

    for cond in ("FILTER", "FILTER_VAULT"):
        print(f"\n=== {cond} - OFF (pareado por semilla, n={len(seeds)}) ===")
        for metric in _METRICS:
            deltas = []
            for seed in seeds:
                off = by_key.get((seed, "OFF"))
                on  = by_key.get((seed, cond))
                if off is None or on is None:
                    continue
                deltas.append(on[metric] - off[metric])
            if not deltas:
                continue
            n_pos = sum(1 for d in deltas if d > 0)
            n_neg = sum(1 for d in deltas if d < 0)
            print(
                f"  {metric:20s} delta_mean={_mean(deltas):+.6f}  delta_std={_std(deltas):.6f}  "
                f"n_pos={n_pos}  n_neg={n_neg}  n={len(deltas)}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="42-56", help="Semillas: '42-56' o '42,43,44'")
    parser.add_argument("--days", type=int, default=300)
    parser.add_argument("--seed-file", default="data/seeds/rich_culture_100.yaml")
    parser.add_argument("--weight", type=float, default=0.15, help="INTERPRETIVE_WEIGHT (default = comportamiento actual)")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--output", default="data/metrics/ab_interpretive_fase1_sweep.jsonl")
    parser.add_argument("--conditions", default="OFF,FILTER,FILTER_VAULT")
    args = parser.parse_args()

    seeds = _parse_seeds(args.seeds)
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    jobs = [(s, c) for s in seeds for c in conditions]

    print(f"[ab_sweep] {len(seeds)} semillas x {len(conditions)} condiciones = "
          f"{len(jobs)} corridas, {args.days} dias c/u, weight={args.weight}, workers={args.workers}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool, open(out_path, "w", encoding="utf-8") as f:
        futures = {
            pool.submit(_run_one, seed, cond, args.days, args.seed_file, args.weight): (seed, cond)
            for seed, cond in jobs
        }
        for fut in as_completed(futures):
            seed, cond = futures[fut]
            done += 1
            try:
                r = fut.result()
                results.append(r)
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
                elapsed = time.time() - t0
                print(f"  [{done}/{len(jobs)}] seed={seed} {cond:14s} OK  "
                      f"({elapsed:.0f}s transcurridos)", flush=True)
            except Exception as exc:
                print(f"  [{done}/{len(jobs)}] seed={seed} {cond:14s} ERROR: {exc}", flush=True)

    print(f"\n[ab_sweep] {len(results)}/{len(jobs)} corridas completadas en {time.time() - t0:.0f}s")
    print(f"[ab_sweep] resultados crudos en {out_path}")

    _paired_analysis(results, seeds)


if __name__ == "__main__":
    main()
