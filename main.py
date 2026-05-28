#!/usr/bin/env python3
"""main.py — Llave maestra de PSYCHE SIMULACRA."""

import json
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

DB_PATH         = ROOT / "data" / "db" / "simulation.db"
CHECKPOINTS_DIR = ROOT / "data" / "checkpoints"
ARCHIVE_DIR     = ROOT / "data" / "archive"
VAULT_DIR       = ROOT / "vault"
SEEDS_DIR       = ROOT / "data" / "seeds"
SEEDS_FILE      = SEEDS_DIR / "initial_personas.yaml"
LIMINAL_SERVER  = ROOT / "liminal_server" / "main.py"


# ── Utilidades de archivo ─────────────────────────────────────────────────────

def _next_archive_name() -> str:
    import re
    existing = [
        d.name for d in ARCHIVE_DIR.iterdir()
        if d.is_dir() and re.fullmatch(r"Simulacion_\d+", d.name)
    ] if ARCHIVE_DIR.exists() else []
    nums = [int(n.split("_")[1]) for n in existing] if existing else [0]
    return f"Simulacion_{max(nums) + 1:02d}"


def archive_simulation(state: dict) -> Path:
    """Copia DB, checkpoints y vault a data/archive/Simulacion_XX/."""
    dest = ARCHIVE_DIR / _next_archive_name()
    dest.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        db_dest = dest / "db"
        db_dest.mkdir()
        shutil.copy2(DB_PATH, db_dest / DB_PATH.name)
        for ext in ("-wal", "-shm"):
            wal = Path(str(DB_PATH) + ext)
            if wal.exists():
                shutil.copy2(wal, db_dest / wal.name)

    if CHECKPOINTS_DIR.exists():
        cp_dest = dest / "checkpoints"
        cp_dest.mkdir()
        for f in CHECKPOINTS_DIR.glob("checkpoint_*.json"):
            shutil.copy2(f, cp_dest / f.name)

    if VAULT_DIR.exists():
        shutil.copytree(VAULT_DIR, dest / "vault", dirs_exist_ok=True)

    with open(dest / "meta.json", "w", encoding="utf-8") as f:
        json.dump({
            "dia_final":    state["dia"],
            "vivos":        state["vivos"],
            "total":        state["total"],
            "archivado_en": datetime.now().isoformat(),
        }, f, indent=2, ensure_ascii=False)

    return dest


def generate_seeds(n: int, seed: int) -> Path:
    """Genera un YAML de semillas con N agentes usando generate_personas.py."""
    out = SEEDS_DIR / f"_session_{n}ag_{seed}s.yaml"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "generate_personas.py"),
        "--n", str(n),
        "--seed", str(seed),
        "--output", str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"generate_personas.py falló: {result.stderr}")
    return out


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    from core.narrative.daemon import OllamaDaemon
    threading.Thread(target=OllamaDaemon().setup, daemon=True, name="ollama_setup").start()

    from ui.app_state import state
    from ui.psyche_ui import launch_ui
    launch_ui(state)


if __name__ == "__main__":
    main()
