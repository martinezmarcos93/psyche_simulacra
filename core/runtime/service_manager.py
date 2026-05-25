"""
ServiceManager — ciclo de vida de servicios externos (Ollama, Liminal).
Fase 4: implementación completa con health checks, backoff exponencial
y heartbeat configurable.
"""
from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Literal

from .event_bus import EventBus
from .event_types import ServiceHealthEvent

ServiceState = Literal["stopped", "starting", "running", "error"]

_MAX_RETRIES    = 5
_BACKOFF_BASE   = 1.5   # segundos; se multiplica por 2^n en cada reintento


@dataclass
class ServiceHandle:
    name:         str
    cmd:          list[str]           = field(default_factory=list)
    process:      subprocess.Popen | None = None
    state:        ServiceState        = "stopped"
    retry_count:  int                 = 0
    popen_kwargs: dict                = field(default_factory=dict)


class ServiceManager:
    """
    Gestiona subprocesos externos con health check, backoff exponencial y
    heartbeat configurable. Los cambios de estado se publican como
    ServiceHealthEvent en el EventBus.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._bus       = event_bus
        self._services: dict[str, ServiceHandle]           = {}
        self._heartbeats: dict[str, threading.Thread]      = {}
        self._stop_flags: dict[str, threading.Event]       = {}
        self._lock      = threading.Lock()

    # ── Control ──────────────────────────────────────────────────────────────

    def launch(
        self,
        name:        str,
        cmd:         list[str],
        max_retries: int = _MAX_RETRIES,
        **popen_kwargs,
    ) -> ServiceHandle:
        with self._lock:
            existing = self._services.get(name)
            if existing and existing.state == "running":
                return existing
            handle = ServiceHandle(name=name, cmd=cmd, state="starting",
                                   popen_kwargs=popen_kwargs)
            self._services[name] = handle

        delay = _BACKOFF_BASE
        for attempt in range(max_retries):
            try:
                proc = subprocess.Popen(cmd, **popen_kwargs)
                handle.process     = proc
                handle.state       = "running"
                handle.retry_count = attempt
                self._emit_health(name, "running",
                                  f"started (attempt {attempt + 1})")
                return handle
            except Exception as exc:
                handle.state = "error"
                self._emit_health(name, "error",
                                  f"attempt {attempt + 1}/{max_retries}: {exc}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2.0

        handle.state = "error"
        return handle

    def stop(self, name: str) -> None:
        flag = self._stop_flags.get(name)
        if flag:
            flag.set()

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
        # esperar que los threads de heartbeat terminen
        for t in list(self._heartbeats.values()):
            t.join(timeout=3)

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    def start_heartbeat(
        self,
        name:         str,
        interval_sec: float = 30.0,
        on_crash:     Callable[[str], None] | None = None,
    ) -> None:
        """
        Monitorea el proceso cada `interval_sec` segundos. Si cae, intenta
        relanzarlo automáticamente y llama `on_crash(name)` si está definido.
        """
        if name in self._heartbeats and self._heartbeats[name].is_alive():
            return

        stop_flag = threading.Event()
        self._stop_flags[name] = stop_flag

        def _beat() -> None:
            while not stop_flag.wait(interval_sec):
                state = self.get_state(name)
                if state != "running":
                    self._emit_health(name, "error", "heartbeat: process down, relaunching")
                    with self._lock:
                        handle = self._services.get(name)
                    if handle and handle.cmd:
                        self.launch(name, handle.cmd, **handle.popen_kwargs)
                    if on_crash:
                        try:
                            on_crash(name)
                        except Exception:
                            pass

        t = threading.Thread(target=_beat, name=f"heartbeat-{name}", daemon=True)
        self._heartbeats[name] = t
        t.start()

    def stop_heartbeat(self, name: str) -> None:
        flag = self._stop_flags.get(name)
        if flag:
            flag.set()

    # ── Internos ─────────────────────────────────────────────────────────────

    def _emit_health(self, service: str, state: str, detail: str) -> None:
        self._bus.emit(ServiceHealthEvent(service=service, state=state, detail=detail))
