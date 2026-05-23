"""
core/liminal_clock.py — Reloj independiente de la Zona Liminal.

No sincronizado con ninguna simulación. Avanza a su propio ritmo.
El servidor lo incrementa en su loop principal.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class LiminalTimePoint:
    tick:           int
    real_elapsed:   float   # segundos desde que arrancó el servidor


class LiminalClock:
    """Contador de tiempo propio de la Zona Liminal."""

    def __init__(self) -> None:
        self._tick:        int   = 0
        self._start_real:  float = time.monotonic()

    def advance(self) -> LiminalTimePoint:
        self._tick += 1
        return LiminalTimePoint(
            tick=self._tick,
            real_elapsed=time.monotonic() - self._start_real,
        )

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def elapsed_real(self) -> float:
        return time.monotonic() - self._start_real

    def to_dict(self) -> dict:
        return {
            "tick":         self._tick,
            "elapsed_real": round(self.elapsed_real, 2),
        }
