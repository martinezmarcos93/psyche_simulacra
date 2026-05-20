"""
run_simulation.py — Entry point principal de PSYCHE SIMULACRA.

Uso:
    python scripts/run_simulation.py                     # Nueva sesión, 30 días
    python scripts/run_simulation.py --days 120          # Nueva sesión, 120 días
    python scripts/run_simulation.py --resume            # Reanuda último checkpoint
    python scripts/run_simulation.py --resume --days 60  # Reanuda, 60 días más
    python scripts/run_simulation.py --seed 7 --days 10  # Semilla distinta
"""

import argparse
import sys
from pathlib import Path

# Asegurar que el raíz del proyecto esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simulation import SimulationRunner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PSYCHE SIMULACRA — Motor de simulación ABM jungiano"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Reanudar desde el checkpoint más reciente"
    )
    parser.add_argument(
        "--checkpoint", type=str, default=None,
        help="Path a un checkpoint específico para reanudar"
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="Número de días simulados a correr (default: 30)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Semilla aleatoria (solo para nueva sesión, default: 42)"
    )
    parser.add_argument(
        "--seeds-file", type=str, default="data/seeds/initial_personas.yaml",
        help="Archivo YAML de agentes iniciales"
    )
    parser.add_argument(
        "--db", type=str, default="data/db/simulation.db",
        help="Path a la base de datos SQLite"
    )
    parser.add_argument(
        "--checkpoints-dir", type=str, default="data/checkpoints",
        help="Directorio de checkpoints"
    )
    args = parser.parse_args()

    if args.resume or args.checkpoint:
        print(f"Reanudando desde checkpoint...")
        runner = SimulationRunner.resume(
            checkpoint_path = args.checkpoint,
            db_path         = args.db,
            checkpoint_dir  = args.checkpoints_dir,
        )
    else:
        print(f"Nueva sesión | seed={args.seed} | agentes desde: {args.seeds_file}")
        runner = SimulationRunner.new_session(
            seed_file      = args.seeds_file,
            seed           = args.seed,
            db_path        = args.db,
            checkpoint_dir = args.checkpoints_dir,
        )

    n_agentes = len(runner.agents.agents)
    print(f"Agentes cargados: {n_agentes} | Corriendo {args.days} días simulados...")
    print("(Ctrl+C para parar limpiamente y guardar checkpoint)\n")

    runner.run(n_days=args.days)

    vivos  = runner.alive_count
    muertes = n_agentes - vivos
    dia     = runner.current_dia
    print(f"\nSimulación finalizada.")
    print(f"  Día simulado: {dia}")
    print(f"  Agentes vivos: {vivos}/{n_agentes} ({muertes} muertes)")
    print(f"  BD: {runner.db.path}")


if __name__ == "__main__":
    main()
