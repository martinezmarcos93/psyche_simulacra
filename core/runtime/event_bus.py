"""
EventBus — pub/sub interno de PSYCHE SIMULACRA.

Prioridades heredadas del SimulationClock:
  ≤ 30  → síncrono, en el thread del clock (handlers ligeros)
  ≥ 50  → asíncrono via queue.Queue (handlers lentos: narrator, UI, etc.)

Thread safety: suscripción/desuscripción protegidas con Lock.
El dispatch en prioridades ≥ 50 usa Queue bounded; si se llena, el evento
se descarta para nunca bloquear el loop de simulación.
"""
from __future__ import annotations

import queue
import threading
from collections import defaultdict
from typing import Any, Callable

_ASYNC_QUEUE_SIZE = 500


class AsyncQueueHandler:
    """Wraps a slow handler behind a queue so it never blocks the clock."""

    def __init__(self, handler: Callable[[Any], None], maxsize: int = _ASYNC_QUEUE_SIZE) -> None:
        self._handler   = handler
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=maxsize)
        self._thread    = threading.Thread(target=self._run, daemon=True, name=f"bus-{id(self)}")
        self._thread.start()

    def enqueue(self, event: Any) -> None:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            pass  # silently drop — never block the sim clock

    def _run(self) -> None:
        while True:
            event = self._queue.get()
            if event is _STOP_SENTINEL:
                break
            try:
                self._handler(event)
            except Exception:
                pass

    def stop(self) -> None:
        self._queue.put(_STOP_SENTINEL)


_STOP_SENTINEL = object()


class EventBus:
    """
    Central pub/sub bus.

    subscribe(EventType, handler, priority=50)
    emit(event_instance)

    Handlers with priority < 50 are called synchronously in the emitting thread.
    Handlers with priority >= 50 receive events via an AsyncQueueHandler.
    """

    ASYNC_THRESHOLD = 50

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        # type → sorted list of (priority, callable_or_AsyncQueueHandler, original_handler)
        self._sync_handlers:  dict[type, list[tuple[int, Callable]]]              = defaultdict(list)
        self._async_handlers: dict[type, list[tuple[int, AsyncQueueHandler, Callable]]] = defaultdict(list)

    # ── Suscripción ──────────────────────────────────────────────────────────

    def subscribe(
        self,
        event_type: type,
        handler: Callable[[Any], None],
        priority: int = 50,
    ) -> None:
        with self._lock:
            if priority < self.ASYNC_THRESHOLD:
                self._sync_handlers[event_type].append((priority, handler))
                self._sync_handlers[event_type].sort(key=lambda x: x[0])
            else:
                aqh = AsyncQueueHandler(handler)
                self._async_handlers[event_type].append((priority, aqh, handler))
                self._async_handlers[event_type].sort(key=lambda x: x[0])

    def unsubscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        with self._lock:
            self._sync_handlers[event_type] = [
                (p, h) for p, h in self._sync_handlers[event_type] if h is not handler
            ]
            to_stop = [
                aqh for p, aqh, h in self._async_handlers[event_type] if h is handler
            ]
            self._async_handlers[event_type] = [
                (p, aqh, h) for p, aqh, h in self._async_handlers[event_type] if h is not handler
            ]
        for aqh in to_stop:
            aqh.stop()

    # ── Emisión ──────────────────────────────────────────────────────────────

    def emit(self, event: Any) -> None:
        event_type = type(event)
        with self._lock:
            sync  = list(self._sync_handlers[event_type])
            async_ = list(self._async_handlers[event_type])

        for _, handler in sync:
            handler(event)

        for _, aqh, _ in async_:
            aqh.enqueue(event)

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        with self._lock:
            all_aqh = [
                aqh
                for handlers in self._async_handlers.values()
                for _, aqh, _ in handlers
            ]
        for aqh in all_aqh:
            aqh.stop()
