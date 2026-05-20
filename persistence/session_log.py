from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .database import DatabaseManager

_VERSION = "0.1.0"


class SessionLog:
    """
    Registra metadata de la sesión en curso.
    Una sesión = una ejecución del proceso (run.py / resume.py).
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db              = db
        self._session_id:     str   = ""
        self._start_time:     float = 0.0
        self._dia_inicio:     int   = 0
        self._dias_procesados: int  = 0
        self._muertes:        int   = 0
        self._nacimientos:    int   = 0
        self._active:         bool  = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self, dia_inicio: int = 0, session_id: str | None = None) -> str:
        self._session_id      = session_id or str(uuid.uuid4())
        self._start_time      = time.monotonic()
        self._dia_inicio      = dia_inicio
        self._dias_procesados = 0
        self._muertes         = 0
        self._nacimientos     = 0
        self._active          = True

        self._db.upsert_session({
            "session_id":           self._session_id,
            "timestamp_inicio":     datetime.now(timezone.utc).isoformat(),
            "dia_inicio_simulado":  dia_inicio,
            "version_motor":        _VERSION,
        })
        return self._session_id

    def record_day(self) -> None:
        self._dias_procesados += 1

    def record_death(self) -> None:
        self._muertes += 1

    def record_birth(self) -> None:
        self._nacimientos += 1

    def close(self, dia_actual: int = 0, razon: str = "normal") -> None:
        if not self._active:
            return
        self._active = False
        elapsed = time.monotonic() - self._start_time
        self._db.upsert_session({
            "session_id":               self._session_id,
            "timestamp_inicio":         "",  # ya está guardado
            "timestamp_fin":            datetime.now(timezone.utc).isoformat(),
            "dia_inicio_simulado":      self._dia_inicio,
            "dia_fin_simulado":         dia_actual,
            "dias_procesados":          self._dias_procesados,
            "duracion_real_segundos":   elapsed,
            "razon_fin":                razon,
            "muertes_sesion":           self._muertes,
            "nacimientos_sesion":       self._nacimientos,
            "version_motor":            _VERSION,
        })

    # ── Acceso ────────────────────────────────────────────────────────────────

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def dias_procesados(self) -> int:
        return self._dias_procesados

    @property
    def is_active(self) -> bool:
        return self._active
