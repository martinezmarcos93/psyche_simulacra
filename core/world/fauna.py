from __future__ import annotations

import random

from .hexagon import BIOME_DATA
from .terrain import TerrainGrid
from .climate import ClimateState
from core.interface import ActionResult


_FAUNA_REGEN_BASE = 0.02

_FAUNA_SEASON_MOD: dict[str, float] = {
    "primavera": 1.60,
    "verano":    1.20,
    "otoño":     0.80,
    "invierno":  0.30,
}

_FAUNA_WEATHER_MOD: dict[str | None, float] = {
    None:       1.00,
    "tormenta": 0.40,
    "helada":   0.50,
    "sequia":   0.70,
}

_NOISE_STD = 0.005


class FaunaSystem:
    """
    Gestiona densidad de fauna por hex.
    Actualiza solo sobre hexes explorados una vez por día.
    """

    def __init__(self, terrain: TerrainGrid, seed: int = 42) -> None:
        self.terrain = terrain
        random.seed(seed + 100)
        self._density: dict[tuple[int, int], dict[str, float]] = {}
        # Cache de datos de bioma por coord — evita doble lookup en el loop
        self._biome_cache: dict[tuple[int, int], dict] = {}
        self._initialize()

    def _initialize(self) -> None:
        for coord, hex_cell in self.terrain._cells.items():
            bdata = BIOME_DATA[hex_cell.biome]
            self._biome_cache[coord] = bdata
            self._density[coord] = dict(bdata["fauna_base"])

    # ── Actualización ────────────────────────────────────────────────────────

    def daily_update(
        self,
        estacion:        str,
        climate:         ClimateState,
        explored_coords: list[tuple[int, int]],
    ) -> None:
        """
        Regenera fauna solo en hexes explorados.
        Usa Python puro en lugar de numpy para operaciones escalares
        (numpy tiene overhead por llamada que penaliza bucles de pocas ops).
        """
        season_mod  = _FAUNA_SEASON_MOD.get(estacion, 1.0)
        weather_mod = _FAUNA_WEATHER_MOD.get(climate.evento_activo, 1.00)
        regen       = _FAUNA_REGEN_BASE * season_mod
        gauss       = random.gauss

        for coord in explored_coords:
            bdata = self._biome_cache.get(coord)
            if bdata is None:
                continue
            densities = self._density[coord]
            base      = bdata["fauna_base"]

            for fauna_type, current in densities.items():
                cap   = base[fauna_type] * weather_mod
                new_v = current + regen * (cap - current) + gauss(0, _NOISE_STD)
                # min/max puro es más rápido que np.clip para escalares
                densities[fauna_type] = max(0.0, min(base[fauna_type], new_v))

    # ── Caza ─────────────────────────────────────────────────────────────────

    def hunt(
        self,
        coord:      tuple[int, int],
        fauna_type: str,
        amount:     float,
        agent_id:   str,
    ) -> ActionResult:
        densities = self._density.get(coord, {})
        available = densities.get(fauna_type, 0.0)

        if available < 0.10:
            return ActionResult(
                agent_id       = agent_id,
                action_type    = "cazar",
                success        = False,
                failure_reason = f"fauna_insuficiente:{fauna_type}",
                world_effects  = {},
            )

        success_prob = min(0.90, available * 0.80)
        success = random.random() < success_prob

        if success:
            taken = min(amount, available * 0.30)
            densities[fauna_type] = available - taken
            return ActionResult(
                agent_id        = agent_id,
                action_type     = "cazar",
                success         = True,
                resource_gained = {"carne": taken * 0.8, "cuero": taken * 0.15},
                world_effects   = {f"fauna_{fauna_type}_delta": -taken},
            )
        else:
            densities[fauna_type] = max(0.0, available - 0.02)
            return ActionResult(
                agent_id       = agent_id,
                action_type    = "cazar",
                success        = False,
                failure_reason = "caza_fallida",
                world_effects  = {f"fauna_{fauna_type}_delta": -0.02},
            )

    # ── Consultas ────────────────────────────────────────────────────────────

    def get_hex_summary(self, coord: tuple[int, int]) -> dict[str, float]:
        return {
            ft: d
            for ft, d in self._density.get(coord, {}).items()
            if d > 0.05
        }

    def get_density_map(
        self,
        explored_coords: list[tuple[int, int]],
    ) -> dict[tuple[int, int], dict[str, float]]:
        result = {}
        for coord in explored_coords:
            summary = self.get_hex_summary(coord)
            if summary:
                result[coord] = summary
        return result

    # ── Checkpoint ───────────────────────────────────────────────────────────

    def get_density_snapshot(
        self,
        explored_coords: list[tuple[int, int]],
    ) -> dict[str, dict[str, float]]:
        """Serializa densidades de fauna exploradas como {"q,r": {...}}."""
        return {
            f"{q},{r}": dict(self._density[(q, r)])
            for (q, r) in explored_coords
            if (q, r) in self._density
        }

    def restore_density(self, data: dict[str, dict[str, float]]) -> None:
        """Restaura desde el formato {"q,r": {...}}."""
        for key, densities in data.items():
            q, r = (int(x) for x in key.split(","))
            if (q, r) in self._density:
                self._density[(q, r)].update(densities)
