"""
Arnés A/B para la Fase 1 (InterpretiveFilter).

Corre una simulación headless (sin BD, narrativa ni Obsidian) y reporta las
métricas de emergencia agregadas. El flag INTERPRETIVE_FILTER_ENABLED se lee al
importar core.agents, así que cada condición (OFF/ON) se ejecuta en su propio
proceso con el env var distinto. Mismo seed → mismas condiciones iniciales →
la única diferencia es la ecuación personal.

Uso:
    INTERPRETIVE_FILTER_ENABLED=0 python scripts/ab_interpretive.py
    INTERPRETIVE_FILTER_ENABLED=1 python scripts/ab_interpretive.py

Salida: una línea JSON precedida por "AB_RESULT " con los agregados.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.time import SimulationClock, ClockPriority
from core.world import WorldCore
from core.agents import AgentCore
from core.metrics import EmergenceMetrics

_SEED      = int(os.environ.get("AB_SEED", "42"))
_DAYS      = int(os.environ.get("AB_DAYS", "300"))
_SEED_FILE = os.environ.get("AB_SEED_FILE", "data/seeds/rich_culture_100.yaml")


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def main() -> None:
    flag = os.environ.get("INTERPRETIVE_FILTER_ENABLED", "0").strip() not in ("0", "false", "no")
    vault = (
        os.environ.get("MENTAL_VAULT_ENABLED", "0").strip() not in ("0", "false", "no")
        and flag
    )

    world  = WorldCore(seed=_SEED)
    agents = AgentCore.from_yaml(_SEED_FILE, world, seed=_SEED)
    clock  = SimulationClock(start_dia=0, start_hora=6)
    metrics = EmergenceMetrics()

    clock.on_tick(world.on_tick,  priority=ClockPriority.WORLD)
    clock.on_day(world.on_day,    priority=ClockPriority.WORLD)
    clock.on_tick(agents.on_tick, priority=ClockPriority.AGENT)
    clock.on_day(agents.on_day,   priority=ClockPriority.AGENT)
    clock.on_season_change(world.on_season_change,  priority=ClockPriority.WORLD)
    clock.on_season_change(agents.on_season_change, priority=ClockPriority.AGENT)

    series: list = []

    def _collect(tp) -> None:
        dm = metrics.compute_day(
            dia=tp.dia_simulado,
            agents=agents.agents,
            tribe_manager=agents.tribe_manager,
            collective_field=agents.collective_field,
            culture_engine=agents.culture_engine,
        )
        series.append(dm)

    def _stopper(tp) -> None:
        if tp.dia_simulado >= _DAYS:
            clock.shutdown()

    def _extinction(tp) -> None:
        if agents.alive_count() == 0:
            clock.shutdown()

    clock.on_day(_collect,    priority=ClockPriority.PERSISTENCE)
    clock.on_day(_stopper,    priority=ClockPriority.STOPPER)
    clock.on_day(_extinction, priority=ClockPriority.EXTINCTION)

    t0 = time.time()
    try:
        clock.start()
    except KeyboardInterrupt:
        pass
    elapsed = time.time() - t0

    # Agregar sobre el último cuartil (estado estacionario, tras el transitorio de
    # formación de tribus que confunde las medias tempranas).
    q4 = series[3 * len(series) // 4:] or series
    result = {
        "filter":          flag,
        "vault":           vault,
        "seed":            _SEED,
        "days_run":        len(series),
        "elapsed_s":       round(elapsed, 1),
        "final_alive":     series[-1].n_alive if series else 0,
        # Divergencia cultural normalizada (menos sensible al nº de tribus): MIG e IMI.
        # KL crudo se reporta junto a n_tribes para poder controlar el confound.
        "kl_mean_q4":      round(_mean([m.kl_mean for m in q4]), 6),
        "kl_max_q4":       round(_mean([m.kl_max for m in q4]), 6),
        "mig_q4":          round(_mean([m.mig for m in q4]), 6),
        "imi_q4":          round(_mean([m.imi for m in q4]), 6),
        "vfe_global_q4":   round(_mean([m.vfe_global for m in q4]), 6),
        "n_tribes_q4":     round(_mean([m.n_tribes for m in q4]), 3),
        # KL normalizada por el nº de tribus (control aproximado del confound)
        "kl_per_tribe_q4": round(_mean([m.kl_mean for m in q4]) / max(1.0, _mean([m.n_tribes for m in q4])), 6),
        # ── Instrumento de la Ecuación Personal (camino c) ───────────────────────
        # Lo que el filtro/vault SÍ cambian primero: conducta, campo y afecto.
        "behavioral_kl_q4": round(_mean([m.behavioral_kl_mean for m in q4]), 6),
        "field_kl_q4":      round(_mean([m.field_kl_mean for m in q4]), 6),
        "valence_std_q4":   round(_mean([m.valence_std for m in q4]), 6),
        "arousal_std_q4":   round(_mean([m.arousal_std for m in q4]), 6),
        "worldview_coh_q4": round(_mean([m.worldview_coherence_mean for m in q4]), 6),
    }
    print("AB_RESULT " + json.dumps(result))


if __name__ == "__main__":
    main()
