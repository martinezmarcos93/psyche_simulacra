from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.world import WorldCore
    from core.agents import AgentCore
    from .database import DatabaseManager

_KEEP_N_DEFAULT = 5
_CHECKPOINT_FIELDS = ("checkpoint_id", "dia_simulado", "agentes", "world", "reloj")


class CheckpointManager:
    """
    Guardado y carga atómica del estado completo de la simulación.

    Estrategia de escritura segura:
      1. Escribir a archivo temporal (.tmp)
      2. os.replace() al path final — atómico en POSIX y Windows 10+
      Resultado: nunca hay un checkpoint parcialmente escrito.
    """

    def __init__(
        self,
        checkpoint_dir: str = "data/checkpoints",
        db: DatabaseManager | None = None,
    ) -> None:
        self._dir = Path(checkpoint_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db  = db

    # ── Guardado ──────────────────────────────────────────────────────────────

    def save(
        self,
        world:      WorldCore,
        agents:     AgentCore,
        clock_dict: dict,
        session_id: str = "",
        reason:     str = "auto",
    ) -> Path:
        """
        Serializa y guarda el estado completo.
        Devuelve el path del archivo escrito.
        """
        checkpoint_id = str(uuid.uuid4())
        dia           = clock_dict.get("dia_simulado", 0)
        hora          = clock_dict.get("hora_del_dia", 0)

        data = {
            "checkpoint_id":  checkpoint_id,
            "dia_simulado":   dia,
            "hora_simulada":  hora,
            "timestamp_real": datetime.now(timezone.utc).isoformat(),
            "session_id":     session_id,
            "razon":          reason,
            "reloj":          clock_dict,
            "world":          world.full_state_dict(),
            "agentes":        agents.to_dict(),
        }

        filename   = f"checkpoint_{dia:05d}_{checkpoint_id[:8]}.json"
        final_path = self._dir / filename
        temp_path  = self._dir / f"_tmp_{checkpoint_id}.json"

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, default=_json_default)
            os.replace(temp_path, final_path)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

        if self._db is not None:
            self._db.insert_checkpoint_meta({
                "checkpoint_id":  checkpoint_id,
                "dia_simulado":   dia,
                "hora_simulada":  hora,
                "timestamp_real": data["timestamp_real"],
                "session_id":     session_id,
                "razon":          reason,
                "archivo_json":   str(final_path),
            })

        return final_path

    # ── Carga ─────────────────────────────────────────────────────────────────

    def load_latest(self) -> dict:
        """Carga el checkpoint más reciente (por nombre de archivo, que incluye el día)."""
        candidates = sorted(self._dir.glob("checkpoint_*.json"), reverse=True)
        if not candidates:
            raise FileNotFoundError(
                f"No hay checkpoints en '{self._dir}'. Primera ejecución."
            )
        path = candidates[0]
        ok, msg = self.verify(path)
        if not ok:
            raise ValueError(f"Checkpoint corrupto ({path}): {msg}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def load(self, path: str | Path) -> dict:
        path = Path(path)
        ok, msg = self.verify(path)
        if not ok:
            raise ValueError(f"Checkpoint corrupto ({path}): {msg}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ── Verificación ─────────────────────────────────────────────────────────

    def verify(self, path: str | Path) -> tuple[bool, str]:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for field in _CHECKPOINT_FIELDS:
                if field not in data:
                    return False, f"campo faltante: {field}"
            if not isinstance(data.get("agentes", {}).get("agents"), list):
                return False, "agentes.agents debe ser una lista"
            if data["dia_simulado"] < 0:
                return False, "dia_simulado negativo"
            return True, "ok"
        except Exception as exc:
            return False, str(exc)

    # ── Gestión de archivos ───────────────────────────────────────────────────

    def list_checkpoints(self) -> list[Path]:
        return sorted(self._dir.glob("checkpoint_*.json"), reverse=True)

    def prune(self, keep_n: int = _KEEP_N_DEFAULT) -> list[Path]:
        """Elimina los más antiguos, conservando los últimos keep_n."""
        all_cp  = self.list_checkpoints()
        to_delete = all_cp[keep_n:]
        for p in to_delete:
            p.unlink(missing_ok=True)
        return to_delete


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json_default(obj: object) -> object:
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"No serializable: {type(obj)}")
