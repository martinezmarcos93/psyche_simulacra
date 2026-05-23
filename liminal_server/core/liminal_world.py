"""
core/liminal_world.py — Mapa hexagonal de la Zona Liminal.

30×20 = 600 hexágonos. Sin recursos, sin clima, sin fauna.
Solo un espacio de tránsito con biomas etéreos que dan identidad visual.
Coordenadas axiales (q, r), misma convención que PSYCHE SIMULACRA.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# Biomas liminales — solo tienen valor visual/conceptual
LIMINAL_BIOMES   = ["vacio", "nebulosa", "cristalino", "sombra", "aurora"]
LIMINAL_WEIGHTS  = [0.30,    0.25,        0.20,          0.15,     0.10]

# Colores Pygame por sub-bioma (importados por el visualizador)
SUB_BIOME_COLORS_DEF: dict[str, tuple[int, int, int]] = {
    "vacio":      ( 15,  12,  30),   # Vacío — violeta profundo
    "nebulosa":   ( 55,  18,  85),   # Nebulosa — púrpura
    "cristalino": ( 18,  55,  88),   # Cristalino — azul profundo
    "sombra":     (  8,   8,  18),   # Sombra — negro casi puro
    "aurora":     ( 18,  75,  65),   # Aurora — verde-teal
}


@dataclass
class LiminalHex:
    q:         int
    r:         int
    sub_biome: str = "vacio"

    @property
    def coords(self) -> tuple[int, int]:
        return (self.q, self.r)


class LiminalWorld:
    """
    Mapa hexagonal etéreo de la Zona Liminal.
    Compartido por todos los nodos — generado con WORLD_SEED fijo.
    """

    WIDTH:  int = 30
    HEIGHT: int = 20

    def __init__(self, seed: int = 0) -> None:
        self.seed  = seed
        self._rng  = np.random.default_rng(seed)
        self._cells: dict[tuple[int, int], LiminalHex] = {}
        self._generate()

    # ── Generación ───────────────────────────────────────────────────────────

    def _generate(self) -> None:
        flat = self._rng.choice(
            LIMINAL_BIOMES,
            size=self.WIDTH * self.HEIGHT,
            p=LIMINAL_WEIGHTS,
        )
        idx = 0
        for r in range(self.HEIGHT):
            for q in range(self.WIDTH):
                self._cells[(q, r)] = LiminalHex(q=q, r=r, sub_biome=flat[idx])
                idx += 1

    # ── Acceso ───────────────────────────────────────────────────────────────

    def get(self, q: int, r: int) -> LiminalHex | None:
        return self._cells.get((q, r))

    def all_cells(self):
        return self._cells.values()

    def __contains__(self, coord: tuple[int, int]) -> bool:
        return coord in self._cells

    # ── Geometría ────────────────────────────────────────────────────────────

    @staticmethod
    def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
        return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2

    def neighbors(self, q: int, r: int) -> list[LiminalHex]:
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        return [
            self._cells[q + dq, r + dr]
            for dq, dr in dirs
            if (q + dq, r + dr) in self._cells
        ]

    @property
    def center(self) -> tuple[int, int]:
        return (self.WIDTH // 2, self.HEIGHT // 2)

    # ── Spawn ─────────────────────────────────────────────────────────────────

    def spawn_position(self, agent_id: str) -> tuple[int, int]:
        """
        Posición de spawn determinista para un agente.
        Todos los agentes aparecen cerca del centro (radio 3) para favorecer
        los encuentros entre agentes de distintas simulaciones.
        """
        import math
        h   = abs(hash(agent_id))
        cx, cy = self.center
        # Radio pequeño (1-3) → agentes muy cerca del centro, encuentros probables
        radius    = 1 + (h % 3)
        angle_deg = (h * 137) % 360    # distribuir ángulos uniformemente
        q = int(cx + radius * math.cos(math.radians(angle_deg)))
        r = int(cy + radius * math.sin(math.radians(angle_deg)) * 0.65)
        q = max(1, min(self.WIDTH - 2, q))
        r = max(1, min(self.HEIGHT - 2, r))
        return (q, r)
