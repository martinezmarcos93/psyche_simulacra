from __future__ import annotations

import numpy as np

from .hexagon import Hexagon, BIOME_DATA


class TerrainGrid:
    """
    Grilla hexagonal del mundo en coordenadas axiales (q, r).
    Tamaño: 80×60 = 4800 celdas. 1 hex ≈ 1 km² ≈ 1 día de viaje.
    """

    WIDTH:  int = 80
    HEIGHT: int = 60

    # Distribución de biomas — pesos de frecuencia (deben sumar 1.0)
    _BIOMES = [
        "bosque_templado", "pradera_humeda", "rio_lago",     "montana_alta",
        "sabana_abierta",  "pantano_costero", "cueva",       "valle_fertil",
        "costa_abierta",   "desierto_borde",  "colinas_suaves", "lago_interior",
    ]
    _WEIGHTS = [
        0.18, 0.15, 0.08, 0.06,
        0.10, 0.04, 0.03, 0.08,
        0.05, 0.04, 0.10, 0.09,
    ]

    def __init__(self, seed: int = 42) -> None:
        self.rng    = np.random.default_rng(seed)
        self._cells: dict[tuple[int, int], Hexagon] = {}
        # Cache de coords exploradas — evita iterar 4800 celdas por tick
        self._explored_set: set[tuple[int, int]] = set()
        self._explored_list: list[tuple[int, int]] = []   # versión lista (para snapshot)
        self._carrying_capacity_cache: int = 0
        self._generate()

    def _generate(self) -> None:
        biomes  = self._BIOMES
        weights = self._WEIGHTS

        # Asignar bioma a cada celda
        flat_biomes = self.rng.choice(
            biomes,
            size=self.WIDTH * self.HEIGHT,
            p=weights,
        )
        idx = 0
        for r in range(self.HEIGHT):
            for q in range(self.WIDTH):
                self._cells[(q, r)] = Hexagon(q=q, r=r, biome=flat_biomes[idx])
                idx += 1

        # Asegurar que el área de inicio (centro) es habitable
        cx, cy = self.center
        for dq in range(-4, 5):
            for dr in range(-4, 5):
                if self.hex_distance(0, 0, dq, dr) <= 4:
                    coord = (cx + dq, cy + dr)
                    if coord in self._cells:
                        # Núcleo central: valle fértil; periferia: pradera
                        dist = self.hex_distance(0, 0, dq, dr)
                        biome = "valle_fertil" if dist <= 1 else "pradera_humeda"
                        self._cells[coord].biome = biome

        # Revelar el área de inicio (radio 2 alrededor del centro)
        self.reveal(cx, cy, radius=2)

    # ── Acceso ───────────────────────────────────────────────────────────────

    def get(self, q: int, r: int) -> Hexagon | None:
        return self._cells.get((q, r))

    def __contains__(self, coord: tuple[int, int]) -> bool:
        return coord in self._cells

    # ── Geometría hexagonal ──────────────────────────────────────────────────

    @staticmethod
    def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
        return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2

    def neighbors(self, q: int, r: int) -> list[Hexagon]:
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        result = []
        for dq, dr in dirs:
            cell = self._cells.get((q + dq, r + dr))
            if cell is not None:
                result.append(cell)
        return result

    def in_radius(self, q: int, r: int, radius: int) -> list[Hexagon]:
        result = []
        for dq in range(-radius, radius + 1):
            r_min = max(-radius, -dq - radius)
            r_max = min(radius, -dq + radius)
            for dr in range(r_min, r_max + 1):
                cell = self._cells.get((q + dq, r + dr))
                if cell is not None:
                    result.append(cell)
        return result

    # ── Exploración ──────────────────────────────────────────────────────────

    def reveal(self, q: int, r: int, radius: int = 1) -> list[tuple[int, int]]:
        """Marca celdas como exploradas. Devuelve coords de las nuevas."""
        newly_revealed = []
        for cell in self.in_radius(q, r, radius):
            if not cell.explored:
                cell.explored = True
                coord = cell.coords
                newly_revealed.append(coord)
                self._explored_set.add(coord)
                self._explored_list.append(coord)
                self._carrying_capacity_cache += cell.carrying_capacity
        return newly_revealed

    def add_structure(self, q: int, r: int, structure: str) -> bool:
        cell = self._cells.get((q, r))
        if cell is None:
            return False
        cell.structures.append(structure)
        return True

    # ── Consultas ────────────────────────────────────────────────────────────

    def explored_hexes(self) -> list[Hexagon]:
        return [self._cells[c] for c in self._explored_set]

    def explored_coords(self) -> list[tuple[int, int]]:
        return self._explored_list

    @property
    def center(self) -> tuple[int, int]:
        return (self.WIDTH // 2, self.HEIGHT // 2)

    @property
    def total_cells(self) -> int:
        return len(self._cells)

    def total_carrying_capacity(self) -> int:
        return self._carrying_capacity_cache
