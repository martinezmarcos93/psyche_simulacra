"""
SnapshotPipeline — broadcast pub/sub de snapshots del mundo.

Fase 3 de Evolution: múltiples observers simultáneos pueden suscribirse
para recibir el snapshot completo cada día simulado.

La UI, Streamlit, y cualquier observer futuro se suscriben aquí.
El runtime nunca llama a la UI directamente (Doctrina B).
"""
from __future__ import annotations

import threading
from typing import Callable

from .event_bus import EventBus
from .event_types import SnapshotEmittedEvent


class SnapshotPipeline:
    """
    Broadcast pub/sub de snapshots de mundo a observers simultáneos.

    Uso:
        pipeline.subscribe(mi_handler)      # handler(snapshot: dict) -> None
        pipeline.broadcast(snap_dict, tick) # empuja a todos los suscriptores
        pipeline.unsubscribe(mi_handler)
    """

    def __init__(self, bus: EventBus) -> None:
        self._bus  = bus
        self._subscribers: list[Callable[[dict], None]] = []
        self._lock = threading.Lock()

    def subscribe(self, handler: Callable[[dict], None]) -> None:
        with self._lock:
            if handler not in self._subscribers:
                self._subscribers.append(handler)

    def unsubscribe(self, handler: Callable[[dict], None]) -> None:
        with self._lock:
            self._subscribers = [h for h in self._subscribers if h is not handler]

    def broadcast(self, snapshot: dict, tick: int) -> None:
        """Envía snapshot a todos los suscriptores y emite SnapshotEmittedEvent en el bus."""
        with self._lock:
            handlers = list(self._subscribers)

        for handler in handlers:
            try:
                handler(snapshot)
            except Exception:
                pass

        self._bus.emit(SnapshotEmittedEvent(
            tick=tick,
            snapshot_size_bytes=len(str(snapshot)),
        ))

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)
