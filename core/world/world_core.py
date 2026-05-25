from __future__ import annotations

from .climate import ClimateState, ClimateSystem
from .terrain import TerrainGrid
from .resources import ResourceSystem
from .fauna import FaunaSystem
from .fire import FireSystem
from .grave_hex import GraveSystem
from .substances import SubstanceSystem, SUBSTANCE_NAMES
from .catastrophe import CatastropheEngine
from .fauna_symbolic import SymbolicFaunaSystem
from .liminal_hex import LiminalHexSystem
from .psychic_geography import PsychicGeography
from .persistent_structures import PersistentStructureSystem
import random
from core.time import TimePoint
from core.interface import WorldAction, WorldSnapshot, ActionResult, ActionType

_WATER_TYPES = frozenset([
    "agua", "agua_lluvia", "agua_fresca",
    "agua_subterranea", "agua_salobre", "nieve",
])
_FOOD_TYPES = frozenset(["planta", "fruto", "semilla", "fungi"])
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
        self.fire        = FireSystem(seed=seed)
        self.graves      = GraveSystem()
        self.substances  = SubstanceSystem()
        self.catastrophe      = CatastropheEngine(seed=seed + 13)
        self.fauna_symbolic   = SymbolicFaunaSystem(seed=seed + 17)
        self.liminal_system   = LiminalHexSystem(seed=seed + 23)
        self.psychic_geography    = PsychicGeography()
        self.persistent_structures = PersistentStructureSystem()
        self._rng             = random.Random(seed + 7)
        # Inicializar hexes liminales con el terreno ya generado
        self.liminal_system.initialize(self.terrain)
        # Eventos del día actual (consumidos por AgentCore)
        self._fauna_events:   list[dict] = []

        self._pending_actions:     list[WorldAction]       = []
        self._last_action_results: dict[str, ActionResult] = {}
        self._current_snapshot:    WorldSnapshot | None    = None
        # resource_pressure solo se recalcula una vez por día (costoso)
        self._resource_pressure:   float                   = 0.0
        # R5-B2: coords ocupadas por agentes vivos (actualizado por AgentCore antes de on_day)
        self._occupied_coords:     set[tuple[int, int]]    = set()

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
        self.catastrophe.on_day(tp.dia_simulado, tp.estacion, self.terrain, self.graves)
        graves_active = self.graves.active_sites()
        self._fauna_events = self.fauna_symbolic.on_day(
            tp.dia_simulado, tp.estacion, self.terrain, graves_active
        )
        self.liminal_system.on_day(tp.dia_simulado, self.terrain)
        self.psychic_geography.on_day()
        # R5-B2: estructuras — occupied_coords se actualiza por AgentCore antes de on_day
        self.persistent_structures.on_day(
            dia             = tp.dia_simulado,
            occupied_coords = self._occupied_coords,
            psychic_geography = self.psychic_geography,
        )
        self.resources.daily_regeneration(tp.estacion, explored)
        self.fauna.daily_update(tp.estacion, climate, explored)
        self._resource_pressure = self.resources.total_pressure(explored)
        self.graves.daily_update()
        self.substances.daily_regen()

    def on_season_change(self, tp: TimePoint) -> None:
        """Llamado cuando la estación cambia."""
        # El ajuste estacional ya se maneja dentro de daily_regeneration/daily_update
        pass

    # ── Interfaz con AgentCore ───────────────────────────────────────────────

    def receive_actions(self, actions: list[WorldAction]) -> None:
        """AgentCore entrega las acciones; se aplican al final del tick."""
        self._pending_actions.extend(actions)

    def update_occupied_coords(self, coords: set[tuple[int, int]]) -> None:
        """R5-B2: AgentCore informa qué hexes tienen agentes vivos este día."""
        self._occupied_coords = coords

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
            if resource in SUBSTANCE_NAMES:
                taken = self.substances.consume(action.coord, resource, amount, action.agent_id)
                if taken > 0:
                    return ActionResult(
                        agent_id        = action.agent_id,
                        action_type     = "recolectar",
                        success         = True,
                        resource_gained = {resource: taken},
                        world_effects   = {f"{resource}_consumido": taken},
                    )
                return ActionResult(
                    agent_id       = action.agent_id,
                    action_type    = "recolectar",
                    success        = False,
                    failure_reason = "sustancia_agotada",
                    world_effects  = {},
                )
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
            # Descubrimiento accidental de sustancia al explorar el hex
            hex_cell  = self.terrain.get(action.coord[0], action.coord[1])
            substance = None
            if hex_cell is not None:
                substance = self.substances.maybe_reveal(action.coord, hex_cell.biome, self._rng)
            discoveries = [{"tipo": "hex", "coord": c} for c in newly]
            if substance:
                discoveries.append({"tipo": "sustancia", "nombre": substance, "coord": action.coord})
            return ActionResult(
                agent_id      = action.agent_id,
                action_type   = ActionType.EXPLORAR,
                success       = True,
                world_effects = {"nuevos_hexes": len(newly)},
                discoveries   = discoveries,
            )

        elif action.type == ActionType.CONSTRUIR_REFUGIO:
            ok = self.terrain.add_structure(
                action.coord[0], action.coord[1], "refugio"
            )
            if ok:
                self.persistent_structures.register_build(
                    coord = action.coord,
                    tipo  = "refugio",
                    tribu = action.params.get("tribu_id"),
                    dia   = action.tick // 24,
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

        # Añadir sustancias descubiertas a los recursos visibles
        for coord, sub_dict in self.substances.get_for_snapshot(explored).items():
            recursos_por_hex.setdefault(coord, {}).update(sub_dict)

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

        # Aplicar modificadores de catástrofe a recursos visibles (Hito 5)
        if self.catastrophe.active is not None:
            for coord in list(recursos_por_hex.keys()):
                hex_cell  = self.terrain.get(*coord)
                biome     = hex_cell.biome if hex_cell else ""
                water_mod = self.catastrophe.get_water_modifier(coord, biome)
                food_mod  = self.catastrophe.get_food_modifier(coord)
                if water_mod < 1.0 or food_mod < 1.0:
                    modified = dict(recursos_por_hex[coord])
                    for resource, qty in modified.items():
                        if resource in _WATER_TYPES:
                            modified[resource] = qty * water_mod
                        elif resource in _FOOD_TYPES:
                            modified[resource] = qty * food_mod
                    recursos_por_hex[coord] = modified

        fauna_visible = self.fauna.get_density_map(explored)

        carrying_cap = self.terrain.total_carrying_capacity()
        pressure     = self._resource_pressure

        return WorldSnapshot(
            tick              = tp.tick,
            dia               = tp.dia_simulado,
            hora              = tp.hora_del_dia,
            estacion          = tp.estacion,
            temperatura       = climate.temperatura,
            precipitacion     = climate.precipitacion,
            luminosidad       = climate.luminosidad,
            viento            = climate.viento,
            evento_climatico  = climate.evento_activo,
            mood_modifier     = climate.mood_modifier,
            productivity_mod  = climate.productivity_mod,
            survival_risk     = climate.survival_risk,
            recursos_por_hex  = recursos_por_hex,
            fauna_visible     = fauna_visible,
            fuego_activo      = self.fire.is_active,
            fuego_coord       = self.fire.location,
            fuego_intensidad  = self.fire.intensity,
            fuego_calor_bonus = self.fire.heat_bonus,
            carrying_capacity = carrying_cap,
            resource_pressure = pressure,
            graves_activos    = self.graves.active_sites(),
            action_results    = self._last_action_results,
            catastrofe_activa = self.catastrophe.get_snapshot_data(),
            fauna_simbolica   = self.fauna_symbolic.active_entities(),
            liminal_hexes     = self.liminal_system.active_hexes(),
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
            "graves":           self.graves.to_dict(),
            "substances":       self.substances.to_dict(),
            "catastrophe":      self.catastrophe.to_dict(),
            "fauna_symbolic":   self.fauna_symbolic.to_dict(),
            "liminal_system":      self.liminal_system.to_dict(),
            "psychic_geography":       self.psychic_geography.to_dict(),
            "persistent_structures":   self.persistent_structures.to_dict(),
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
        if "graves" in data:
            self.graves = GraveSystem.from_dict(data["graves"])
        if "substances" in data:
            self.substances = SubstanceSystem.from_dict(data["substances"])
        if "catastrophe" in data:
            self.catastrophe = CatastropheEngine.from_dict(
                data["catastrophe"], seed=self._seed + 13
            )
        if "fauna_symbolic" in data:
            self.fauna_symbolic = SymbolicFaunaSystem.from_dict(
                data["fauna_symbolic"], seed=self._seed + 17
            )
        if "liminal_system" in data:
            self.liminal_system = LiminalHexSystem.from_dict(
                data["liminal_system"], seed=self._seed + 23
            )
        if "psychic_geography" in data:
            self.psychic_geography = PsychicGeography.from_dict(
                data["psychic_geography"]
            )
        if "persistent_structures" in data:
            self.persistent_structures = PersistentStructureSystem.from_dict(
                data["persistent_structures"]
            )
