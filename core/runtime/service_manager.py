"""
ServiceManager — ciclo de vida de servicios externos (Ollama, Liminal).
Fase 0: stubs. Fase 4: implementación completa con health checks y backoff.
"""
from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from typing import Callable, Literal

from .event_bus import EventBus
from .event_types import ServiceHealthEvent

ServiceState = Literal["stopped", "starting", "running", "error"]


@dataclass
class ServiceHandle:
    name:    str
    process: subprocess.Popen | None = None
    state:   ServiceState = "stopped"


class ServiceManager:
    """
    Gestiona subprocesos externos con health check básico.
    En Fase 4 añade: backoff exponencial, reintentos, heartbeat configurable.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._bus      = event_bus
        self._services: dict[str, ServiceHandle] = {}
        self._lock     = threading.Lock()

    # ── Control ──────────────────────────────────────────────────────────────

    def launch(self, name: str, cmd: list[str], **popen_kwargs) -> ServiceHandle:
        with self._lock:
            existing = self._services.get(name)
            if existing and existing.state == "running":
                return existing

            handle = ServiceHandle(name=name, state="starting")
            self._services[name] = handle

        try:
            proc = subprocess.Popen(cmd, **popen_kwargs)
            handle.process = proc
            handle.state   = "running"
            self._emit_health(name, "running", "started")
        except Exception as e:
            handle.state = "error"
            self._emit_health(name, "error", str(e))

        return handle

    def stop(self, name: str) -> None:
        with self._lock:
            handle = self._services.get(name)
        if handle and handle.process:
            try:
                handle.process.terminate()
                handle.process.wait(timeout=10)
            except Exception:
                try:
                    handle.process.kill()
                except Exception:
                    pass
            handle.state = "stopped"
            self._emit_health(name, "stopped", "terminated")

    def get_state(self, name: str) -> ServiceState:
        with self._lock:
            handle = self._services.get(name)
        if handle is None:
            return "stopped"
        if handle.process and handle.process.poll() is not None:
            handle.state = "stopped"
        return handle.state

    def shutdown_all(self) -> None:
        with self._lock:
            names = list(self._services.keys())
        for name in names:
            self.stop(name)

    # ── Internos ─────────────────────────────────────────────────────────────

    def _emit_health(self, service: str, state: str, detail: str) -> None:
        self._bus.emit(ServiceHealthEvent(service=service, state=state, detail=detail))
