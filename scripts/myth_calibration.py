"""
Arnés de calibración — mide la tasa de cristalización mítica tras la extensión
de MythologyEngine.on_social_transmission() a cooperación pura y
conflicto/explotación (ver docs/handoffs/2026-09-21.md §7, prioridad media).

Corre una simulación headless (sin BD/narrativa/UI, igual patrón que
scripts/ab_interpretive.py) y reporta, por semilla:

    - día de la primera cristalización (o None si no cristalizó nada);
    - número total de MythCrystal (activos + leyendas) al final;
    - tipos de mito cristalizados (cobertura de los 5 tipos Campbell);
    - día final alcanzado (por si hay extinción antes de completar los días
      pedidos).

Objetivo original del Roadmap 7: 3000-6000 días -> >= 3 mitos/leyendas.
No reemplaza scripts/run_robustness.py (ese mide emergencia general, no
mitología en particular); este es un instrumento específico y más barato
para esta pregunta puntual.

Uso:
    python scripts/myth_calibration.py --seeds 42,1337,9999 --days 4000
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows: consola cp1252 no imprime el emoji narrativo de algunos
# subsistemas (objetos sagrados, deidades) — evita un UnicodeEncodeError
# ajeno a la calibración en corridas largas.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.time import SimulationClock, ClockPriority
from core.world import WorldCore
from core.agents import AgentCore


def _run_one(seed: int, n_days: int, seed_file: str) -> dict:
    world  = WorldCore(seed=seed)
    agents = AgentCore.from_yaml(seed_file, world, seed=seed)
    clock  = SimulationClock(start_dia=0, start_hora=6)

    clock.on_tick(world.on_tick,  priority=ClockPriority.WORLD)
    clock.on_day(world.on_day,    priority=ClockPriority.WORLD)
    clock.on_tick(agents.on_tick, priority=ClockPriority.AGENT)
    clock.on_day(agents.on_day,   priority=ClockPriority.AGENT)
    clock.on_season_change(world.on_season_change,  priority=ClockPriority.WORLD)
    clock.on_season_change(agents.on_season_change, priority=ClockPriority.AGENT)

    state = {"first_crystal_day": None, "n_crystals_seen": 0}

    def _watch(tp) -> None:
        n_now = len(agents.mythology_engine.active_myths)
        if n_now > state["n_crystals_seen"]:
            if state["first_crystal_day"] is None:
                state["first_crystal_day"] = tp.dia_simulado
            state["n_crystals_seen"] = n_now

    def _stopper(tp) -> None:
        if tp.dia_simulado >= n_days:
            clock.shutdown()

    def _extinction(tp) -> None:
        if agents.alive_count() == 0:
            clock.shutdown()

    clock.on_day(_watch,      priority=ClockPriority.PERSISTENCE)
    clock.on_day(_stopper,    priority=ClockPriority.STOPPER)
    clock.on_day(_extinction, priority=ClockPriority.EXTINCTION)

    t0 = time.time()
    try:
        clock.start()
    except KeyboardInterrupt:
        pass
    elapsed = time.time() - t0

    myths = agents.mythology_engine.active_myths
    tipos = sorted({m.tipo for m in myths})
    n_leyendas = sum(1 for m in myths if m.es_leyenda)

    return {
        "seed":              seed,
        "days_requested":    n_days,
        "final_dia":         clock.now.dia_simulado,
        "final_alive":       agents.alive_count(),
        "elapsed_s":         round(elapsed, 1),
        "first_crystal_day": state["first_crystal_day"],
        "n_myths_total":     len(myths),
        "n_legends":         n_leyendas,
        "n_proto_myths":     len(agents.mythology_engine.proto_myths),
        "tipos_cristalizados": tipos,
        "meets_roadmap7_target": len(myths) >= 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibración de cristalización mítica")
    parser.add_argument("--seeds",     default="42",   help="Semillas separadas por coma")
    parser.add_argument("--days",      type=int, default=4000)
    parser.add_argument("--seed-file", default="data/seeds/rich_culture_100.yaml")
    args = parser.parse_args()

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    results = []
    for seed in seeds:
        print(f"[MythCalibration] seed={seed} days={args.days} ...", flush=True)
        r = _run_one(seed, args.days, args.seed_file)
        results.append(r)
        print("MYTH_RESULT " + json.dumps(r), flush=True)

    n_meeting = sum(1 for r in results if r["meets_roadmap7_target"])
    print(json.dumps({
        "summary": {
            "n_seeds":              len(results),
            "n_meeting_target":     n_meeting,
            "mean_n_myths":         round(sum(r["n_myths_total"] for r in results) / len(results), 2),
        }
    }))


if __name__ == "__main__":
    main()
