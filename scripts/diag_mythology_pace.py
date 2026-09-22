"""
Diagnóstico de ritmo de cristalización mítica — headless, sin BD ni narrativa.

Mide cuántos ProtoMitos cristalizan (y cuántos se vuelven leyenda) a lo largo
de la simulación, ahora que on_social_transmission() se dispara desde los tres
tipos de encuentro más intensos (choque_violento, conflicto_explotacion,
cooperacion_pura) en vez de solo choque_violento.

Objetivo de referencia (Roadmap 7): 3000-6000 días → >=3 mitos/leyendas.

Uso:
    python scripts/diag_mythology_pace.py --seed 42 --days 3000
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.time import SimulationClock, ClockPriority
from core.world import WorldCore
from core.agents import AgentCore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--days", type=int, default=3000)
    parser.add_argument("--seed-file", default="data/seeds/rich_culture_100.yaml")
    parser.add_argument("--checkpoint-every", type=int, default=250)
    args = parser.parse_args()

    world  = WorldCore(seed=args.seed)
    agents = AgentCore.from_yaml(args.seed_file, world, seed=args.seed)
    clock  = SimulationClock(start_dia=0, start_hora=6)

    clock.on_tick(world.on_tick,  priority=ClockPriority.WORLD)
    clock.on_day(world.on_day,    priority=ClockPriority.WORLD)
    clock.on_tick(agents.on_tick, priority=ClockPriority.AGENT)
    clock.on_day(agents.on_day,   priority=ClockPriority.AGENT)
    clock.on_season_change(world.on_season_change,  priority=ClockPriority.WORLD)
    clock.on_season_change(agents.on_season_change, priority=ClockPriority.AGENT)

    myth = agents.mythology_engine
    first_crystal_day: int | None = None
    first_legend_day: int | None = None

    def _checkpoint(tp) -> None:
        nonlocal first_crystal_day, first_legend_day
        dia = tp.dia_simulado
        n_crystal = len(myth.active_myths)
        n_legend  = sum(1 for m in myth.active_myths if m.es_leyenda)
        if n_crystal > 0 and first_crystal_day is None:
            first_crystal_day = dia
        if n_legend > 0 and first_legend_day is None:
            first_legend_day = dia
        if dia % args.checkpoint_every == 0:
            n_proto = len(myth.proto_myths)
            coh_max = max((p.coherencia for p in myth.proto_myths), default=0.0)
            print(f"  dia={dia:5d}  proto={n_proto}  coh_max={coh_max:.2f}  "
                  f"cristalizados={n_crystal}  leyendas={n_legend}", flush=True)

    def _stopper(tp) -> None:
        if tp.dia_simulado >= args.days:
            clock.shutdown()

    def _extinction(tp) -> None:
        if agents.alive_count() == 0:
            print("  [extinción de la población]")
            clock.shutdown()

    clock.on_day(_checkpoint,  priority=ClockPriority.PERSISTENCE)
    clock.on_day(_stopper,     priority=ClockPriority.STOPPER)
    clock.on_day(_extinction,  priority=ClockPriority.EXTINCTION)

    print(f"[Diag mitología] seed={args.seed} days={args.days} seed_file={args.seed_file}")
    t0 = time.time()
    try:
        clock.start()
    except KeyboardInterrupt:
        pass
    elapsed = time.time() - t0

    n_crystal = len(myth.active_myths)
    n_legend  = sum(1 for m in myth.active_myths if m.es_leyenda)
    print(f"\n[Diag mitología] elapsed={elapsed:.1f}s")
    print(f"  Mitos cristalizados al final: {n_crystal}")
    print(f"  Leyendas al final:            {n_legend}")
    print(f"  Primer mito cristalizado:     día {first_crystal_day}")
    print(f"  Primera leyenda:              día {first_legend_day}")


if __name__ == "__main__":
    main()
