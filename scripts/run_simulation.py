"""
run_simulation.py — Entry point principal de PSYCHE SIMULACRA.

Uso:
    python scripts/run_simulation.py                     # Nueva sesión, 30 días
    python scripts/run_simulation.py --days 120          # Nueva sesión, 120 días
    python scripts/run_simulation.py --resume            # Reanuda último checkpoint
    python scripts/run_simulation.py --resume --days 60  # Reanuda, 60 días más
    python scripts/run_simulation.py --seed 7 --days 10  # Semilla distinta
    python scripts/run_simulation.py --liminal           # Conectar a la Zona Liminal
"""

import argparse
import os
import sys
from pathlib import Path

# Asegurar que el raíz del proyecto esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.narrative.daemon import OllamaDaemon
from core.simulation import SimulationRunner


def _wire_liminal(runner: SimulationRunner, host: str, port: int, vault_path: str) -> None:
    """Instancia y registra la Zona Liminal en el clock del runner."""
    import time as _time
    from core.liminal.sim_identity import get_sim_id
    from core.liminal.portal_hex import PortalHex
    from core.liminal.liminal_client import LiminalClient
    from core.liminal.agent_transfer import AgentTransferHandler
    from core.liminal.dialogue_writer import DialogueWriter

    sim_id = get_sim_id()
    seed   = runner.world.seed if hasattr(runner.world, "seed") else 42
    portal = PortalHex(seed=seed)
    client = LiminalClient(sim_id=sim_id, seed=seed)
    client.start(host=host, port=port)
    _time.sleep(0.5)   # dar tiempo a la conexión WebSocket

    writer   = DialogueWriter(vault_path=vault_path)
    handler  = AgentTransferHandler(
        agent_core      = runner.agents,
        portal          = portal,
        client          = client,
        dialogue_writer = writer,
    )
    runner.clock.on_tick(handler.on_tick, priority=25)
    runner.clock.on_day(handler.on_day,   priority=25)
    print(f"  [Liminal] Conectado a ws://{host}:{port} | SIM_ID={sim_id}")


def main() -> None:
    OllamaDaemon().setup()

    parser = argparse.ArgumentParser(
        description="PSYCHE SIMULACRA — Motor de simulación ABM jungiano"
    )
    parser.add_argument("--resume", action="store_true",
                        help="Reanudar desde el checkpoint más reciente")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path a un checkpoint específico para reanudar")
    parser.add_argument("--days", type=int, default=30,
                        help="Número de días simulados a correr (default: 30)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Semilla aleatoria (solo para nueva sesión, default: 42)")
    parser.add_argument("--seeds-file", type=str, default="data/seeds/initial_personas.yaml",
                        help="Archivo YAML de agentes iniciales")
    parser.add_argument("--db", type=str, default=None,
                        help="Path a la base de datos SQLite")
    parser.add_argument("--checkpoints-dir", type=str, default=None,
                        help="Directorio de checkpoints")
    parser.add_argument("--vault-dir", type=str, default=None,
                        help="Directorio del vault Obsidian (default: VAULT_PATH env o 'vault')")
    # Zona Liminal
    parser.add_argument("--liminal", action="store_true",
                        help="Conectar a la Zona Liminal")
    parser.add_argument("--liminal-host", type=str, default="localhost",
                        help="Host del servidor liminal (default: localhost)")
    parser.add_argument("--liminal-port", type=int, default=8765,
                        help="Puerto del servidor liminal (default: 8765)")
    args = parser.parse_args()

    # Resolver rutas con defaults que respetan SIM_DATA_DIR
    data_base     = os.environ.get("SIM_DATA_DIR", "data")
    db_path       = args.db            or f"{data_base}/db/simulation.db"
    cp_dir        = args.checkpoints_dir or f"{data_base}/checkpoints"
    vault_path    = args.vault_dir     or os.environ.get("VAULT_PATH", "vault")

    if args.resume or args.checkpoint:
        print("Reanudando desde checkpoint...")
        runner = SimulationRunner.resume(
            checkpoint_path = args.checkpoint,
            db_path         = db_path,
            checkpoint_dir  = cp_dir,
            vault_path      = vault_path,
        )
    else:
        print(f"Nueva sesión | seed={args.seed} | agentes desde: {args.seeds_file}")
        runner = SimulationRunner.new_session(
            seed_file      = args.seeds_file,
            seed           = args.seed,
            db_path        = db_path,
            checkpoint_dir = cp_dir,
            vault_path     = vault_path,
        )

    if args.liminal:
        _wire_liminal(runner, args.liminal_host, args.liminal_port, vault_path)

    n_agentes = len(runner.agents.agents)
    if args.days <= 0:
        print(f"Agentes cargados: {n_agentes} | Corriendo indefinidamente...")
        print("(Ctrl+C para parar limpiamente y guardar checkpoint)\n")
        runner.run(n_days=None)
    else:
        print(f"Agentes cargados: {n_agentes} | Corriendo {args.days} días simulados...")
        print("(Ctrl+C para parar limpiamente y guardar checkpoint)\n")
        runner.run(n_days=args.days)

    vivos   = runner.alive_count
    muertes = n_agentes - vivos
    dia     = runner.current_dia
    print(f"\nSimulación finalizada.")
    print(f"  Día simulado: {dia}")
    print(f"  Agentes vivos: {vivos}/{n_agentes} ({muertes} muertes)")
    print(f"  BD: {runner.db.path}")


if __name__ == "__main__":
    main()
