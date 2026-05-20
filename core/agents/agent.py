from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.interface import ActionType, WorldAction, WorldSnapshot
from core.time import TimePoint
from .needs import Needs, CRITICAL_THRESHOLD, OVERRIDE_THRESHOLD
from .schedule import ScheduleSystem

if TYPE_CHECKING:
    pass

# Days at critical threshold before death
_DIAS_HAMBRE_MUERTE = 3
_DIAS_SED_MUERTE    = 2

# How much a successful gather/hunt satisfies the need
_COMIDA_POR_RECOLECTA = 0.35
_COMIDA_POR_CAZA      = 0.55
_AGUA_POR_BEBER       = 0.60


class Agent:
    """
    Agente con 4 capas:
      - Biológica  : activa (Needs + ScheduleSystem)
      - Psicológica: placeholder (Phase 6)
      - Social     : placeholder (Phase 7)
      - Simbólica  : placeholder (Phase 7)
    """

    def __init__(
        self,
        agent_id: str,
        nombre:   str,
        posicion: tuple[int, int],
        rol:      str = "generico",
        edad:     int = 25,
        sexo:     str = "M",
        seed:     int | None = None,
    ) -> None:
        self.id       = agent_id
        self.nombre   = nombre
        self.posicion = posicion
        self.rol      = rol
        self.edad     = edad
        self.sexo     = sexo
        self.is_alive = True

        # Biological layer
        self.needs    = Needs()
        self.schedule = ScheduleSystem(rol=rol)

        # Emotional state (simplified; full version in Phase 6)
        self.humor    = 0.5   # 0=very bad, 1=very good
        self.energia  = 0.8   # 0=drained, 1=full
        self.ansiedad = 0.2   # 0=calm, 1=panic

        # Death counters
        self._dias_hambre_critica = 0
        self._dias_sed_critica    = 0

        self._rng = random.Random(seed)

    # ── Tick update ──────────────────────────────────────────────────────────

    def update_biological(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
    ) -> None:
        """Called once per tick by AgentCore."""
        actividad = self.schedule.get_activity(tp.hora_del_dia)

        if actividad == "dormir":
            self.needs.update_sleeping()
        else:
            self.needs.update_waking()

        # Apply results of the action submitted last tick
        if self.id in snapshot.action_results:
            result = snapshot.action_results[self.id]
            if result.success and result.resource_gained:
                self._apply_resource_gain(result.resource_gained)

        # Emotional coupling to needs (simplified)
        self.ansiedad = min(1.0, self.needs.stress_level * 1.2)
        self.humor    = max(0.0, 1.0 - self.needs.stress_level)
        self.energia  = max(0.0, 1.0 - self.needs.fatiga)

    def check_death(self) -> str | None:
        """
        Call once per simulated day.
        Returns cause of death string or None if alive.
        """
        if self.needs.hambre >= CRITICAL_THRESHOLD:
            self._dias_hambre_critica += 1
        else:
            self._dias_hambre_critica = 0

        if self.needs.sed >= CRITICAL_THRESHOLD:
            self._dias_sed_critica += 1
        else:
            self._dias_sed_critica = 0

        if self._dias_sed_critica >= _DIAS_SED_MUERTE:
            self.is_alive = False
            return "deshidratacion"
        if self._dias_hambre_critica >= _DIAS_HAMBRE_MUERTE:
            self.is_alive = False
            return "inanicion"
        return None

    # ── Decision ─────────────────────────────────────────────────────────────

    def decide_action(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
    ) -> WorldAction | None:
        """
        Returns a single WorldAction or None.
        Survival needs override the normal schedule.
        """
        if not self.is_alive:
            return None

        actividad = self.schedule.get_activity(tp.hora_del_dia)

        # Critical survival overrides schedule
        if self.needs.survival_override_active():
            critical = self.needs.most_critical_need()
            if critical == "sed":
                return self._find_water_action(tp, snapshot)
            if critical == "hambre":
                return self._find_food_action(tp, snapshot)
            if critical == "fatiga":
                return None  # rest in place

        # Normal schedule
        if actividad == "dormir" or actividad == "descansar":
            return None
        if actividad == "buscar_alimento":
            return self._find_food_action(tp, snapshot)
        if actividad == "buscar_agua":
            return self._find_water_action(tp, snapshot)
        if actividad == "cazar":
            return self._hunt_action(tp, snapshot)
        if actividad == "explorar":
            return self._explore_action(tp, snapshot)
        # interactuar — no WorldAction yet (Phase 7)
        return None

    # ── Action builders ──────────────────────────────────────────────────────

    def _find_food_action(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
    ) -> WorldAction | None:
        coord = self.posicion
        food  = self._get_nearby_food(coord, snapshot)
        if food is None:
            return self._explore_action(tp, snapshot)
        return WorldAction(
            agent_id = self.id,
            tick     = tp.tick,
            type     = ActionType.RECOLECTAR,
            coord    = coord,
            params   = {"resource": food, "amount": 0.15},
            priority = 0.7,
        )

    def _find_water_action(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
    ) -> WorldAction | None:
        coord = self.posicion
        resources = snapshot.recursos_por_hex.get(coord, {})
        water_sources = ["agua", "agua_lluvia", "agua_fresca", "agua_subterranea"]
        for water in water_sources:
            if resources.get(water, 0) > 0.1:
                return WorldAction(
                    agent_id = self.id,
                    tick     = tp.tick,
                    type     = ActionType.RECOLECTAR,
                    coord    = coord,
                    params   = {"resource": water, "amount": 0.20},
                    priority = 0.9,
                )
        return self._explore_action(tp, snapshot)

    def _hunt_action(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
    ) -> WorldAction | None:
        coord   = self.posicion
        fauna   = snapshot.fauna_visible.get(coord, {})
        target  = "grande" if fauna.get("grande", 0) > 0.2 else "pequena"
        if fauna.get(target, 0) <= 0.05:
            return self._find_food_action(tp, snapshot)
        return WorldAction(
            agent_id = self.id,
            tick     = tp.tick,
            type     = ActionType.CAZAR,
            coord    = coord,
            params   = {"fauna_type": target, "amount": 0.10},
            priority = 0.6,
        )

    def _explore_action(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
    ) -> WorldAction:
        # Simplified movement: agent physically moves to a neighbor this tick.
        # Full pathfinding comes in a later phase.
        q, r = self.posicion
        directions = [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
        dq, dr = self._rng.choice(directions)
        target = (q + dq, r + dr)
        self.posicion = target  # commit move immediately
        return WorldAction(
            agent_id = self.id,
            tick     = tp.tick,
            type     = ActionType.EXPLORAR,
            coord    = target,
            params   = {},
            priority = 0.3,
        )

    def _get_nearby_food(
        self,
        coord:    tuple[int, int],
        snapshot: WorldSnapshot,
    ) -> str | None:
        resources = snapshot.recursos_por_hex.get(coord, {})
        food_types = ["frutos", "raices", "plantas", "semillas", "peces"]
        for ft in food_types:
            if resources.get(ft, 0) > 0.1:
                return ft
        return None

    # ── Resource application ─────────────────────────────────────────────────

    def _apply_resource_gain(self, resources: dict) -> None:
        food_types  = {"frutos", "raices", "plantas", "semillas", "carne", "peces"}
        water_types = {"agua", "agua_lluvia", "agua_fresca", "agua_subterranea", "agua_salobre"}
        for rtype, qty in resources.items():
            if rtype in food_types:
                self.needs.eat(qty * _COMIDA_POR_RECOLECTA)
            elif rtype in water_types:
                self.needs.drink(qty * _AGUA_POR_BEBER)

    # ── Serialization ────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        return {
            "id":       self.id,
            "nombre":   self.nombre,
            "posicion": list(self.posicion),
            "rol":      self.rol,
            "edad":     self.edad,
            "sexo":     self.sexo,
            "is_alive": self.is_alive,
            "needs":    self.needs.to_dict(),
            "humor":    self.humor,
            "energia":  self.energia,
            "ansiedad": self.ansiedad,
            "dias_hambre_critica": self._dias_hambre_critica,
            "dias_sed_critica":    self._dias_sed_critica,
        }

    def to_dict(self) -> dict:
        return {
            **self.snapshot(),
            "schedule": self.schedule.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Agent:
        a = cls(
            agent_id = data["id"],
            nombre   = data["nombre"],
            posicion = tuple(data["posicion"]),
            rol      = data.get("rol", "generico"),
            edad     = data.get("edad", 25),
            sexo     = data.get("sexo", "M"),
        )
        a.needs    = Needs.from_dict(data.get("needs", {}))
        a.is_alive = data.get("is_alive", True)
        a.humor    = data.get("humor", 0.5)
        a.energia  = data.get("energia", 0.8)
        a.ansiedad = data.get("ansiedad", 0.2)
        a._dias_hambre_critica = data.get("dias_hambre_critica", 0)
        a._dias_sed_critica    = data.get("dias_sed_critica", 0)
        return a
