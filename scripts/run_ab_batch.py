"""
Orquestador del batch A/B de la Fase 1 (Ecuación Personal) — corre N semillas
x 3 condiciones (OFF / FILTER / FILTER+VAULT) invocando scripts/ab_interpretive.py
en subprocesos separados (el flag INTERPRETIVE_FILTER_ENABLED se lee al importar
core.agents, así que cada condición necesita su propio proceso — ver el
docstring de ab_interpretive.py).

Reemplaza los one-off bash sueltos usados en la sesión 2026-09-21: portable
(no depende de Git Bash) y **resumible** con --append — pensado para mover
esta corrida de una máquina a otra (ver docs/experiments/
2026-09-21-fase1-n15-repeticion.md, interrumpida en una máquina de 2 núcleos).

Uso:
    python scripts/run_ab_batch.py --seeds 42-56 --days 300 \
        --output data/metrics/ab_interpretive_fase1_n15.jsonl

    # Retomar un batch interrumpido sin repetir lo ya hecho:
    python scripts/run_ab_batch.py --seeds 42-56 --days 300 \
        --output data/metrics/ab_interpretive_fase1_n15.jsonl --append
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT      = Path(__file__).parent.parent
AB_SCRIPT = ROOT / "scripts" / "ab_interpretive.py"

_CONDITIONS: list[tuple[str, dict[str, str]]] = [
    ("OFF",    {"INTERPRETIVE_FILTER_ENABLED": "0", "MENTAL_VAULT_ENABLED": "0"}),
    ("FILTER", {"INTERPRETIVE_FILTER_ENABLED": "1", "MENTAL_VAULT_ENABLED": "0"}),
    ("VAULT",  {"INTERPRETIVE_FILTER_ENABLED": "1", "MENTAL_VAULT_ENABLED": "1"}),
]


def _parse_seeds(spec: str) -> list[int]:
    """Acepta '42,43,44' y/o rangos '42-56' (o una combinación: '42-46,50')."""
    seeds: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))
    return seeds


def _already_done(out_path: Path) -> set[tuple[int, bool, bool]]:
    done: set[tuple[int, bool, bool]] = set()
    if not out_path.exists():
        return done
    for line in out_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("AB_RESULT "):
            continue
        r = json.loads(line[len("AB_RESULT "):])
        done.add((r["seed"], bool(r["filter"]), bool(r["vault"])))
    return done


def main() -> None:
    p = argparse.ArgumentParser(description="Batch A/B de la Fase 1 — múltiples semillas x 3 condiciones")
    p.add_argument("--seeds",     default="42-56", help="Ej: '42-56' o '42,43,50'")
    p.add_argument("--days",      type=int, default=300)
    p.add_argument("--seed-file", default="data/seeds/rich_culture_100.yaml")
    p.add_argument("--output",    default="data/metrics/ab_interpretive_fase1_batch.jsonl")
    p.add_argument("--append",    action="store_true",
                    help="No trunca el output; salta combinaciones (seed, condición) ya presentes")
    args = p.parse_args()

    seeds    = _parse_seeds(args.seeds)
    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done = _already_done(out_path) if args.append else set()
    mode = "a" if args.append else "w"

    total = len(seeds) * len(_CONDITIONS)
    i = 0
    with open(out_path, mode, encoding="utf-8") as f:
        for seed in seeds:
            for label, env_extra in _CONDITIONS:
                i += 1
                filt  = env_extra["INTERPRETIVE_FILTER_ENABLED"] == "1"
                vault = env_extra["MENTAL_VAULT_ENABLED"] == "1"
                tag = f"[{i}/{total}] seed={seed} {label}"
                if (seed, filt, vault) in done:
                    print(f"{tag} -- ya en {args.output}, salteado")
                    continue

                env = os.environ.copy()
                env["AB_SEED"]      = str(seed)
                env["AB_DAYS"]      = str(args.days)
                env["AB_SEED_FILE"] = args.seed_file
                env.update(env_extra)

                t0 = time.time()
                print(f"{tag} ...", flush=True)
                proc = subprocess.run(
                    [sys.executable, str(AB_SCRIPT)],
                    cwd=str(ROOT), env=env, capture_output=True, text=True,
                )
                elapsed = time.time() - t0
                result_line = next(
                    (l for l in proc.stdout.splitlines() if l.startswith("AB_RESULT ")), None
                )
                if result_line is None:
                    print(f"  [ERROR] sin AB_RESULT tras {elapsed:.0f}s: {proc.stderr[-500:]}")
                    continue
                f.write(result_line + "\n")
                f.flush()
                print(f"  ok ({elapsed:.0f}s)")

    print(f"Listo. Resultados en {out_path}")


if __name__ == "__main__":
    main()
