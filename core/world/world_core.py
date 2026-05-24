from __future__ import annotations

from .climate import ClimateState, ClimateSystem
from .terrain import TerrainGrid
from .resources import ResourceSystem
from .fauna import FaunaSystem
from .fire import FireSystem
from core.time import TimePoint
from core.interface import WorldAction, WorldSnapshot, ActionResult, ActionType

_WATER_TYPES = frozenset([
    "agua", "agua_lluvia", "agua_fresca",
    "agua_subterranea", "agua_salobre", "nieve",
])
_HEX_RING1 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


class WorldCore:
    """
    Núcleo 1 — El mundo físico.
    Existe antes que los agentes. No conoce la psicología.
    No modifica su estado directamente: recibe acciones de agentes y las aplica.
    Se registra en el SimulationClock con priority=10.
    """

    def __init__(self, seed: int = 42) -> None:
        self._seed     = seed
        self.terrain   = TerrainGrid(seed=seed)
        self.climate   = ClimateSystem(seed=seed)
        self.resources = ResourceSystem(self.terrain)
        self.fauna     = FaunaSystem(self.terrain, seed=seed)
        self.fire      = FireSystem(seed=seed)

        self._pending_actions:     list[WorldAction]       = []
        self._last_action_results: dict[str, ActionResult] = {}
        self._current_snapshot:    WorldSnapshot | None    = None
        # resource_pressure solo se recalcula una vez por día (costoso)
        self._resource_pressure:   float                   = 0.0

    # ── Handlers del SimulationClock ─────────────────────────────────────────

    def on_tick(self, tp: TimePoint) -> None:
        """Llamado por SimulationClock (priority=10) en cada tick."""
        climate_state = self.climate.update(tp)
        self.fire.update(climate_state)

        # Aplicar acciones pendientes de los agentes del tick anterior
        self._last_action_results = self._apply_pending_actions(climate_state)
        self._pending_actions.clear()

        # Producir snapshot para que AgentCore lo lea
        self._current_snapshot = self._produce_snapshot(tp, climate_state)

    def on_day(self, tp: TimePoint) -> None:
        """Llamado al inicio de cada nuevo día simulado."""
        explored = self.terrain.explored_coords()
        climate  = self._last_climate_state()
        self.resources.daily_regeneration(tp.estacion, explored)
        self.fauna.daily_update(tp.estacion, climate, explored)
        self._resource_pressure = self.resources.total_pressure(explored)

    def on_season_change(self, tp: TimePoint) -> None:
        """Llamado cuando la estación cambia."""
        # El ajuste estacional ya se maneja dentro de daily_regeneration/daily_update
        pass

    # ── Interfaz con AgentCore ───────────────────────────────────────────────

    def receive_actions(self, actions: list[WorldAction]) -> None:
        """AgentCore entrega las acciones; se aplican al final del tick."""
        self._pending_actions.extend(actions)

    @property
    def current_snapshot(self) -> WorldSnapshot | None:
        return self._current_snapshot

    @property
    def last_action_results(self) -> dict[str, ActionResult]:
        return self._last_action_results

    # ── Lógica interna ────────────────────────────────────────────────────────

    def _apply_pending_actions(
        self,
        climate: ClimateState,
    ) -> dict[str, ActionResult]:
        results: dict[str, ActionResult] = {}

        for action in sorted(self._pending_actions,
                             key=lambda a: -a.priority):
            result = self._apply_action(action, climate)
            if result is not None:
                results[action.agent_id] = result

        return results

    def _apply_action(
        self,
        action:  WorldAction,
        climate: ClimateState,
    ) -> ActionResult | None:
        if action.type == ActionType.RECOLECTAR:
            resource = action.params.get("resource", "")
            amount   = action.params.get("amount", 0.1)
            return self.resources.consume(action.coord, resource, amount, action.agent_id)

        elif action.type == ActionType.CAZAR:
            fauna_type = action.params.get("fauna_type", "pequena")
            amount     = action.params.get("amount", 0.1)
            return self.fauna.hunt(action.coord, fauna_type, amount, action.agent_id)

        elif action.type == ActionType.ENCENDER_FUEGO:
            return self.fire.ignite(action.coord, action.agent_id, climate)

        elif action.type == ActionType.MANTENER_FUEGO:
            return self.fire.maintain(action.agent_id)

        elif action.type == ActionType.EXPLORAR:
            newly = self.terrain.reveal(
                action.coord[0], action.coord[1], radius=1
            )
            return ActionResult(
                agent_id      = action.agent_id,
                action_type   = ActionType.EXPLORAR,
                success       = True,
                world_effects = {"nuevos_hexes": len(newly)},
                discoveries   = [{"tipo": "hex", "coord": c} for c in newly],
            )

        elif action.type == ActionType.CONSTRUIR_REFUGIO:
            ok = self.terrain.add_structure(
                action.coord[0], action.coord[1], "refugio"
            )
            return ActionResult(
                agent_id    = action.agent_id,
                action_type = ActionType.CONSTRUIR_REFUGIO,
                success     = ok,
            )

        else:
            return None

    def _produce_snapshot(
        self,
        tp:      TimePoint,
        climate: ClimateState,
    ) -> WorldSnapshot:
        explored = self.terrain.explored_coords()

        recursos_por_hex = {
            coord: self.resources.get_hex_summary(coord)
            for coord in explored
        }

        # Incluir hexes frontera (no explorados adyacentes a explorados) mostrando
        # solo recursos de agua, para que los agentes puedan navegar hacia el agua
        # incluso antes de explorar ese hex.
        explored_set = set(explored)
        seen_frontier: set[tuple[int, int]] = set()
        for (q, r) in explored:
            for dq, dr in _HEX_RING1:
                nc = (q + dq, r + dr)
                if nc not in explored_set and nc not in seen_frontier \
                        and 0 <= nc[0] < 80 and 0 <= nc[1] < 60:
                    seen_frontier.add(nc)
                    summary = self.resources.get_hex_summary(nc)
                    water_data = {k: v for k, v in summary.items() if k in _WATER_TYPES}
                    if water_data:
                        recursos_por_hex[nc] = water_data

        fauna_visible = self.fauna.get_density_map(explored)

        carrying_cap = self.terrain.total_carrying_capacity()
        pressure     = self._resource_pressure

        return WorldSnapshot(
            tick             = tp.tick,
            dia              = tp.dia_simulado,
            hora             = tp.hora_del_dia,
            estacion         = tp.estacion,
            temperatura      = climate.temperatura,
            precipitacion    = climate.precipitacion,
            luminosidad      = climate.luminosidad,
            viento           = climate.viento,
            evento_climatico = climate.evento_activo,
            mood_modifier    = climate.mood_modifier,
            productivity_mod = climate.productivity_mod,
            survival_risk    = climate.survival_risk,
            recursos_por_hex = recursos_por_hex,
            fauna_visible    = fauna_visible,
            fuego_activo     = self.fire.is_active,
            fuego_coord      = self.fire.location,
            fuego_intensidad = self.fire.intensity,
            fuego_calor_bonus = self.fire.heat_bonus,
            carrying_capacity = carrying_cap,
            resource_pressure = pressure,
            action_results    = self._last_action_results,
        )

    def _last_climate_state(self) -> ClimateState:
        """Devuelve el último estado climático conocido."""
        if self._current_snapshot is None:
            # Estado inicial antes del primer tick
            return ClimateState(
                temperatura=16.0, precipitacion=0.45, luminosidad=0.70,
                viento=0.30, humedad=0.55, estacion="primavera",
                evento_activo=None, mood_modifier=0.0,
                productivity_mod=0.0, survival_risk=0.0,
            )
        snap = self._current_snapshot
        return ClimateState(
            temperatura      = snap.temperatura,
            precipitacion    = snap.precipitacion,
            luminosidad      = snap.luminosidad,
            viento           = snap.viento,
            humedad          = 0.55,
            estacion         = snap.estacion,
            evento_activo    = snap.evento_climatico,
            mood_modifier    = snap.mood_modifier,
            productivity_mod = snap.productivity_mod,
            survival_risk    = snap.survival_risk,
        )

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "fire": self.fire.to_dict(),
            "explored_coords": list(self.terrain.explored_coords()),
        }

    def full_state_dict(self) -> dict:
        """Estado completo para checkpoint — incluye recursos y fauna de hexes explorados."""
        explored = self.terrain.explored_coords()
        return {
            "seed":             self._seed,
            "fire":             self.fire.to_dict(),
            "explored_coords":  [[q, r] for (q, r) in explored],
            "resource_amounts": self.resources.get_amounts_snapshot(explored),
            "fauna_density":    self.fauna.get_density_snapshot(explored),
        }

    def restore_from_state_dict(self, data: dict) -> None:
        """Restaura el mundo desde un dict de checkpoint."""
        explored_raw = data.get("explored_coords", [])
        for qr in explored_raw:
            q, r = qr[0], qr[1]
            self.terrain.reveal(q, r, radius=0)

        self.fire = self.fire.from_dict(data.get("fire", {}))
        self.resources.restore_amounts(data.get("resource_amounts", {}))
        self.fauna.restore_density(data.get("fauna_density", {}))
