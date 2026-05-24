from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.interface import ActionType, WorldAction, WorldSnapshot
from core.time import TimePoint
from core.world.substances import SUBSTANCES, SUBSTANCE_NAMES
from core.social.perception import PerceptionSystem
from .needs import Needs, CRITICAL_THRESHOLD, OVERRIDE_THRESHOLD
from .schedule import ScheduleSystem
from .psyche.archetypes import ArchetypeVector
from .psyche.complexes import ComplexProfile
from .psyche.traits import TraitProfile
from .psyche.dreams import DreamGrammarEngine, Dream, extract_traumas_from_log
from .quantum.superposition import BehavioralState
from .quantum.collapse import collapse_state

if TYPE_CHECKING:
    pass

_DIAS_HAMBRE_MUERTE   = 3
_DIAS_SED_MUERTE      = 3
_COMIDA_POR_RECOLECTA = 4.0
_COMIDA_POR_CAZA      = 8.0
_AGUA_POR_BEBER       = 5.0
# Ciclo de vida
_EDAD_INFANCIA        = 15   # antes de esta edad el agente es dependiente
_EDAD_VEJEZ_INICIO    = 50   # a partir de aquí hay riesgo de muerte por vejez
_PROB_BASE_VEJEZ      = 0.01 # probabilidad anual base; se duplica cada 5 años


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
        self._dream_engine  = DreamGrammarEngine()
        self.dreams: list[Dream] = []
        self.bioma_actual: str = "tierra"

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

        # Última posición conocida donde se encontró agua (navegación de emergencia)
        self._last_known_water: tuple[int, int] | None = None

        # Sustancias
        self._active_substances: dict[str, int]   = {}  # nombre → ticks restantes
        self._addiction:         dict[str, float] = {}  # nombre → nivel (0-1)
        self._psychoactive_consumed: bool         = False  # flag transient para cadena chamánica

        # Ciclo de vida
        self._padres:                tuple[str, str] | None = None
        self._cooldown_reproduccion: int = 0

        self._rng = random.Random(seed)

        # Episodic Memory Log (Fase 8)
        self.episodic_log: list[str] = []

        # Zona Liminal — True cuando el agente está en tránsito intersimulación
        self.in_liminal: bool = False
        # Encuentro liminal pendiente de procesar en el próximo ciclo de sueños
        self._pending_liminal_encounter: dict | None = None

        # Percepción limitada: radio de visión, rumores y sesgo causal
        self._perception = PerceptionSystem()

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    @property
    def es_infante(self) -> bool:
        return self.edad < _EDAD_INFANCIA

    def _need_factor(self) -> float:
        """Factor de decay de necesidades según edad. 0.2 en la infancia, 1.0 en adultos."""
        if self.edad >= _EDAD_INFANCIA:
            return 1.0
        if self.edad <= 4:
            return 0.2
        # Transición lineal 0.2 → 1.0 entre los 4 y los 15 años
        return 0.2 + (self.edad - 4) * (0.8 / (_EDAD_INFANCIA - 4))

    def _vigor_por_edad(self) -> float:
        """Multiplicador de energía efectiva. Declina gradualmente a partir de los 40."""
        if self.edad <= 40:
            return 1.0
        if self.edad <= 65:
            return max(0.70, 1.0 - (self.edad - 40) * 0.012)
        return max(0.40, 0.70 - (self.edad - 65) * 0.015)

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

        nf = self._need_factor()
        if actividad == "dormir":
            self.needs.update_sleeping(need_factor=nf)
        else:
            self.needs.update_waking(need_factor=nf)

        # Aplicar resultado de la acción del tick anterior
        if self.id in snapshot.action_results:
            result = snapshot.action_results[self.id]
            if result.success and result.resource_gained:
                self._apply_resource_gain(result.resource_gained)

        # Actualizar efectos de sustancias activas
        self._tick_substances()

        # Complejos decaen por tick
        self.complexes.decay_tick()

        # Decay del estado cuántico hacia el estado base
        if self._base_state is not None:
            self.behavioral_state.decay_toward_base(self._base_state, rate=0.01)

        # Estado emocional integrado
        self._update_emotional_state()

    def _update_emotional_state(self) -> None:
        """Integra biología, psicología y cuántica en el estado emocional."""
        stress = self.needs.stress_level
        mood_base = self.traits.mood_modifier()
        complejo_ansiedad = 0.10 if self.complexes.activos else 0.0

        self.ansiedad = min(1.0, stress * (1.0 + self.traits.stress_sensitivity()) + complejo_ansiedad)
        self.humor    = max(0.0, 1.0 - stress + mood_base * 0.3)
        self.energia  = max(0.0, (1.0 - self.needs.fatiga) * self._vigor_por_edad())

    def _process_dream(
        self,
        dia:               int,
        bioma:             str = "tierra",
        resonancia_grupal: str | None = None,
    ) -> None:
        """Genera un sueño y aplica sus deltas arquetípicos."""
        # Consumir encuentro liminal pendiente como resonancia si no hay otra activa
        if resonancia_grupal is None and self._pending_liminal_encounter:
            resonancia_grupal = self._pending_liminal_encounter.get("resonancia")
            self._pending_liminal_encounter = None

        traumas = extract_traumas_from_log(self.episodic_log)
        dream = self._dream_engine.generate_dream(
            dia               = dia,
            dominante         = self.archetypes.dominant(),
            tension           = self.archetypes.tension(),
            complejo_activo   = self.complexes.most_active(),
            bioma             = bioma,
            traumas_recientes = traumas,
            resonancia_grupal = resonancia_grupal,
            rng               = self._rng,
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

        # Senectud: probabilidad diaria exponencial a partir de _EDAD_VEJEZ_INICIO
        # Prob. anual = 2^((edad - inicio) / 5) * base → se duplica cada 5 años de más
        if self.edad >= _EDAD_VEJEZ_INICIO:
            prob_anual = (2 ** ((self.edad - _EDAD_VEJEZ_INICIO) / 5)) * _PROB_BASE_VEJEZ
            if self._rng.random() < min(1.0, prob_anual / 365):
                self.is_alive = False
                return "vejez"

        return None

    def on_day(self, tp: TimePoint) -> None:
        """Llamado al inicio de cada nuevo día."""
        if not self.is_alive:
            return
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

        # Aislamiento crítico: el agente busca interacción aunque no sea su hora de socializar
        if self.needs.social_override_active():
            return self._decide_via_collapse(tp, snapshot, collective_field, hay_aliados)

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
            # En horas de exploración, los agentes con afinidad arquetípica pueden
            # ser atraídos por una tumba sagrada activa cercana (peregrinación emergente)
            pilgrimage = self._find_pilgrimage_site(snapshot)
            if pilgrimage is not None and self._rng.random() < 0.20:
                action = self._pilgrimage_action(tp, pilgrimage)
                if action is not None:
                    return action
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
        # Interactuar satisface la necesidad social
        self.needs.socialize()

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
            water_sources = ["agua", "agua_lluvia", "agua_fresca", "agua_subterranea",
                             "agua_salobre", "nieve"]
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
        water_sources = ["agua", "agua_lluvia", "agua_fresca", "agua_subterranea",
                         "agua_salobre", "nieve"]

        # Buscar primero en el hex actual, luego anillo 1 (6 hexes) y anillo 2 (12 hexes)
        q, r = self.posicion
        ring1 = [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
        ring2 = [(2,0),(-2,0),(0,2),(0,-2),(2,-2),(-2,2),
                 (1,1),(-1,-1),(2,-1),(-2,1),(1,-2),(-1,2)]
        candidates = [(q, r)] + [
            (q + dq, r + dr)
            for dq, dr in ring1 + ring2
            if 0 <= q + dq < 80 and 0 <= r + dr < 60
        ]

        for coord in candidates:
            resources = snapshot.recursos_por_hex.get(coord, {})
            for water in water_sources:
                if resources.get(water, 0) > 0.1:
                    if coord != self.posicion:
                        # Movimiento: un tick para llegar, recolectar el próximo
                        self.posicion = coord
                        return WorldAction(
                            agent_id = self.id,
                            tick     = tp.tick,
                            type     = ActionType.MOVERSE,
                            coord    = coord,
                            params   = {},
                            priority = 0.8,
                        )
                    return WorldAction(
                        agent_id = self.id,
                        tick     = tp.tick,
                        type     = ActionType.RECOLECTAR,
                        coord    = coord,
                        params   = {"resource": water, "amount": 0.20},
                        priority = 0.9,
                    )

        # Sin agua en radio 2: navegar hacia la última fuente conocida, o explorar
        if self._last_known_water is not None and self._last_known_water != self.posicion:
            target = self._step_toward(self._last_known_water)
            self.posicion = target
            return WorldAction(
                agent_id = self.id,
                tick     = tp.tick,
                type     = ActionType.MOVERSE,
                coord    = target,
                params   = {},
                priority = 0.85,
            )
        return self._explore_action(tp, snapshot)

    def _find_pilgrimage_site(
        self,
        snapshot: WorldSnapshot,
    ) -> tuple[int, int] | None:
        """
        Busca la tumba sagrada activa más cercana cuyo arquetipo dominante
        coincide con el del agente. Sólo considera sitios a ≤ 10 hexes.
        """
        my_arch = self.archetypes.dominant()
        my_arch_norm = "self_" if my_arch == "self" else my_arch
        q, r = self.posicion
        best: tuple[int, int] | None = None
        best_dist = float("inf")
        for coord, carga, arch in snapshot.graves_activos:
            if arch != my_arch_norm:
                continue
            dist = abs(coord[0] - q) + abs(coord[1] - r)
            if dist < best_dist and dist <= 10:
                best_dist = dist
                best = coord
        return best

    def _pilgrimage_action(
        self,
        tp:     TimePoint,
        target: tuple[int, int],
    ) -> WorldAction | None:
        """Avanza un paso hacia la tumba sagrada."""
        if target == self.posicion:
            return None
        dest = self._step_toward(target)
        self.posicion = dest
        return WorldAction(
            agent_id = self.id,
            tick     = tp.tick,
            type     = ActionType.MOVERSE,
            coord    = dest,
            params   = {"pilgrimage": True},
            priority = 0.55,
        )

    def _step_toward(self, target: tuple[int, int]) -> tuple[int, int]:
        """Avanza un hex en dirección al objetivo usando distancia Manhattan."""
        tq, tr = target
        q, r   = self.posicion
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        best = min(
            directions,
            key=lambda d: abs((q + d[0]) - tq) + abs((r + d[1]) - tr),
        )
        nq, nr = q + best[0], r + best[1]
        if 0 <= nq < 80 and 0 <= nr < 60:
            return (nq, nr)
        return self.posicion

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
        los demás buscan recursos. Si hay una sustancia en el hex actual,
        la consumen accidentalmente con cierta probabilidad.
        """
        # Contacto accidental con sustancia
        substance = self._get_nearby_substance(snapshot)
        if substance and self._rng.random() < 0.35:
            return WorldAction(
                agent_id = self.id,
                tick     = tp.tick,
                type     = ActionType.RECOLECTAR,
                coord    = self.posicion,
                params   = {"resource": substance, "amount": 0.10},
                priority = 0.50,
            )
        if self._rng.random() < self.traits.exploration_drive():
            return self._explore_action(tp, snapshot)
        return self._find_food_action(tp, snapshot)

    def _get_nearby_substance(self, snapshot: WorldSnapshot) -> str | None:
        resources = snapshot.recursos_por_hex.get(self.posicion, {})
        for rtype, qty in resources.items():
            if rtype in SUBSTANCE_NAMES and qty > 0.1:
                return rtype
        return None

    def _get_nearby_food(self, coord: tuple[int, int], snapshot: WorldSnapshot) -> str | None:
        resources = snapshot.recursos_por_hex.get(coord, {})
        food_types = ["frutos", "raices", "plantas", "semillas", "peces"]
        for ft in food_types:
            if resources.get(ft, 0) > 0.1:
                return ft
        return None

    def _apply_resource_gain(self, resources: dict) -> None:
        food_types  = {"frutos", "raices", "plantas", "semillas", "carne", "peces"}
        water_types = {"agua", "agua_lluvia", "agua_fresca", "agua_subterranea",
                       "agua_salobre", "nieve"}
        for rtype, qty in resources.items():
            if rtype in food_types:
                self.needs.eat(qty * _COMIDA_POR_RECOLECTA)
            elif rtype in water_types:
                self.needs.drink(qty * _AGUA_POR_BEBER)
                self._last_known_water = self.posicion
            elif rtype in SUBSTANCE_NAMES:
                self._consume_substance(rtype)

    # ── Sustancias ────────────────────────────────────────────────────────────

    def _consume_substance(self, name: str) -> None:
        """
        Aplica los efectos de una sustancia al agente.
        Si el agente está en tránsito liminal, los efectos se amplían × 1.5.
        """
        defn = SUBSTANCES.get(name)
        if defn is None:
            return

        amp = 1.5 if self.in_liminal else 1.0

        # Registrar efecto activo (se extiende si ya estaba activo)
        self._active_substances[name] = defn.duration_ticks

        # Efectos arquetípicos
        for arch_attr, delta in defn.archetype_effects.items():
            current = getattr(self.archetypes, arch_attr, None)
            if current is not None:
                setattr(self.archetypes, arch_attr,
                        max(0.0, min(1.0, current + delta * amp)))

        # Efecto físico: positivo = sana; negativo = daña (sube fatiga)
        if defn.physical_effect > 0:
            self.needs.eat(defn.physical_effect * 0.50)
            self.needs.drink(defn.physical_effect * 0.30)
        else:
            self.needs.fatiga = min(1.0, self.needs.fatiga + abs(defn.physical_effect) * amp)

        # Adicción progresiva
        if defn.addiction_rate > 0:
            self._addiction[name] = min(
                1.0, self._addiction.get(name, 0.0) + defn.addiction_rate * 0.10
            )

        # Flag para cadena chamánica (procesado en AgentCore.on_tick)
        if defn.is_psychoactive:
            self._psychoactive_consumed = True

        self.episodic_log.append(
            f"Consumió {name} (x{amp:.1f}). "
            f"Efectos: {list(defn.archetype_effects.keys())}."
        )

    def _tick_substances(self) -> None:
        """Decrementa duración de efectos activos; aplica abstinencia si hay adicción."""
        # Tick down
        vencidos = [n for n, t in self._active_substances.items() if t <= 1]
        for n in vencidos:
            del self._active_substances[n]
        for n in list(self._active_substances):
            self._active_substances[n] -= 1

        # Abstinencia: adicción sin efecto activo → estrés y degradación de rasgos
        for name, level in self._addiction.items():
            if level > 0.30 and name not in self._active_substances:
                self.needs.fatiga = min(1.0, self.needs.fatiga + level * 0.005)
                if level > 0.60:
                    self.traits.estabilidad_emocional = max(
                        0.0, self.traits.estabilidad_emocional - 0.001
                    )
                    self.traits.neuroticismo = min(1.0, self.traits.neuroticismo + 0.001)

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
            "dias_hambre_critica":    self._dias_hambre_critica,
            "dias_sed_critica":       self._dias_sed_critica,
            "padres":                 list(self._padres) if self._padres else None,
            "cooldown_reproduccion":  self._cooldown_reproduccion,
            # Psicología (para inspector/dashboard)
            "arquetipo_dominante": self.arquetipo_dominante,
            "estado_conductual":   self.estado_conductual,
        }

    def to_dict(self) -> dict:
        return {
            **self.snapshot(),
            "last_known_water":  list(self._last_known_water) if self._last_known_water else None,
            "active_substances": dict(self._active_substances),
            "addiction":         dict(self._addiction),
            "perception":        self._perception.to_dict(),
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
                    "bioma":        d.bioma,
                    "traumas":      d.traumas,
                    "shared_with":  d.shared_with,
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
        a._dias_hambre_critica       = data.get("dias_hambre_critica", 0)
        a._dias_sed_critica          = data.get("dias_sed_critica", 0)
        lkw                          = data.get("last_known_water")
        a._last_known_water          = tuple(lkw) if lkw else None
        a._active_substances         = dict(data.get("active_substances", {}))
        a._addiction                 = {k: float(v) for k, v in data.get("addiction", {}).items()}
        a._perception                = PerceptionSystem.from_dict(data.get("perception", {}))
        padres_raw                   = data.get("padres")
        a._padres                    = tuple(padres_raw) if padres_raw else None
        a._cooldown_reproduccion     = data.get("cooldown_reproduccion", 0)

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
