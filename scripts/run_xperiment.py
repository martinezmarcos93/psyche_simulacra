"""
run_xperiment.py — Lanzador del experimento de diálogo inter-civilizacional.

Levanta dos instancias de PSYCHE SIMULACRA con modelos de IA diferentes y las
conecta a través de la Zona Liminal. Cuando agentes de distintas civilizaciones
se encuentran en el espacio liminal, sus respectivas IAs dialogan.

Uso:
    python scripts/run_xperiment.py
    python scripts/run_xperiment.py --days 200
    python scripts/run_xperiment.py --model-a llama3.2:1b --model-b phi3
    python scripts/run_xperiment.py --agents-a 50 --agents-b 50

Estructura de datos generada:
    data_a/   vault_a/   → Simulación A (llama3.2:1b, seed 42)
    data_b/   vault_b/   → Simulación B (phi3, seed 7)
    dialogues/           → Transcripciones JSON del servidor liminal
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).parent.parent)
PYTHON       = sys.executable
RUN_SIM      = str(Path(PROJECT_ROOT) / "scripts" / "run_simulation.py")
LIMINAL_SRV  = str(Path(PROJECT_ROOT) / "liminal_server" / "main.py")


def wait_for_port(port: int, timeout: float = 15.0) -> bool:
    """Espera hasta que el puerto TCP esté escuchando."""
    import socket
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PSYCHE SIMULACRA — Experimento de diálogo inter-civilizacional"
    )
    parser.add_argument("--days", type=int, default=0,
                        help="Días a simular por instancia (0 = indefinido, default: 0)")
    parser.add_argument("--model-a", type=str, default="llama3.2:1b",
                        help="Modelo Ollama para la Simulación A (default: llama3.2:1b)")
    parser.add_argument("--model-b", type=str, default="phi3",
                        help="Modelo Ollama para la Simulación B (default: phi3)")
    parser.add_argument("--seed-a", type=int, default=42,
                        help="Semilla de la Simulación A (default: 42)")
    parser.add_argument("--seed-b", type=int, default=7,
                        help="Semilla de la Simulación B (default: 7)")
    parser.add_argument("--seeds-file", type=str,
                        default="data/seeds/100_personas.yaml",
                        help="Archivo YAML de agentes (default: 100_personas.yaml)")
    parser.add_argument("--liminal-port", type=int, default=8765,
                        help="Puerto del servidor liminal (default: 8765)")
    args = parser.parse_args()

    procs: list[subprocess.Popen] = []

    def _cleanup(signum=None, frame=None):
        print("\n[xperiment] Deteniendo todos los procesos...")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in procs:
            try:
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("[xperiment] Terminado.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    # ── 1. Servidor liminal ───────────────────────────────────────────────────

    print(f"[xperiment] Levantando servidor liminal en puerto {args.liminal_port}...")
    liminal_proc = subprocess.Popen(
        [PYTHON, LIMINAL_SRV, "--port", str(args.liminal_port)],
        cwd=PROJECT_ROOT,
    )
    procs.append(liminal_proc)

    if not wait_for_port(args.liminal_port, timeout=15.0):
        print(f"[xperiment] ERROR: el servidor liminal no levantó en el puerto {args.liminal_port}")
        _cleanup()
    print(f"[xperiment] Servidor liminal activo en ws://localhost:{args.liminal_port}")

    # ── 2. Simulación A ───────────────────────────────────────────────────────

    env_a = {
        **os.environ,
        "OLLAMA_MODEL":  args.model_a,
        "SIM_DATA_DIR":  "data_a",
        "VAULT_PATH":    "vault_a",
        "NARRATIVE_ENABLED": "1",
    }
    cmd_a = [
        PYTHON, RUN_SIM,
        "--seed",           str(args.seed_a),
        "--days",           str(args.days),
        "--db",             "data_a/db/simulation.db",
        "--checkpoints-dir","data_a/checkpoints",
        "--vault-dir",      "vault_a",
        "--seeds-file",     args.seeds_file,
        "--liminal",
        "--liminal-host",   "localhost",
        "--liminal-port",   str(args.liminal_port),
    ]
    print(f"[xperiment] Levantando Sim A  (model={args.model_a}, seed={args.seed_a})...")
    sim_a_proc = subprocess.Popen(cmd_a, env=env_a, cwd=PROJECT_ROOT)
    procs.append(sim_a_proc)
    time.sleep(3)   # stagger el inicio para evitar race conditions en el servidor

    # ── 3. Simulación B ───────────────────────────────────────────────────────

    env_b = {
        **os.environ,
        "OLLAMA_MODEL":  args.model_b,
        "SIM_DATA_DIR":  "data_b",
        "VAULT_PATH":    "vault_b",
        "NARRATIVE_ENABLED": "1",
    }
    cmd_b = [
        PYTHON, RUN_SIM,
        "--seed",           str(args.seed_b),
        "--days",           str(args.days),
        "--db",             "data_b/db/simulation.db",
        "--checkpoints-dir","data_b/checkpoints",
        "--vault-dir",      "vault_b",
        "--seeds-file",     args.seeds_file,
        "--liminal",
        "--liminal-host",   "localhost",
        "--liminal-port",   str(args.liminal_port),
    ]
    print(f"[xperiment] Levantando Sim B  (model={args.model_b}, seed={args.seed_b})...")
    sim_b_proc = subprocess.Popen(cmd_b, env=env_b, cwd=PROJECT_ROOT)
    procs.append(sim_b_proc)

    print()
    print("═" * 60)
    print("  PSYCHE SIMULACRA — Xperiment corriendo")
    print(f"  Sim A  ← {args.model_a}  (seed {args.seed_a})")
    print(f"  Sim B  ← {args.model_b}  (seed {args.seed_b})")
    print(f"  Liminal ← ws://localhost:{args.liminal_port}")
    print()
    print("  Diálogos registrados en:  dialogues/")
    print("  Vault A en:               vault_a/Liminal/Dialogos/")
    print("  Vault B en:               vault_b/Liminal/Dialogos/")
    print("  Ctrl+C para detener todo")
    print("═" * 60)
    print()

    # Esperar a que alguno termine o el usuario interrumpa
    try:
        while True:
            for p in procs:
                if p.poll() is not None:
                    print(f"[xperiment] Proceso terminó (returncode={p.returncode}). Cerrando todo.")
                    _cleanup()
            time.sleep(2)
    except KeyboardInterrupt:
        _cleanup()


if __name__ == "__main__":
    main()
