"""
core/liminal/sim_identity.py — Identidad global de esta instancia de simulación.

El SIM_ID se genera la primera vez y se guarda en data/sim_id.txt.
En ejecuciones posteriores, se carga desde ese archivo.
El formato es: SIM:<8 chars del hostname>:<uuid4 corto>
"""

from __future__ import annotations

import socket
import uuid
from pathlib import Path

_SIM_ID_FILE = Path("data") / "sim_id.txt"


def load_or_create_sim_id() -> str:
    """
    Carga el SIM_ID desde disco si existe, o lo genera y guarda.
    Siempre retorna el mismo ID para esta instalación.
    """
    if _SIM_ID_FILE.exists():
        sim_id = _SIM_ID_FILE.read_text(encoding="utf-8").strip()
        if sim_id:
            return sim_id

    # Generar nuevo ID
    hostname = socket.gethostname()[:8].replace(" ", "_")
    uid      = str(uuid.uuid4())[:8]
    sim_id   = f"SIM:{hostname}:{uid}"

    _SIM_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SIM_ID_FILE.write_text(sim_id, encoding="utf-8")

    return sim_id


def get_sim_id() -> str:
    """Atajo — carga o crea el SIM_ID de esta instalación."""
    return load_or_create_sim_id()
