from __future__ import annotations

from .hexagon import BIOME_DATA
from .terrain import TerrainGrid
from core.interface import ActionResult


_REGEN_MOD: dict[str, float] = {
    "primavera": 1.40,
    "verano":    1.00,
    "otoño":     0.60,
    "invierno":  0.20,
}

_SEASONAL_RESOURCES: dict[str, list[str]] = {
    "verano":    ["frutos"],
    "primavera": ["frutos", "flores"],
    "otoño":     ["frutos", "raices"],
    "invierno":  [],
}


class ResourceSystem:
    """
    Gestiona cantidades de recursos en cada hex del mundo.
    Cada recurso va de 0.0 (agotado) a su cap (nivel base del bioma).
    Regenera una vez por día solo sobre hexes explorados
    (los no explorados nunca se agotan, por lo que no necesitan regen).
    """

    def __init__(self, terrain: TerrainGrid) -> None:
        self.terrain = terrain
        self._amounts: dict[tuple[int, int], dict[str, float]] = {}
        # Cache de datos de bioma por coord — evita doble lookup en el loop de regen
        self._biome_cache: dict[tuple[int, int], dict] = {}
        self._initialize()

    def _initialize(self) -> None:
        for coord, hex_cell in self.terrain._cells.items():
            bdata = BIOME_DATA[hex_cell.biome]
            self._biome_cache[coord] = bdata
            self._amounts[coord] = dict(bdata["base_resources"])

    # ── Actualización ────────────────────────────────────────────────────────

    def daily_regeneration(
        self,
        estacion:       str,
        explored_coords: list[tuple[int, int]],
    ) -> None:
        """
        Regenera recursos solo en hexes explorados.
        Los hexes no explorados no se agotan nunca (no hay agentes allí),
        así que siempre están a nivel base — no necesitan regen.
        """
        season_mod  = _REGEN_MOD.get(estacion, 1.0)
        no_seasonal = _SEASONAL_RESOURCES.get(estacion, [])

        for coord in explored_coords:
            bdata  = self._biome_cache.get(coord)
            if bdata is None:
                continue
            amounts = self._amounts[coord]
            base    = bdata["base_resources"]
            regen   = bdata["regen_rate"] * season_mod

            for resource, current in amounts.items():
                cap = base[resource]
                if resource in ("frutos", "flores") and resource not in no_seasonal:
                    cap *= 0.30
                new_val = current + regen * (cap - current)
                amounts[resource] = new_val if new_val < cap else cap

    # ── Consumo ──────────────────────────────────────────────────────────────

    def consume(
        self,
        coord:    tuple[int, int],
        resource: str,
        amount:   float,
        agent_id: str,
    ) -> ActionResult:
        amounts   = self._amounts.get(coord, {})
        available = amounts.get(resource, 0.0)

        if available < 0.05:
            return ActionResult(
                agent_id       = agent_id,
                action_type    = "recolectar",
                success        = False,
                failure_reason = f"recurso_agotado:{resource}",
                world_effects  = {},
            )

        taken = amount if amount < available else available
        amounts[resource] = available - taken

        return ActionResult(
            agent_id        = agent_id,
            action_type     = "recolectar",
            success         = True,
            resource_gained = {resource: taken},
            world_effects   = {f"{resource}_delta": -taken},
        )

    # ── Consultas ────────────────────────────────────────────────────────────

    def get_hex_summary(self, coord: tuple[int, int]) -> dict[str, float]:
        return {
            res: qty
            for res, qty in self._amounts.get(coord, {}).items()
            if qty > 0.01
        }

    def total_pressure(self, explored_coords: list[tuple[int, int]]) -> float:
        """0.0 = abundancia · 1.0 = crisis (fracción de recursos < 30% del cap)."""
        total    = 0
        depleted = 0
        for coord in explored_coords:
            bdata = self._biome_cache.get(coord)
            if bdata is None:
                continue
            base = bdata["base_resources"]
            for resource, current in self._amounts.get(coord, {}).items():
                cap = base.get(resource, 1.0)
                total += 1
                if cap > 0 and current / cap < 0.30:
                    depleted += 1
        return depleted / total if total else 0.0

    # ── Checkpoint ───────────────────────────────────────────────────────────

    def get_amounts_snapshot(
        self,
        explored_coords: list[tuple[int, int]],
    ) -> dict[str, dict[str, float]]:
        """Serializa cantidades de recursos explorados como {"q,r": {...}}."""
        return {
            f"{q},{r}": dict(self._amounts[(q, r)])
            for (q, r) in explored_coords
            if (q, r) in self._amounts
        }

    def restore_amounts(self, data: dict[str, dict[str, float]]) -> None:
        """Restaura desde el formato {"q,r": {...}}."""
        for key, amounts in data.items():
            q, r = (int(x) for x in key.split(","))
            if (q, r) in self._amounts:
                self._amounts[(q, r)].update(amounts)
