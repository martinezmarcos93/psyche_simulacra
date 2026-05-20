from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.interface import ActionType, WorldAction, WorldSnapshot
from core.time import TimePoint
from .needs import Needs, CRITICAL_THRESHOLD, OVERRIDE_THRESHOLD
from .schedule import ScheduleSystem
from .psyche.archetypes import ArchetypeVector
from .psyche.complexes import ComplexProfile
from .psyche.traits import TraitProfile
from .psyche.dreams import DreamEngine, Dream
from .quantum.superposition import BehavioralState
from .quantum.collapse import collapse_state

if TYPE_CHECKING:
    pass

_DIAS_HAMBRE_MUERTE   = 3
_DIAS_SED_MUERTE      = 2
_COMIDA_POR_RECOLECTA = 0.35
_COMIDA_POR_CAZA      = 0.55
_AGUA_POR_BEBER       = 0.60
_DREAM_HORA           = 22   # se sueña en esta hora del día simulado


class Agent:
    """
    Agente con 4 capas:
      - Biológica   : Needs + ScheduleSystem
      - Psicológica : ArchetypeVector + ComplexProfile + TraitProfile + DreamEngine
      - Cuántica    : BehavioralState + collapse_state
      - Social      : placeholder (Phase 7)
      - Simbólica   : placeholder (Phase 7)
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

        # Psychological layer
        self.archetypes = ArchetypeVector()
        self.complexes  = ComplexProfile()
        self.traits     = TraitProfile()
        self._dream_engine = DreamEngine()
        self.dreams: list[Dream] = []

        # Quantum layer
        self.behavioral_state = BehavioralState()
        # Estado base estable para el decay (refleja la personalidad duradera)
        self._base_state: BehavioralState | None = None

        # Emotional state (driven by layer integration)
        self.humor    = 0.5
        self.energia  = 0.8
        self.ansiedad = 0.2

        # Death counters
        self._dias_hambre_critica = 0
        self._dias_sed_critica    = 0

        self._rng = random.Random(seed)

        # Episodic Memory Log (Fase 8)
        self.episodic_log: list[str] = []

    # ── Inicialización desde YAML ─────────────────────────────────────────────

    def load_psyche_from_yaml(self, data: dict) -> None:
        """Carga la capa psicológica desde los datos del YAML de seeds."""
        if "arquetipos" in data:
            self.archetypes = ArchetypeVector.from_dict(data["arquetipos"])

        if "complejos" in data:
            raw = dict(data["complejos"])
            triggers = raw.pop("triggers", {})
            self.complexes = ComplexProfile.from_dict(raw)
            self.complexes.custom_triggers = triggers

        if "big_five" in data:
            self.traits = TraitProfile.from_dict(data["big_five"])
        elif "rasgos" in data:
            self.traits = TraitProfile.from_dict(data["rasgos"])

        if "estado_cuantico" in data:
            vc = data["estado_cuantico"].get("vector_conductual", {})
            self.behavioral_state = BehavioralState.from_dict(vc)
        else:
            # Derivar el estado inicial del arquetipo dominante
            self.behavioral_state = BehavioralState.from_archetype_dominant(
                self.archetypes.dominant()
            )

        # Guardar el estado base para el decay natural
        self._base_state = BehavioralState(
            cooperacion  = self.behavioral_state.cooperacion,
            competencia  = self.behavioral_state.competencia,
            aislamiento  = self.behavioral_state.aislamiento,
            manipulacion = self.behavioral_state.manipulacion,
        )

    # ── Tick update ──────────────────────────────────────────────────────────

    def update_biological(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
    ) -> None:
        """Llamado una vez por tick por AgentCore."""
        actividad = self.schedule.get_activity(tp.hora_del_dia)

        if actividad == "dormir":
            self.needs.update_sleeping()
        else:
            self.needs.update_waking()

        # Aplicar resultado de la acción del tick anterior
        if self.id in snapshot.action_results:
            result = snapshot.action_results[self.id]
            if result.success and result.resource_gained:
                self._apply_resource_gain(result.resource_gained)

        # Complejos decaen por tick
        self.complexes.decay_tick()

        # Decay del estado cuántico hacia el estado base
        if self._base_state is not None:
            self.behavioral_state.decay_toward_base(self._base_state, rate=0.01)

        # Sueño: procesamiento onírico una vez por día en hora definida
        if tp.hora_del_dia == _DREAM_HORA and actividad == "dormir":
            self._process_dream(tp.dia_simulado)

        # Estado emocional integrado
        self._update_emotional_state()

    def _update_emotional_state(self) -> None:
        """Integra biología, psicología y cuántica en el estado emocional."""
        stress = self.needs.stress_level
        mood_base = self.traits.mood_modifier()
        complejo_ansiedad = 0.10 if self.complexes.activos else 0.0

        self.ansiedad = min(1.0, stress * (1.0 + self.traits.stress_sensitivity()) + complejo_ansiedad)
        self.humor    = max(0.0, 1.0 - stress + mood_base * 0.3)
        self.energia  = max(0.0, 1.0 - self.needs.fatiga)

    def _process_dream(self, dia: int) -> None:
        """Genera un sueño y aplica sus deltas arquetípicos."""
        dream = self._dream_engine.generate_dream(
            dia             = dia,
            dominante       = self.archetypes.dominant(),
            tension         = self.archetypes.tension(),
            complejo_activo = self.complexes.most_active(),
            rng             = self._rng,
        )
        self.dreams.append(dream)
        self.episodic_log.append(
            f"Día {dia}: Soñó con '{dream.simbolo}' ({dream.arquetipo}). Insight: {dream.insight}"
        )
        # Guardar solo los últimos 7 sueños
        if len(self.dreams) > 7:
            self.dreams = self.dreams[-7:]

        # Aplicar deltas al vector arquetípico
        self.archetypes.update_from_event.__func__  # touch to avoid lint warnings
        for arch_key, delta in dream.delta_arquetipo.items():
            attr = "self_" if arch_key == "self" else arch_key
            if hasattr(self.archetypes, attr):
                current = getattr(self.archetypes, attr)
                setattr(self.archetypes, attr, max(0.0, min(1.0, current + delta)))

    def check_death(self) -> str | None:
        """Llamado una vez por día. Devuelve causa de muerte o None."""
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

    def on_day(self, tp: TimePoint) -> None:
        """Llamado al inicio de cada nuevo día."""
        self.complexes.decay_day()
        # Activar complejos por contexto de supervivencia
        events: list[str] = []
        if self.needs.hambre > OVERRIDE_THRESHOLD:
            events.append("fracaso")
        if self.needs.sed > OVERRIDE_THRESHOLD:
            events.append("fracaso")
        if not self.is_alive:
            events.append("muerte")
        if events:
            self.complexes.check_activation(events)

    # ── Decision ─────────────────────────────────────────────────────────────

    def decide_action(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
        collective_field: CollectiveField | None = None,
        hay_aliados: bool = False,
    ) -> WorldAction | None:
        """Devuelve una WorldAction o None. Integra psicología en la decisión."""
        if not self.is_alive:
            return None

        actividad = self.schedule.get_activity(tp.hora_del_dia)

        # Necesidades críticas siempre sobreescriben
        if self.needs.survival_override_active():
            critical = self.needs.most_critical_need()
            if critical == "sed":
                return self._find_water_action(tp, snapshot)
            if critical == "hambre":
                return self._find_food_action(tp, snapshot)
            if critical == "fatiga":
                return None

        # Colapso cuántico para decisiones no-críticas
        if actividad == "interactuar":
            return self._decide_via_collapse(tp, snapshot, collective_field, hay_aliados)

        # Rutina normal de la agenda
        if actividad in ("dormir", "descansar"):
            return None
        if actividad == "buscar_alimento":
            return self._find_food_action(tp, snapshot)
        if actividad == "buscar_agua":
            return self._find_water_action(tp, snapshot)
        if actividad == "cazar":
            return self._hunt_action(tp, snapshot)
        if actividad == "explorar":
            return self._choose_explore_or_gather(tp, snapshot)
        return None

    def _decide_via_collapse(
        self,
        tp:       TimePoint,
        snapshot: WorldSnapshot,
        collective_field: CollectiveField | None = None,
        hay_aliados: bool = False,
    ) -> WorldAction | None:
        """
        Usa el motor cuántico para decidir la acción en horas sociales.
        Considera la influencia del campo colectivo y la presencia de aliados.
        """
        context = {
            "peligro":         snapshot.survival_risk,
            "recursos_escasos": snapshot.resource_pressure > 0.7,
            "hay_aliados":     hay_aliados,
            "hay_amenaza":     snapshot.survival_risk > 0.5,
        }

        arch_biases = {
            a: self.archetypes.action_bias(a) for a in
            ("cooperacion", "competencia", "aislamiento", "manipulacion")
        }
        complex_biases = {
            a: self.complexes.action_bias(a) for a in
            ("cooperacion", "competencia", "aislamiento", "manipulacion")
        }
        trait_biases = {
            a: self.traits.action_bias(a) for a in
            ("cooperacion", "competencia", "aislamiento", "manipulacion")
        }

        # Obtener influencia del campo memético colectivo
        field_influence = collective_field.radiate() if collective_field is not None else None

        accion = collapse_state(
            state            = self.behavioral_state,
            context          = context,
            archetype_biases = arch_biases,
            complex_biases   = complex_biases,
            trait_biases     = trait_biases,
            field_influence  = field_influence,
            rng              = self._rng,
        )

        # Traducir colapso a WorldAction (Fase 7: socializar localmente vs explorar solo)
        if accion == "aislamiento":
            return self._explore_action(tp, snapshot)  # Se aleja del grupo

        # Si coopera, compite o manipula, prioriza permanecer en su hexágono para propiciar encuentros
        coord = self.posicion
        if accion in ("cooperacion", "manipulacion"):
            food = self._get_nearby_food(coord, snapshot)
            if food is not None:
                return WorldAction(
                    agent_id = self.id,
                    tick     = tp.tick,
                    type     = ActionType.RECOLECTAR,
                    coord    = coord,
                    params   = {"resource": food, "amount": 0.15},
                    priority = 0.7,
                )
            # Intentar agua local
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
        elif accion == "competencia":
            fauna = snapshot.fauna_visible.get(coord, {})
            target = "grande" if fauna.get("grande", 0) > 0.2 else "pequena"
            if fauna.get(target, 0) > 0.05:
                return WorldAction(
                    agent_id = self.id,
                    tick     = tp.tick,
                    type     = ActionType.CAZAR,
                    coord    = coord,
                    params   = {"fauna_type": target, "amount": 0.10},
                    priority = 0.6,
                )

        # Si no hay recursos locales que recolectar/cazar, realiza movimiento local estático para socializar
        return WorldAction(
            agent_id = self.id,
            tick     = tp.tick,
            type     = ActionType.MOVERSE,
            coord    = coord,
            params   = {"socializing": True},
            priority = 0.5,
        )

    # ── Action builders ──────────────────────────────────────────────────────

    def _find_food_action(self, tp: TimePoint, snapshot: WorldSnapshot) -> WorldAction | None:
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

    def _find_water_action(self, tp: TimePoint, snapshot: WorldSnapshot) -> WorldAction | None:
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

    def _hunt_action(self, tp: TimePoint, snapshot: WorldSnapshot) -> WorldAction | None:
        coord  = self.posicion
        fauna  = snapshot.fauna_visible.get(coord, {})
        target = "grande" if fauna.get("grande", 0) > 0.2 else "pequena"
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

    def _explore_action(self, tp: TimePoint, snapshot: WorldSnapshot) -> WorldAction:
        q, r = self.posicion
        # Rasgos influyen en la dirección de exploración (por ahora, aleatoria)
        directions = [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
        
        valid_targets = []
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            # Mantener dentro de la grilla 80x60
            if 0 <= nq < 80 and 0 <= nr < 60:
                valid_targets.append((nq, nr))
                
        if valid_targets:
            target = self._rng.choice(valid_targets)
        else:
            target = (q, r)  # Fallback si no hay salidas válidas
            
        self.posicion = target
        return WorldAction(
            agent_id = self.id,
            tick     = tp.tick,
            type     = ActionType.EXPLORAR,
            coord    = target,
            params   = {},
            priority = 0.3,
        )

    def _choose_explore_or_gather(self, tp: TimePoint, snapshot: WorldSnapshot) -> WorldAction | None:
        """
        Exploradores y agentes con alta apertura prefieren explorar;
        los demás buscan recursos.
        """
        if self._rng.random() < self.traits.exploration_drive():
            return self._explore_action(tp, snapshot)
        return self._find_food_action(tp, snapshot)

    def _get_nearby_food(self, coord: tuple[int, int], snapshot: WorldSnapshot) -> str | None:
        resources = snapshot.recursos_por_hex.get(coord, {})
        food_types = ["frutos", "raices", "plantas", "semillas", "peces"]
        for ft in food_types:
            if resources.get(ft, 0) > 0.1:
                return ft
        return None

    def _apply_resource_gain(self, resources: dict) -> None:
        food_types  = {"frutos", "raices", "plantas", "semillas", "carne", "peces"}
        water_types = {"agua", "agua_lluvia", "agua_fresca", "agua_subterranea", "agua_salobre"}
        for rtype, qty in resources.items():
            if rtype in food_types:
                self.needs.eat(qty * _COMIDA_POR_RECOLECTA)
            elif rtype in water_types:
                self.needs.drink(qty * _AGUA_POR_BEBER)

    # ── Acceso psicológico rápido ─────────────────────────────────────────────

    @property
    def arquetipo_dominante(self) -> str:
        return self.archetypes.dominant()

    @property
    def estado_conductual(self) -> str:
        return self.behavioral_state.ultimo_colapso

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
            # Psicología (para inspector/dashboard)
            "arquetipo_dominante": self.arquetipo_dominante,
            "estado_conductual":   self.estado_conductual,
        }

    def to_dict(self) -> dict:
        return {
            **self.snapshot(),
            "episodic_log":      list(self.episodic_log),
            "schedule":         self.schedule.to_dict(),
            "archetypes":       self.archetypes.to_dict(),
            "complexes":        self.complexes.to_dict(),
            "traits":           self.traits.to_dict(),
            "behavioral_state": self.behavioral_state.to_dict(),
            "base_state":       self._base_state.to_dict() if self._base_state else None,
            "dreams":           [
                {
                    "dia":          d.dia,
                    "simbolo":      d.simbolo,
                    "arquetipo":    d.arquetipo,
                    "complejo":     d.complejo,
                    "procesamiento": d.procesamiento,
                    "insight":      d.insight,
                }
                for d in self.dreams
            ],
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

        # Psicología
        if "archetypes" in data:
            a.archetypes = ArchetypeVector.from_dict(data["archetypes"])
        if "complexes" in data:
            a.complexes = ComplexProfile.from_dict(data["complexes"])
        if "traits" in data:
            a.traits = TraitProfile.from_dict(data["traits"])
        if "behavioral_state" in data:
            a.behavioral_state = BehavioralState.from_dict(data["behavioral_state"])
        if "base_state" in data and data["base_state"]:
            a._base_state = BehavioralState.from_dict(data["base_state"])

        a.episodic_log = data.get("episodic_log", [])

        return a
