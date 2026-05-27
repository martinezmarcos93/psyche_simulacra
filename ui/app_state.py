"""
Estado global de la aplicación NiceGUI — compartido entre páginas y conexiones.
Usa un lock para acceso thread-safe desde el hilo de simulación.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.simulation import SimulationRunner
    from core.runtime.psyche_runtime import PsycheRuntime


class AppState:
    def __init__(self) -> None:
        self._lock           = threading.Lock()
        self.runner:         "SimulationRunner | None" = None
        self.runtime:        "PsycheRuntime | None"    = None
        self.sim_thread:     threading.Thread | None   = None
        self.use_liminal:    bool                      = False
        self.liminal_port:   int                       = 8765
        self._liminal_proc   = None   # subprocess del servidor liminal
        self._pause_event:   threading.Event           = threading.Event()

    @property
    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    # ── Acceso thread-safe ────────────────────────────────────────────────────

    def set_runner(self, runner, runtime) -> None:
        with self._lock:
            self.runner  = runner
            self.runtime = runtime

    def get_runner(self):
        with self._lock:
            return self.runner

    def get_runtime(self):
        with self._lock:
            return self.runtime

    # ── Snapshot directo del mundo (sin serialización) ────────────────────────

    def get_snapshot(self):
        """Retorna el WorldSnapshot vivo, o None. NO serializa."""
        with self._lock:
            r = self.runner
        if r is None:
            return None
        return r.world.current_snapshot

    # ── Estado legible ────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        t = self.sim_thread
        return t is not None and t.is_alive()

    @property
    def dia_simulado(self) -> int:
        with self._lock:
            r = self.runner
        if r is None:
            return 0
        try:
            return r.current_dia
        except Exception:
            return 0

    @property
    def agentes_vivos(self) -> int:
        with self._lock:
            r = self.runner
        if r is None:
            return 0
        try:
            return r.alive_count
        except Exception:
            return 0


# Singleton global — importado por todas las páginas
state = AppState()
