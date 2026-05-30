#!/usr/bin/env python3
"""run_overnight.py — Simulación headless con auto-stop por hora real."""

import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

SEED_FILE = ROOT / "data" / "seeds" / "rich_culture_100.yaml"
STOP_HOUR = 4   # 04:00 AM
REPORT_EVERY = 100  # días simulados entre líneas de progreso


def _build_stop_time(stop_hour: int) -> datetime.datetime:
    now  = datetime.datetime.now()
    stop = now.replace(hour=stop_hour, minute=0, second=0, microsecond=0)
    if now >= stop:
        stop += datetime.timedelta(days=1)
    return stop


def main() -> None:
    from core.simulation import SimulationRunner
    from core.time import TimePoint

    stop_time = _build_stop_time(STOP_HOUR)

    print(f"\n{'='*60}")
    print(f"  PSYCHE SIMULACRA — Simulación nocturna")
    print(f"  Seed: {SEED_FILE.name}")
    print(f"  Inicio:           {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"  Stop programado:  {stop_time.strftime('%H:%M:%S del %d/%m/%Y')}")
    print(f"{'='*60}\n")

    runner = SimulationRunner.new_session(seed_file=str(SEED_FILE))

    # ── Stopper por tiempo real (prioridad 98, antes del STOPPER normal=99) ──
    def _time_stopper(tp: TimePoint) -> None:
        if datetime.datetime.now() >= stop_time:
            elapsed = datetime.datetime.now() - (stop_time - datetime.timedelta(hours=STOP_HOUR))
            print(
                f"\n[⏰] {stop_time.strftime('%H:%M')} alcanzado"
                f" en día simulado {tp.dia_simulado}."
                f" Guardando checkpoint y cerrando..."
            )
            runner.clock.shutdown()

    runner.clock.on_day(_time_stopper, priority=98)

    # ── Reporte de progreso cada REPORT_EVERY días ───────────────────────────
    last_report = [0]

    def _progress(tp: TimePoint) -> None:
        if tp.dia_simulado - last_report[0] >= REPORT_EVERY:
            last_report[0] = tp.dia_simulado
            vivos   = runner.alive_count
            total   = len(runner.agents.agents)
            now_str = datetime.datetime.now().strftime('%H:%M')
            mins_left = int((stop_time - datetime.datetime.now()).total_seconds() / 60)
            print(
                f"[{now_str}] Día {tp.dia_simulado:>5}"
                f"  |  vivos: {vivos}/{total}"
                f"  |  {mins_left} min restantes"
            )

    runner.clock.on_day(_progress, priority=50)

    runner.run()

    print(f"\n{'='*60}")
    print(f"  Simulación detenida a las {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"  Checkpoint en: data/checkpoints/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
