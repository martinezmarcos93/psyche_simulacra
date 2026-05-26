#!/usr/bin/env python3
"""
ui/launch.py — Lanza PSYCHE SIMULACRA con interfaz NiceGUI.

La simulación corre en un hilo background; NiceGUI ocupa el hilo principal.
Cuando se cierra el browser, el proceso termina en ~5 segundos.

Uso:
    python ui/launch.py               # retoma checkpoint existente
    python ui/launch.py --new         # nueva simulación (requiere semillas)
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH        = ROOT / "data" / "db" / "simulation.db"
CHECKPOINT_DIR = ROOT / "data" / "checkpoints"


def main() -> None:
    from core.simulation import SimulationRunner
    from core.runtime.psyche_runtime import PsycheRuntime
    from ui.psyche_ui import launch_ui

    new_session = "--new" in sys.argv

    if new_session:
        seeds = ROOT / "data" / "seeds" / "initial_personas.yaml"
        if not seeds.exists():
            print(f"ERROR: archivo de semillas no encontrado: {seeds}")
            sys.exit(1)
        runner = SimulationRunner.new_session(
            seed_file      = str(seeds),
            seed           = 42,
            db_path        = str(DB_PATH),
            checkpoint_dir = str(CHECKPOINT_DIR),
        )
    else:
        runner = SimulationRunner.resume(
            db_path        = str(DB_PATH),
            checkpoint_dir = str(CHECKPOINT_DIR),
        )

    runtime = PsycheRuntime()
    runtime.attach_runner(runner)

    # Simulación en hilo background (daemon → termina con el proceso principal)
    stop_event = threading.Event()

    def run_sim() -> None:
        try:
            runner.run(n_days=None)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[sim] Error: {e}")
        finally:
            stop_event.set()

    sim_thread = threading.Thread(target=run_sim, daemon=True, name="sim_worker")
    sim_thread.start()

    # NiceGUI en hilo principal (bloqueante)
    # reconnect_timeout: termina el proceso 5s después de que todos los browsers cierren
    try:
        launch_ui(runtime, runner)
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    main()
