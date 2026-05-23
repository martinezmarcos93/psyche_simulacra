"""
core/simulation_registry.py — Registro de simulaciones conectadas al servidor.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class SimulationEntry:
    sim_id:       str
    seed:         int
    version:      str
    connected_at: float = field(default_factory=time.monotonic)
    websocket:    object = None   # websockets.ServerConnection


class SimulationRegistry:
    """Mantiene el estado de todas las simulaciones actualmente conectadas."""

    def __init__(self) -> None:
        self._sims: dict[str, SimulationEntry] = {}

    def register(self, sim_id: str, seed: int, version: str, ws: object) -> SimulationEntry:
        entry = SimulationEntry(sim_id=sim_id, seed=seed, version=version, websocket=ws)
        self._sims[sim_id] = entry
        return entry

    def unregister(self, sim_id: str) -> None:
        self._sims.pop(sim_id, None)

    def get(self, sim_id: str) -> SimulationEntry | None:
        return self._sims.get(sim_id)

    def all_websockets(self) -> list:
        return [e.websocket for e in self._sims.values() if e.websocket is not None]

    def count(self) -> int:
        return len(self._sims)

    def sim_ids(self) -> list[str]:
        return list(self._sims.keys())

    def is_connected(self, sim_id: str) -> bool:
        return sim_id in self._sims
