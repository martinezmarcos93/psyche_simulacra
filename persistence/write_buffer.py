from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .database import DatabaseManager


class WriteBuffer:
    """
    Acumula filas y las envía a la base de datos en lote.
    Las muertes se persisten de forma inmediata (no se pueden reconstruir).
    El resto se acumula hasta flush() o hasta alcanzar max_size.
    """

    def __init__(self, db: DatabaseManager, max_size: int = 500) -> None:
        self._db       = db
        self._max_size = max_size
        self._climate:  list[dict] = []
        self._agents:   list[tuple[int, list[dict]]] = []  # (dia, agents_data)
        self._total_buffered = 0

    # ── Escritura de muertes (inmediata) ─────────────────────────────────────

    def record_deaths(self, deaths: list[dict]) -> None:
        """Las muertes nunca se bufferizan — van directo a la BD."""
        if deaths:
            self._db.insert_deaths_batch(deaths)

    # ── Acumulación buffered ──────────────────────────────────────────────────

    def add_climate(self, row: dict) -> None:
        self._climate.append(row)
        self._total_buffered += 1
        if self._total_buffered >= self._max_size:
            self.flush()

    def add_agent_snapshots(self, dia: int, agents_data: list[dict]) -> None:
        self._agents.append((dia, agents_data))
        self._total_buffered += len(agents_data)
        if self._total_buffered >= self._max_size:
            self.flush()

    def add_scenario(self, dia: int, snapshot: object) -> None:
        self._db.insert_scenario(dia, snapshot)

    # ── Flush ─────────────────────────────────────────────────────────────────

    def flush(self) -> int:
        """Escribe todos los datos acumulados. Devuelve el número de filas escritas."""
        written = 0

        if self._climate:
            self._db.insert_climate_batch(self._climate)
            written += len(self._climate)
            self._climate.clear()

        for dia, agents_data in self._agents:
            self._db.insert_agent_snapshots(dia, agents_data)
            written += len(agents_data)
        self._agents.clear()

        self._total_buffered = 0
        return written

    def __len__(self) -> int:
        return self._total_buffered
