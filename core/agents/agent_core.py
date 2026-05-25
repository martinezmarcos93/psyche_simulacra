from __future__ import annotations

import random
from typing import TYPE_CHECKING

from core.time import TimePoint
from core.interface import WorldAction
from .agent import Agent
from .psyche.archetypes import ARCHETYPE_NAMES
from .psyche.dreams import _ARCHETYPE_SYMBOLS, _DEFAULT_SYMBOL
from .psyche.traits import TraitProfile
from core.social.network import SocialNetwork
from core.social.interaction import InteractionEngine
from core.social.collective_field import CollectiveField
from core.social.mythology import MythologyEngine
from core.social.tribe_manager import TribeManager
from core.world.culture_engine import CultureEngine
from core.social.genealogy import LineageGraph
from core.social.knowledge import KnowledgeSystem, KnowledgeUnit, _ALL_KNOWLEDGE, _DISCOVERY_TRIGGERS

if TYPE_CHECKING:
    from core.world import WorldCore

# Pool de nombres para la descendencia (nombres no usados por los fundadores)
_NOMBRES_POOL = [
    # Daímones y abstracciones olímpicas
    "Zelos", "Nike", "Kratos", "Bia", "Anteros", "Tyche", "Nemesis",
    "Eunomia", "Dike", "Eirene", "Thanatos", "Hypnos", "Morpheus",
    "Oizys", "Geras", "Momos", "Thallo", "Auxo", "Karpo", "Aglaea",
    "Euphrosyne", "Phanes", "Ananke", "Aether", "Hemera", "Nyx",
    "Alke", "Harmonia", "Arke", "Calais", "Zetes", "Chloris",
    "Acantha", "Adrasteia", "Aeolus", "Aletheia", "Alpheus",
    # Ninfas y héroes menores
    "Calypso", "Circe", "Medea", "Ariadne", "Phaedra", "Semele",
    "Alcyone", "Celaeno", "Sterope", "Merope", "Electra", "Taygete",
    "Maia", "Dione", "Metis", "Thetis", "Doris", "Galene",
    "Amphitrite", "Leucothea", "Ino", "Procne", "Philomela", "Niobe",
    "Atalanta", "Andromache", "Penthesilea", "Camilla",
    # Dioses menores y titánides
    "Eos", "Helios", "Boreas", "Notos", "Euros",
    "Proteus", "Glaukos", "Nereus", "Triton", "Pontus", "Oceanus",
    "Iapetos", "Koios", "Krios", "Hyperion", "Mnemosyne",
    "Themis", "Tethys",
    # Héroes épicos y sus allegados
    "Achilleas", "Patroklos", "Diomedes", "Telamon", "Peleus", "Aeacus",
    "Bellerophon", "Chrysaor", "Chryseis", "Briseis",
    "Laodamia", "Polyxena", "Andromeda", "Erigone", "Iphigenia",
    # Nombres líricos y pastorales
    "Amaryllis", "Lycidas", "Daphnis", "Chloe", "Melibea", "Thyrsis",
    "Alexis", "Menalcas", "Corydon", "Chromis", "Mnasyllos", "Aegon",
]

_BOND_REPRODUCCION    = 0.70   # vínculo mínimo para reproducirse
_EDAD_MIN_REPRO       = 16
_EDAD_MAX_REPRO       = 45
_PROB_REPRO_DIARIA    = 0.003  # 0.3% por par elegible por día (~1 nac./año con 3 pares)
_COOLDOWN_REPRO       = 300    # días de espera post-nacimiento por padre
_LIMITE_POBLACION     = 150    # máximo de agentes simultáneos


class AgentCore:
    """
    Núcleo 2 — Los agentes.
    Registrado en SimulationClock con priority=20 (después del WorldCore).
    Lee WorldSnapshot, actualiza cada agente, envía WorldAction[] al WorldCore.
    """

    def __init__(self, world_ref: WorldCore) -> None:
        self.world_ref:  WorldCore          = world_ref
        self.agents:     dict[str, Agent]   = {}
        self._death_log: list[dict]         = []
        self._birth_log: list[dict]         = []

        # Ciclo de vida — estado de reproducción
        self._rng               = random.Random()
        self._nombres_usados:   set[str] = set()
        self._proximo_id_hijo:  int = 0

        # Inicialización de Capas de Sistemas Sociales (Fase 7)
        self.social_network     = SocialNetwork()
        self.interaction_engine = InteractionEngine()
        self.collective_field   = CollectiveField()
        self.mythology_engine   = MythologyEngine()
        # Tribus y campos locales (Fase 2)
        self.tribe_manager      = TribeManager()
        # Cultura material — estructuras y auras (Fase 4)
        self.culture_engine     = CultureEngine()
        # Árbol genealógico (Hito 7)
        self.lineage            = LineageGraph()
        # Registro de ataques por tribu: tribe_id → [dia, ...] (Hito 9)
        self._tribal_attacks: dict[str, list[int]] = {}
        # Sistema de conocimiento técnico (Hito 10)
        self.knowledge = KnowledgeSystem()

    # ── Population management ─────────────────────────────────────────────────

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.id] = agent
        self.social_network.add_agent(agent.id)
        # Registrar en árbol genealógico si aún no existe (fundadores: sin padres)
        if agent.id not in self.lineage.records:
            tribe_orig = self.tribe_manager.get_tribe_id(agent.id) or ""
            self.lineage.register(agent.id, None, None, dia=0, tribe_orig=tribe_orig)

    def remove_agent(self, agent_id: str) -> None:
        self.agents.pop(agent_id, None)
        # Remover nodo de red social
        self.social_network.remove_agent(agent_id)

    def alive_count(self) -> int:
        return sum(1 for a in self.agents.values() if a.is_alive)

    # ── SimulationClock handlers ──────────────────────────────────────────────

    def on_tick(self, tp: TimePoint) -> None:
        """Called by SimulationClock at priority=20."""
        snapshot = self.world_ref.current_snapshot
        if snapshot is None:
            return

        actions: list[WorldAction] = []
        # Precomputar conteo de agentes por posición para saber si hay aliados
        pos_counts: dict[tuple[int, int], int] = {}
        for a in self.agents.values():
            if a.is_alive and not a.in_liminal:
                pos_counts[a.posicion] = pos_counts.get(a.posicion, 0) + 1

        for agent in self.agents.values():
            if not agent.is_alive or agent.in_liminal:
                continue
            agent.update_biological(tp, snapshot)
            hay_aliados = pos_counts.get(agent.posicion, 0) > 1
            # Usa el campo tribal local (si existe) para el colapso cuántico
            local_field = self.tribe_manager.get_local_field(agent.id) or self.collective_field
            action = agent.decide_action(tp, snapshot, local_field, hay_aliados)
            if action is not None:
                actions.append(action)

        # Resolución de interacciones sociales en la zona (Fase 7)
        self.interaction_engine.process_zone_interactions(
            self.agents,
            self.social_network,
            self.collective_field,
            self.mythology_engine,
            dia=tp.dia_simulado,
            tribe_manager=self.tribe_manager,
        )

        # Propagación de entrelazamientos emocionales (Fase 7)
        self.social_network.propagate_entanglement(self.agents)

        if actions:
            self.world_ref.receive_actions(actions)

        # Cadena chamánica: agentes que consumieron una sustancia psicoactiva este tick
        # forman vínculo con los co-presentes; el consumidor gana sabio.
        for agent in self.agents.values():
            if not agent._psychoactive_consumed:
                continue
            agent._psychoactive_consumed = False
            agent.archetypes.sabio = min(1.0, agent.archetypes.sabio + 0.02)
            for other in self.agents.values():
                if other.id == agent.id or not other.is_alive:
                    continue
                if other.posicion == agent.posicion:
                    b_ao = self.social_network.get_bond(agent.id, other.id)
                    b_oa = self.social_network.get_bond(other.id, agent.id)
                    self.social_network.set_bond(agent.id, other.id, min(1.0, b_ao + 0.05))
                    self.social_network.set_bond(other.id, agent.id, min(1.0, b_oa + 0.05))

    def on_day(self, tp: TimePoint) -> None:
        """Called once per simulated day — runs death checks and social dynamics."""
        # 1. Decaimiento y evolución del campo memético global (Fase 7)
        self.collective_field.decay()

        # 1b. Atención selectiva a eventos climáticos + propagación de rumores (Hito 4)
        self._process_selective_attention(tp.dia_simulado)

        # 2. Cristalización y feedback mítico global — on_day() ya incluye apply_myth_effects()
        self.mythology_engine.check_crystallization(self.collective_field, self.agents, tp.dia_simulado)

        # 2b. Mecánicas tribales: re-clustering, campos locales, mitos locales, deriva de bioma (Fase 2)
        terrain = getattr(self.world_ref, "terrain", None)
        self.tribe_manager.on_day(
            self.agents,
            self.social_network,
            self.collective_field,
            terrain,
            tp.dia_simulado,
        )

        # 2c. Cultura material: construcción de estructuras y aplicación de auras (Fase 4)
        if terrain is not None:
            self.culture_engine.on_day(
                self.agents,
                self.tribe_manager.tribes,
                terrain,
                tp.dia_simulado,
            )

        # 3. Control de vitalidad (hambre, sed, vejez)
        for agent in list(self.agents.values()):
            if not agent.is_alive:
                continue
            cause = agent.check_death()
            if cause is not None:
                self._register_death(agent, tp, cause)

        # 3b. Mortalidad selectiva por catástrofe (Hito 5)
        cat_engine = getattr(self.world_ref, "catastrophe", None)
        if cat_engine is not None and cat_engine.active is not None:
            self._process_catastrophe_mortality(tp, cat_engine)

        # 3d. Migración forzada: catástrofe sube ansiedad → agents deciden moverse (Hito 5)
        if cat_engine is not None and cat_engine.active is not None:
            self._process_catastrophe_anxiety(tp, cat_engine)

        # 3g. Celos y conflicto de vínculo (Hito 7)
        self._process_jealousy(tp)

        # 3h. Efectos de hexes liminales: inyección autónoma + amplificación arq. (Hito 8)
        liminal_sys = getattr(self.world_ref, "liminal_system", None)
        if liminal_sys is not None:
            self._process_liminal_hex_effects(tp, liminal_sys)

        # 3f. Fauna simbólica: depredadores, fauna rara, migración (Hito 6)
        fauna_sys = getattr(self.world_ref, "fauna_symbolic", None)
        if fauna_sys is not None:
            self._process_symbolic_fauna(tp, fauna_sys)

        # 3e. Orfandad: infantes cuyos dos padres han muerto
        for agent in list(self.agents.values()):
            if not agent.is_alive or not agent.es_infante or agent._padres is None:
                continue
            pa = self.agents.get(agent._padres[0])
            pb = self.agents.get(agent._padres[1])
            if (pa is None or not pa.is_alive) and (pb is None or not pb.is_alive):
                self._register_death(agent, tp, "orfandad")

        # 4. Envejecimiento anual (un año simulado = 360 días)
        if tp.dia_simulado > 0 and tp.dia_simulado % 360 == 0:
            for agent in self.agents.values():
                if agent.is_alive:
                    agent.edad += 1

        # 5. Decrementar cooldowns de reproducción
        for agent in self.agents.values():
            if agent.is_alive and agent._cooldown_reproduccion > 0:
                agent._cooldown_reproduccion -= 1

        # 6. Reproducción
        self._check_reproduccion(tp)

        # 7. Resonancia grupal por sustancias: ≥2 agentes bajo efecto en el mismo hex
        #    amplifican el campo memético local.
        hex_sub_agents: dict[tuple, list] = {}
        for agent in self.agents.values():
            if agent.is_alive and agent._active_substances:
                hex_sub_agents.setdefault(agent.posicion, []).append(agent)
        for hex_agents in hex_sub_agents.values():
            if len(hex_agents) >= 2:
                lf = self.tribe_manager.get_local_field(hex_agents[0].id)
                if lf is not None:
                    lf.absorb_event("resonancia_enteogenica",
                                    intensity=min(1.0, 0.30 * len(hex_agents)))
                # Registrar en memoria cultural tribal
                tribe_id = self.tribe_manager.get_tribe_id(hex_agents[0].id)
                if tribe_id:
                    cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                    if cmem is not None:
                        nombres = ", ".join(a.nombre for a in hex_agents[:3])
                        subs = next(iter(hex_agents[0]._active_substances), "sustancia")
                        cmem.record_event(
                            dia                 = tp.dia_simulado,
                            agente_nombre       = hex_agents[0].nombre,
                            arquetipo_dominante = "sabio",
                            tipo_evento         = "vision_colectiva",
                            descripcion         = (
                                f"{nombres} compartieron una visión de {subs} "
                                f"en el día {tp.dia_simulado}."
                            ),
                            intensidad          = 0.70,
                        )

        # 8. "El muerto que tiene más poder que vivo":
        #    si un registro cultural tiene alta intensidad y muchas transmisiones,
        #    su protagonista (fallecido) se convierte en figura mítica que sostiene el ICL.
        self._check_mythic_dead(tp.dia_simulado)

        # 9. Sueños nocturnos con entrelazamiento
        self._process_nightly_dreams(tp.dia_simulado)

        # 10. Contagio emocional: agentes muy ansiosos propagan miedo a sus vínculos (Hito 4)
        self._process_emotional_contagion(tp.dia_simulado)

        # 11. Histeria colectiva: chequeo multi-umbral por tribu (Hito 4)
        self._check_collective_hysteria(tp.dia_simulado)

        # 12. Sesgo causal → tabúes en memoria cultural (Hito 4)
        self._process_causal_bias(tp.dia_simulado)

        # 13. Proyección/autoengaño: complejo activo → atribuido al otro (Hito 9)
        self._process_projection(tp.dia_simulado)

        # 14. Sesgo de atribución: fracaso propio → externo; ajeno → interno (Hito 9)
        self._process_attribution_bias(tp.dia_simulado)

        # 15. Paranoia tribal: historial de ataques → eventos neutros = amenaza (Hito 9)
        self._process_tribal_paranoia(tp.dia_simulado)

        # 16. Disonancia cognitiva: mito activo + muertes → reforma religiosa (Hito 9)
        self._process_cognitive_dissonance(tp.dia_simulado)

        # 17a. Descubrimiento accidental de conocimiento técnico (Hito 10)
        self._process_knowledge_discovery(tp)

        # 17b. Transmisión de conocimiento entre co-ubicados (Hito 10)
        self._process_knowledge_transmission(tp)

        # 17c. Asimetría de poder: especialistas atraen dependencia (Hito 10)
        self._process_knowledge_power(tp)

    # ── Helpers ciclo de vida ─────────────────────────────────────────────────

    def _register_death(self, agent: Agent, tp: TimePoint, causa: str) -> None:
        agent.is_alive = False
        agent.episodic_log.append(f"Día {tp.dia_simulado}: Falleció a causa de {causa}.")
        self._death_log.append({
            "tick":     tp.tick,
            "dia":      tp.dia_simulado,
            "agent_id": agent.id,
            "nombre":   agent.nombre,
            "causa":    causa,
        })

        # Extinción de conocimiento: si era el único portador, el saber muere con él
        extinct = self.knowledge.remove_agent(agent.id, tp.dia_simulado)
        if extinct:
            tribe_id = self.tribe_manager.get_tribe_id(agent.id)
            lf       = (self.tribe_manager.local_fields.get(tribe_id)
                        if tribe_id else None) or self.collective_field
            lf.myth_pressure = min(1.0, lf.myth_pressure + 0.15 * len(extinct))
            lf.confusion     = min(1.0, lf.confusion     + 0.10 * len(extinct))
            if tribe_id:
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is not None:
                    for kname in extinct:
                        cmem.record_event(
                            dia=tp.dia_simulado,
                            agente_nombre=agent.nombre,
                            arquetipo_dominante="sabio",
                            tipo_evento="conocimiento_extinto",
                            descripcion=(
                                f"Con la muerte de {agent.nombre}, el conocimiento "
                                f"'{kname}' se perdió para siempre el día {tp.dia_simulado}."
                            ),
                            intensidad=0.80,
                        )
        # La muerte sacude el campo tribal local
        local_field = self.tribe_manager.get_local_field(agent.id)
        if local_field is not None:
            local_field.absorb_event("muerte", intensity=0.8)

        # Registrar la muerte en la memoria cultural de la tribu
        tribe_id = self.tribe_manager.get_tribe_id(agent.id)
        arch     = agent.archetypes.dominant()
        arch_norm = "self_" if arch == "self" else arch
        if tribe_id:
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is not None:
                cmem.record_event(
                    dia                 = tp.dia_simulado,
                    agente_nombre       = agent.nombre,
                    arquetipo_dominante = arch_norm,
                    tipo_evento         = causa,
                    descripcion         = (
                        f"{agent.nombre} falleció a causa de {causa} "
                        f"en el día {tp.dia_simulado}."
                    ),
                    intensidad          = 0.85,
                )

        # Registrar la muerte en el GraveHex (con bond medio de los testigos presentes)
        bonds_presentes = [
            self.social_network.get_bond(other.id, agent.id)
            for other in self.agents.values()
            if other.is_alive and other.posicion == agent.posicion
        ]
        bond_medio = (sum(bonds_presentes) / len(bonds_presentes)) if bonds_presentes else 0.15
        self.world_ref.graves.register_death(
            coord         = agent.posicion,
            agente_nombre = agent.nombre,
            arquetipo     = arch_norm,
            dia           = tp.dia_simulado,
            bond_medio    = bond_medio,
        )

        # Sacudir el campo memético de sobrevivientes con vínculo fuerte al fallecido
        # y registrar la muerte en el sistema de percepción de quienes estaban cerca
        for other in self.agents.values():
            if not other.is_alive or other.id == agent.id:
                continue
            bond = self.social_network.get_bond(other.id, agent.id)
            if bond > 0.50:
                lf = self.tribe_manager.get_local_field(other.id)
                if lf is not None:
                    lf.absorb_event("muerte_vinculada", intensity=bond * 0.60)
            other._perception.witness(
                tipo        = "muerte",
                coord       = agent.posicion,
                intensidad  = min(1.0, 0.40 + bond_medio),
                dia         = tp.dia_simulado,
                agent_coord = other.posicion,
            )

    def _check_reproduccion(self, tp: TimePoint) -> None:
        if self.alive_count >= _LIMITE_POBLACION:
            return
        alive = [a for a in self.agents.values() if a.is_alive]
        reproduced: set[str] = set()

        for i, a in enumerate(alive):
            if a.id in reproduced:
                continue
            if a._cooldown_reproduccion > 0:
                continue
            if not (_EDAD_MIN_REPRO <= a.edad <= _EDAD_MAX_REPRO):
                continue
            if a.needs.hambre >= 0.3 or a.needs.sed >= 0.3 or a.needs.fatiga >= 0.5:
                continue

            for b in alive[i + 1:]:
                if b.id in reproduced:
                    continue
                if b._cooldown_reproduccion > 0:
                    continue
                if not (_EDAD_MIN_REPRO <= b.edad <= _EDAD_MAX_REPRO):
                    continue
                if b.needs.hambre >= 0.3 or b.needs.sed >= 0.3 or b.needs.fatiga >= 0.5:
                    continue
                if self.social_network.get_bond(a.id, b.id) < _BOND_REPRODUCCION:
                    continue

                if self._rng.random() < _PROB_REPRO_DIARIA:
                    child = self._generate_offspring(a, b, tp.dia_simulado)
                    self.add_agent(child)
                    self.social_network.set_bond(child.id, a.id, 0.90)
                    self.social_network.set_bond(child.id, b.id, 0.90)
                    self.collective_field.absorb_event("nacimiento", intensity=0.8)
                    # También en el campo tribal de los padres
                    local_field = self.tribe_manager.get_local_field(a.id)
                    if local_field is not None:
                        local_field.absorb_event("nacimiento", intensity=0.8)
                    self._birth_log.append({
                        "dia":      tp.dia_simulado,
                        "id":       child.id,
                        "nombre":   child.nombre,
                        "padre_a":  a.id,
                        "padre_b":  b.id,
                    })
                    print(f"  [👶] Día {tp.dia_simulado}: Nació {child.nombre} "
                          f"(hijo de {a.nombre} y {b.nombre})")

                    # Registrar nacimiento en la memoria cultural de la tribu
                    tribe_id = self.tribe_manager.get_tribe_id(a.id)
                    if tribe_id:
                        cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                        if cmem is not None:
                            arch = child.archetypes.dominant()
                            cmem.record_event(
                                dia                 = tp.dia_simulado,
                                agente_nombre       = child.nombre,
                                arquetipo_dominante = "self_" if arch == "self" else arch,
                                tipo_evento         = "nacimiento",
                                descripcion         = (
                                    f"{child.nombre} nació de {a.nombre} y {b.nombre} "
                                    f"en el día {tp.dia_simulado}."
                                ),
                                intensidad          = 0.50,
                            )

                    # Registrar nacimiento en los sistemas de percepción cercanos
                    for observer in self.agents.values():
                        if not observer.is_alive:
                            continue
                        observer._perception.witness(
                            tipo        = "nacimiento",
                            coord       = child.posicion,
                            intensidad  = 0.45,
                            dia         = tp.dia_simulado,
                            agent_coord = observer.posicion,
                        )

                    reproduced.add(a.id)
                    reproduced.add(b.id)
                    break

    def _generate_offspring(
        self,
        parent_a: Agent,
        parent_b: Agent,
        dia:      int,
    ) -> Agent:
        """Crea un nuevo agente con psicología heredada de ambos padres."""
        hijo_id = f"hijo_{self._proximo_id_hijo:03d}"
        self._proximo_id_hijo += 1

        # Nombre desde el pool, evitando repeticiones
        disponibles = [n for n in _NOMBRES_POOL if n.lower() not in self._nombres_usados]
        if disponibles:
            nombre = disponibles[self._rng.randrange(len(disponibles))]
        else:
            nombre = f"Descendiente_{hijo_id}"
            print(f"  [⚠️] Pool de nombres agotado — usando nombre genérico: {nombre}")
        self._nombres_usados.add(nombre.lower())

        sexo     = self._rng.choice(["M", "F"])
        rol      = self._rng.choice([parent_a.rol, parent_b.rol])
        posicion = parent_a.posicion

        child = Agent(
            agent_id = hijo_id,
            nombre   = nombre,
            posicion = posicion,
            rol      = rol,
            edad     = 0,
            sexo     = sexo,
            seed     = self._proximo_id_hijo,
        )
        child._padres = (parent_a.id, parent_b.id)

        noise = 0.08  # desviación estándar del ruido genético

        # ── Herencia de arquetipos ──────────────────────────────────────────
        for raw_name in ARCHETYPE_NAMES:
            attr = "self_" if raw_name == "self" else raw_name
            val_a = getattr(parent_a.archetypes, attr, 0.4)
            val_b = getattr(parent_b.archetypes, attr, 0.4)
            inherited = (val_a + val_b) / 2.0 + self._rng.gauss(0, noise)
            setattr(child.archetypes, attr, max(0.0, min(1.0, inherited)))

        # ── Herencia de rasgos Big Five + clínico ──────────────────────────
        for attr in TraitProfile().to_dict():
            val_a = getattr(parent_a.traits, attr, 0.5)
            val_b = getattr(parent_b.traits, attr, 0.5)
            inherited = (val_a + val_b) / 2.0 + self._rng.gauss(0, noise)
            setattr(child.traits, attr, max(0.0, min(1.0, inherited)))

        # ── Herencia de complejos (predisposición latente) ─────────────────
        for cn in ["abandono", "inferioridad", "poder", "culpa", "materno", "trascendencia"]:
            pred_a = getattr(parent_a.complexes, cn, 0.3)
            pred_b = getattr(parent_b.complexes, cn, 0.3)
            # El hijo hereda hasta la mitad de la predisposición más alta
            inherited = max(pred_a, pred_b) * 0.5
            setattr(child.complexes, cn, max(0.20, inherited))

        # ── Estado cuántico derivado del arquetipo dominante ───────────────
        from .quantum.superposition import BehavioralState
        child.behavioral_state = BehavioralState.from_archetype_dominant(
            child.archetypes.dominant()
        )
        child._base_state = BehavioralState(
            cooperacion  = child.behavioral_state.cooperacion,
            competencia  = child.behavioral_state.competencia,
            aislamiento  = child.behavioral_state.aislamiento,
            manipulacion = child.behavioral_state.manipulacion,
        )

        # ── Herencia de memoria cultural: ambas tribus si son distintas (Hito 7) ──
        tribe_a = self.tribe_manager.get_tribe_id(parent_a.id)
        tribe_b = self.tribe_manager.get_tribe_id(parent_b.id)
        for tid, weight in ((tribe_a, 0.60), (tribe_b, 0.40)):
            if not tid:
                continue
            cmem = self.tribe_manager.cultural_memories.get(tid)
            if cmem is not None:
                for arch_attr, delta in cmem.get_inheritance_effects().items():
                    current = getattr(child.archetypes, arch_attr, None)
                    if current is not None:
                        setattr(child.archetypes, arch_attr,
                                max(0.0, min(1.0, current + delta * weight)))

        # ── Registro genealógico (Hito 7) ────────────────────────────────────
        tribe_nac = tribe_a or tribe_b or ""
        self.lineage.register(hijo_id, parent_a.id, parent_b.id, dia, tribe_nac)

        # ── Herencia de bonds: el hijo conoce a los amigos de sus padres (Hito 7) ──
        for other_id in list(self.agents):
            if other_id in (parent_a.id, parent_b.id):
                continue
            bond_pa = self.social_network.get_bond(parent_a.id, other_id)
            bond_pb = self.social_network.get_bond(parent_b.id, other_id)
            inherited = max(bond_pa, bond_pb) * 0.30
            if inherited > 0.05:
                self.social_network.set_bond(hijo_id, other_id, inherited)

        # ── Penalización por consanguinidad (Hito 7) ─────────────────────────
        consang = self.lineage.consanguinity_score(parent_a.id, parent_b.id)
        if consang > 0.0:
            extra_noise = consang * 0.12
            for attr in TraitProfile().to_dict():
                current = getattr(child.traits, attr, 0.5)
                penalty = self._rng.gauss(0, extra_noise)
                setattr(child.traits, attr, max(0.0, min(1.0, current + penalty)))
            # Registrar endogamia en percepción de los padres → tabú causal emergente
            for parent in (parent_a, parent_b):
                parent._perception.witness(
                    "endogamia", None, consang, dia, parent.posicion
                )

        # ── Cooldown en los padres ─────────────────────────────────────────
        parent_a._cooldown_reproduccion = _COOLDOWN_REPRO
        parent_b._cooldown_reproduccion = _COOLDOWN_REPRO

        # ── Memoria episódica de nacimiento ───────────────────────────────
        child.episodic_log.append(
            f"Día {dia}: Nació. Padres: {parent_a.nombre} y {parent_b.nombre}."
        )
        parent_a.episodic_log.append(f"Día {dia}: Nació {nombre}.")
        parent_b.episodic_log.append(f"Día {dia}: Nació {nombre}.")

        return child

    def _check_mythic_dead(self, dia: int) -> None:
        """
        Si un registro cultural tiene alta intensidad emocional y muchas transmisiones,
        y su protagonista está muerto, lo inyecta como figura simbólica activa en el ICL
        tribal (el muerto tiene más poder que vivo).
        """
        nombre_a_agente = {a.nombre: a for a in self.agents.values()}
        for tribe_id, cmem in self.tribe_manager.cultural_memories.items():
            local_field = self.tribe_manager.local_fields.get(tribe_id)
            if local_field is None:
                continue
            for rec in cmem.records:
                if rec.intensidad_emocional < 0.70 or rec.n_transmisiones < 5:
                    continue
                agent = nombre_a_agente.get(rec.agente_origen)
                if agent is None or not agent.is_alive:
                    local_field.absorb_event(
                        "figura_mitica",
                        intensity=rec.intensidad_emocional * 0.25,
                    )

    def _process_nightly_dreams(self, dia: int) -> None:
        """
        Genera sueños nocturnos para todos los agentes vivos.

        Antes de generar cada sueño detecta pares entrelazados o con bond fuerte
        para calcular una resonancia_grupal (símbolo compartido). El agente con
        mayor tensión arquetípica "emite" el símbolo; el receptor lo recibe con
        peso máximo en su pool, aumentando la probabilidad de soñar con él.
        """
        terrain    = getattr(self.world_ref, "terrain", None)
        alive_ids  = [aid for aid, a in self.agents.items() if a.is_alive]

        # Calcular resonancias: agent_id → símbolo compartido | None
        resonances: dict[str, str | None] = {aid: None for aid in alive_ids}

        # O(E) en lugar de O(n²): iterar aristas del grafo social
        # La condición same_tribe+bond>0.35 implica que existe arista → no se pierde ningún par
        alive_set = set(alive_ids)
        processed_pairs: set[frozenset] = set()
        for aid_a, aid_b, edge_data in self.social_network.graph.edges(data=True):
            if aid_a not in alive_set or aid_b not in alive_set:
                continue
            pair = frozenset((aid_a, aid_b))
            if pair in processed_pairs:
                continue
            processed_pairs.add(pair)

            edge_b = self.social_network.graph.get_edge_data(aid_b, aid_a, {})
            bond = max(edge_data.get("bond_strength", 0.0), edge_b.get("bond_strength", 0.0))
            entangled = edge_data.get("entangled", False) or edge_b.get("entangled", False)
            same_tribe = (
                self.tribe_manager.agent_to_tribe.get(aid_a) ==
                self.tribe_manager.agent_to_tribe.get(aid_b)
                and self.tribe_manager.agent_to_tribe.get(aid_a) is not None
            )
            qualifies = entangled or bond > 0.65 or (same_tribe and bond > 0.35)
            if not qualifies:
                continue

            a = self.agents[aid_a]
            b = self.agents[aid_b]
            if a.archetypes.fidelidad(b.archetypes) < 0.4 and not entangled:
                continue

            # El de mayor tensión emite; el de menor tensión recibe
            if a.archetypes.tension() >= b.archetypes.tension():
                emitter, receiver_id = a, aid_b
            else:
                emitter, receiver_id = b, aid_a

            arch = emitter.archetypes.dominant()
            pool = _ARCHETYPE_SYMBOLS.get(arch, [_DEFAULT_SYMBOL])
            shared_sym = emitter._rng.choice(pool)

            if resonances[receiver_id] is None:
                resonances[receiver_id] = shared_sym

        # Generar sueños con bioma y resonancia inyectados
        # Resonancia onírica liminal: hexes liminales adyacentes inyectan símbolos
        # ajenos al ICL actual → sueños "inexplicables" (Hito 8)
        liminal_sys = getattr(self.world_ref, "liminal_system", None)

        for aid, agent in self.agents.items():
            if not agent.is_alive:
                continue
            bioma = "tierra"
            if terrain is not None:
                hx = terrain.get(*agent.posicion)
                if hx is not None:
                    bioma = hx.biome
            agent.bioma_actual = bioma

            resonancia = resonances.get(aid)
            # Si el agente duerme adyacente a un hex liminal, puede soñar con un
            # símbolo del pool que no proviene de ningún compañero (fenómeno no trazable)
            if liminal_sys is not None and resonancia is None:
                nearby = liminal_sys.nearby_hexes(agent.posicion, radius=1)
                for lhex in nearby:
                    if lhex.symbol_pool and self._rng.random() < lhex.misterio * 0.35:
                        resonancia = self._rng.choice(lhex.symbol_pool)
                        break

            agent._process_dream(
                dia,
                bioma             = bioma,
                resonancia_grupal = resonancia,
            )

    # ── Hito 4: Error Epistemológico y Percepción Limitada ────────────────────

    def _process_selective_attention(self, dia: int) -> None:
        """
        Atención selectiva arquetípica a eventos climáticos.

        Cada agente "filtra" el evento climático activo a través de su arquetipo
        dominante. Si el tipo de evento coincide con su foco atencional, la intensidad
        percibida se amplifica × 1.5 y se carga el símbolo arquetípico en el ICL tribal.

        El sabio específicamente amplifica fenómenos inexplicables (tormentas, heladas,
        sequías) → carga el símbolo 'sabio' en el campo → condición necesaria para que
        emerja emergentemente un proto-mito escatológico (par muerte+sabio).
        También propaga rumores de los eventos presenciados hacia vecinos sociales cercanos.
        """
        snap = getattr(self.world_ref, "current_snapshot", None)

        evento = snap.evento_climatico if snap is not None else None
        if evento is not None:
            _CLIMA_TO_TIPO: dict[str, str] = {
                "tormenta": "clima_extremo",
                "helada":   "clima_extremo",
                "sequia":   "clima_extremo",
            }
            tipo_percepcion = _CLIMA_TO_TIPO.get(evento, "clima_extremo")
            intensidad_base = max(0.20, snap.survival_risk if snap is not None else 0.20)

            for agent in self.agents.values():
                if not agent.is_alive:
                    continue

                perceived = agent._perception.witness(
                    tipo        = tipo_percepcion,
                    coord       = None,  # evento global: siempre percibido
                    intensidad  = intensidad_base,
                    dia         = dia,
                    agent_coord = agent.posicion,
                )
                arch = agent.archetypes.dominant()
                amplified = agent._perception.perceived_intensity(tipo_percepcion, perceived, arch)

                if amplified > perceived:
                    lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                    lf.symbols[arch] = min(1.0, lf.symbols.get(arch, 0.0) + amplified * 0.05)
                    if arch == "sabio":
                        lf.myth_pressure = min(1.0, lf.myth_pressure + amplified * 0.10)
                        lf.confusion     = min(1.0, lf.confusion     + amplified * 0.08)

        # Eclipse: terror epistemológico puro — confusion + myth_pressure (Hito 5)
        cat_engine = getattr(self.world_ref, "catastrophe", None)
        if cat_engine is not None and cat_engine.active is not None:
            cat = cat_engine.active
            if cat.tipo == "eclipse":
                intensidad_eclipse = 0.50 + cat.severidad * 0.30
                for agent in self.agents.values():
                    if not agent.is_alive:
                        continue
                    perceived = agent._perception.witness(
                        tipo        = "fenomeno_inexplicable",
                        coord       = None,
                        intensidad  = intensidad_eclipse,
                        dia         = dia,
                        agent_coord = agent.posicion,
                    )
                    arch      = agent.archetypes.dominant()
                    amplified = agent._perception.perceived_intensity(
                        "fenomeno_inexplicable", perceived, arch
                    )
                    lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                    lf.confusion     = min(1.0, lf.confusion     + amplified * 0.15)
                    lf.myth_pressure = min(1.0, lf.myth_pressure + amplified * 0.12)
                    if arch == "sabio":
                        lf.symbols["sabio"] = min(
                            1.0, lf.symbols.get("sabio", 0.0) + amplified * 0.10
                        )

        # Propagación de rumores (1 salto por día entre vecinos con vínculo ≥ 0.30)
        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            rumors = agent._perception.generate_rumors()
            if not rumors:
                continue
            neighbors = sorted(
                [
                    (oid, self.social_network.get_bond(agent.id, oid))
                    for oid in self.agents
                    if oid != agent.id and self.agents[oid].is_alive
                ],
                key=lambda x: -x[1],
            )[:3]
            for oid, bond in neighbors:
                if bond < 0.30:
                    break
                for rumor in rumors:
                    self.agents[oid]._perception.receive_rumor(rumor)

    def _process_emotional_contagion(self, dia: int) -> None:
        """
        Contagio emocional: agentes con ansiedad alta (> 0.70) propagan miedo
        a sus vínculos cercanos. La resistencia depende de estabilidad_emocional.
        El miedo acumulado también presiona el campo colectivo tribal.
        """
        for agent in self.agents.values():
            if not agent.is_alive or agent.ansiedad < 0.70:
                continue
            contagion = (agent.ansiedad - 0.50) * 0.10
            for other in self.agents.values():
                if not other.is_alive or other.id == agent.id:
                    continue
                bond = self.social_network.get_bond(other.id, agent.id)
                if bond < 0.40:
                    continue
                resistance    = getattr(other.traits, "estabilidad_emocional", 0.5)
                effective     = contagion * bond * (1.0 - resistance * 0.5)
                other.ansiedad = min(1.0, other.ansiedad + effective)
                lf = self.tribe_manager.get_local_field(agent.id)
                if lf is not None:
                    lf.emotional_pressure = min(
                        1.0, lf.emotional_pressure + effective * 0.10
                    )

    def _check_collective_hysteria(self, dia: int) -> None:
        """
        Histeria colectiva: cuando myth_pressure + confusion + emotional_pressure
        superan simultáneamente sus umbrales en un cluster tribal, se activa histeria.

        La histeria implementa disonancia cognitiva colectiva: la tribu no puede
        reconciliar la realidad con su modelo del mundo → en lugar de abandonar
        sus creencias, añade capas explicativas (absorb_trauma amplificado).
        Esto acelera la cristalización de proto-mitos escatológicos.
        """
        for tribe_id, lf in self.tribe_manager.local_fields.items():
            if lf.myth_pressure > 0.60 and lf.confusion > 0.50 and lf.emotional_pressure > 0.60:
                if not lf.hysteria_active:
                    lf.hysteria_active    = True
                    lf.hysteria_intensity = min(
                        1.0,
                        (lf.myth_pressure + lf.confusion + lf.emotional_pressure) / 3.0,
                    )
                    lf.absorb_trauma("histeria_colectiva", intensity=lf.hysteria_intensity)
                    cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                    if cmem is not None:
                        member_ids = self.tribe_manager.tribes.get(tribe_id, [])
                        primer = next(
                            (self.agents[aid].nombre for aid in member_ids if aid in self.agents
                             and self.agents[aid].is_alive),
                            "desconocido",
                        )
                        cmem.record_event(
                            dia                 = dia,
                            agente_nombre       = primer,
                            arquetipo_dominante = "sombra",
                            tipo_evento         = "histeria_colectiva",
                            descripcion         = (
                                f"La tribu entró en histeria colectiva el día {dia}. "
                                f"Presión: {lf.myth_pressure:.2f}, "
                                f"confusión: {lf.confusion:.2f}."
                            ),
                            intensidad          = 0.90,
                        )
            else:
                if lf.hysteria_active:
                    lf.hysteria_intensity = max(0.0, lf.hysteria_intensity - 0.05)
                    if lf.hysteria_intensity < 0.05:
                        lf.hysteria_active = False

    def _process_causal_bias(self, dia: int) -> None:
        """
        Sesgo de causalidad: dos eventos que co-ocurrieron en la ventana temporal
        forman una asociación causal en la mente del agente → tabú emergente.
        Las asociaciones con fuerza suficiente se registran en la memoria cultural tribal.
        """
        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            nuevas = agent._perception.check_causal_bias(dia)
            if not nuevas:
                continue
            tribe_id = self.tribe_manager.get_tribe_id(agent.id)
            if not tribe_id:
                continue
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is None:
                continue
            arch = agent.archetypes.dominant()
            for assoc in nuevas:
                if assoc.fuerza < 0.40:
                    continue
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = agent.nombre,
                    arquetipo_dominante = "self_" if arch == "self" else arch,
                    tipo_evento         = "taboo_causal",
                    descripcion         = (
                        f"{agent.nombre} asoció '{assoc.precursor}' con "
                        f"'{assoc.outcome}' (fuerza {assoc.fuerza:.2f})."
                    ),
                    intensidad          = assoc.fuerza * 0.60,
                )

    # ── Hito 5: Catástrofes Climáticas Irreversibles ──────────────────────────

    def _process_catastrophe_mortality(self, tp: TimePoint, cat_engine) -> None:
        """
        Mortalidad selectiva durante catástrofes activas.
        Infantes y ancianos tienen mayor riesgo. La plaga genera tabús de contagio.
        """
        cat = cat_engine.active
        if cat is None:
            return
        for agent in list(self.agents.values()):
            if not agent.is_alive:
                continue
            risk = cat_engine.get_survival_risk_mod(
                coord     = agent.posicion,
                edad      = agent.edad,
                is_infant = agent.es_infante,
            )
            if risk <= 0.0 or self._rng.random() >= risk:
                continue
            self._register_death(agent, tp, cat.tipo)
            tribe_id = self.tribe_manager.get_tribe_id(agent.id)
            if tribe_id:
                self._register_tribal_attack(tribe_id, tp.dia_simulado)
            if cat.tipo == "plaga":
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                if tribe_id:
                    cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                    if cmem is not None:
                        cmem.record_event(
                            dia                 = tp.dia_simulado,
                            agente_nombre       = agent.nombre,
                            arquetipo_dominante = "sombra",
                            tipo_evento         = "taboo_causal",
                            descripcion         = (
                                f"{agent.nombre} cayó con plaga el día {tp.dia_simulado}. "
                                f"Tabú: no acercarse a los enfermos."
                            ),
                            intensidad          = 0.80,
                        )

    def _process_catastrophe_anxiety(self, tp: TimePoint, cat_engine) -> None:
        """
        Durante catástrofes, los agentes en el área afectada acumulan ansiedad.
        La ansiedad alta cambia decisiones de acción → migración emergente.
        """
        cat = cat_engine.active
        if cat is None:
            return
        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            # Eclipse afecta a todos globalmente
            if cat.tipo == "eclipse":
                delta = cat.severidad * 0.08
            elif cat.area_hexes is not None and agent.posicion not in cat.area_hexes:
                # Plaga: checar plague_hexes en lugar de area_hexes
                if cat.tipo == "plaga":
                    delta = (cat.severidad * 0.04
                             if agent.posicion in cat_engine._plague_hexes else 0.0)
                else:
                    continue
            else:
                delta = cat.severidad * 0.05
            if delta <= 0.0:
                continue
            agent.ansiedad = min(1.0, agent.ansiedad + delta)
            lf = self.tribe_manager.get_local_field(agent.id)
            if lf is not None:
                lf.confusion = min(1.0, lf.confusion + delta * 0.25)
                # Registro cultural al primer día de catástrofe
                if cat.dias_transcurridos == 1:
                    cmem = self.tribe_manager.cultural_memories.get(
                        self.tribe_manager.get_tribe_id(agent.id) or ""
                    )
                    if cmem is not None:
                        cmem.record_event(
                            dia                 = tp.dia_simulado,
                            agente_nombre       = agent.nombre,
                            arquetipo_dominante = agent.archetypes.dominant(),
                            tipo_evento         = cat.tipo,
                            descripcion         = (
                                f"Catástrofe '{cat.tipo}' comenzó el día {tp.dia_simulado} "
                                f"con severidad {cat.severidad:.2f}."
                            ),
                            intensidad          = cat.severidad,
                        )

    # ── Hito 6: Fauna como Actor Simbólico ───────────────────────────────────

    def _process_symbolic_fauna(self, tp: TimePoint, fauna_sys) -> None:
        """
        Procesa efectos de fauna simbólica sobre agentes y campo colectivo.

        1. Ataques de depredador → muerte registrada + inyección de 'sombra' en ICL.
           Dos kills en 7 días → boost fuerte: ('muerte','sombra') → cosmogonia emergente.
        2. Fauna rara → percepción de fenomeno_inexplicable para agentes cercanos.
        3. Fauna migratoria recurrente (≥2 apariciones) → registro en CulturalMemory
           como proto-calendario.
        4. Carroñeros cerca de tumbas → amplifican carga simbólica del GraveHex.
        """
        terrain = getattr(self.world_ref, "terrain", None)

        # ── 1. Ataques de depredador ───────────────────────────────────────────
        alive_pos = [
            (a.id, a.posicion, self.tribe_manager.get_tribe_id(a.id) or "")
            for a in self.agents.values()
            if a.is_alive and not a.in_liminal
        ]
        attacks = fauna_sys.check_predator_attacks(tp.dia_simulado, alive_pos)
        killed_ids: set[str] = set()
        for atk in attacks:
            agent = self.agents.get(atk["agent_id"])
            if agent is None or not agent.is_alive or agent.id in killed_ids:
                continue
            killed_ids.add(agent.id)
            self._register_death(agent, tp, f"depredador_{atk['fauna_nombre']}")
            self._register_tribal_attack(atk["tribe_id"], tp.dia_simulado)

            # Inyectar 'sombra' en el campo tribal: el predador es la sombra encarnada
            tribe_id = atk["tribe_id"]
            lf = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field
            charge = fauna_sys.symbolic_charge(
                atk["fauna_nombre"], tribe_id,
                biome=terrain.get(*atk["coord"]).biome if terrain else "",
            )
            lf.symbols["sombra"] = min(1.0, lf.symbols.get("sombra", 0.0) + charge * 0.35)
            fauna_sys.register_sighting(tribe_id, atk["fauna_nombre"])

            # Dos kills en 7 días → boost que cataliza crystallización
            if fauna_sys.kills_last_7_days(tribe_id) >= 2:
                lf.myth_pressure  = min(1.0, lf.myth_pressure  + 0.25)
                lf.symbols["muerte"] = min(1.0, lf.symbols.get("muerte", 0.0) + 0.30)
                lf.symbols["heroe"]  = min(1.0, lf.symbols.get("heroe",  0.0) + 0.15)
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is not None:
                    cmem.record_event(
                        dia                 = tp.dia_simulado,
                        agente_nombre       = agent.nombre,
                        arquetipo_dominante = "sombra",
                        tipo_evento         = "depredador_doble_muerte",
                        descripcion         = (
                            f"El {atk['fauna_nombre']} mató dos veces en siete días. "
                            f"La tribu entró en pánico el día {tp.dia_simulado}."
                        ),
                        intensidad          = 0.90,
                    )

        # ── 2. Fauna rara y carroñeros cerca de agentes ───────────────────────
        snap = getattr(self.world_ref, "current_snapshot", None)
        fauna_activa = snap.fauna_simbolica if snap is not None else fauna_sys.active_entities()

        for fauna_info in fauna_activa:
            tipo   = fauna_info.get("tipo", "")
            nombre = fauna_info.get("nombre", "")
            fcoord = tuple(fauna_info.get("coord", [0, 0]))
            biome  = ""
            if terrain is not None:
                hx = terrain.get(*fcoord)
                biome = hx.biome if hx else ""

            # Fauna rara: avistamiento carga fuertemente el ICL de tribus cercanas
            if tipo == "raro":
                for agent in self.agents.values():
                    if not agent.is_alive:
                        continue
                    dist = abs(agent.posicion[0] - fcoord[0]) + abs(agent.posicion[1] - fcoord[1])
                    if dist > 5:
                        continue
                    tribe_id = self.tribe_manager.get_tribe_id(agent.id) or ""
                    charge = fauna_sys.symbolic_charge(nombre, tribe_id, biome)
                    fauna_sys.register_sighting(tribe_id, nombre)

                    perceived = agent._perception.witness(
                        tipo        = "fenomeno_inexplicable",
                        coord       = fcoord,
                        intensidad  = charge,
                        dia         = tp.dia_simulado,
                        agent_coord = agent.posicion,
                    )
                    arch      = agent.archetypes.dominant()
                    amplified = agent._perception.perceived_intensity(
                        "fenomeno_inexplicable", perceived, arch
                    )
                    lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                    lf.myth_pressure = min(1.0, lf.myth_pressure + amplified * 0.15)
                    lf.symbols["sabio"] = min(
                        1.0, lf.symbols.get("sabio", 0.0) + amplified * 0.10
                    )

            # Carroñeros: amplifican carga simbólica de tumbas cercanas
            elif tipo == "carronero":
                graves = getattr(self.world_ref, "graves", None)
                if graves is not None:
                    for gcoord, carga, _ in self.world_ref.graves.active_sites():
                        dist = abs(gcoord[0] - fcoord[0]) + abs(gcoord[1] - fcoord[1])
                        if dist <= 3:
                            graves.boost_at(gcoord, delta=0.02)

        # ── 3. Fauna migratoria recurrente → proto-calendario ─────────────────
        for fauna_info in fauna_activa:
            if fauna_info.get("tipo") != "migratorio":
                continue
            nombre = fauna_info.get("nombre", "")
            if fauna_sys.migration_recurrences(nombre) < 2:
                continue
            # Registrar en memoria cultural de todas las tribus que la han observado
            for tribe_id, obs in fauna_sys._tribe_obs.items():
                if obs.get(nombre, 0) < 1:
                    continue
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is None:
                    continue
                # Solo registrar una vez por estación (evitar spam)
                existing = [r for r in cmem.records
                            if r.tipo_evento == "migracion_recurrente"
                            and nombre in r.descripcion_actual
                            and tp.dia_simulado - r.dia_origen <= 90]
                if existing:
                    continue
                lf = self.tribe_manager.local_fields.get(tribe_id)
                lf_ref = lf or self.collective_field
                lf_ref.symbols["sabio"] = min(
                    1.0, lf_ref.symbols.get("sabio", 0.0) + 0.08
                )
                # Buscar un representante de la tribu para el registro
                primer = next(
                    (self.agents[aid].nombre
                     for aid in self.tribe_manager.tribes.get(tribe_id, [])
                     if aid in self.agents and self.agents[aid].is_alive),
                    "tribu",
                )
                cmem.record_event(
                    dia                 = tp.dia_simulado,
                    agente_nombre       = primer,
                    arquetipo_dominante = "sabio",
                    tipo_evento         = "migracion_recurrente",
                    descripcion         = (
                        f"El {nombre} regresó otra vez. "
                        f"La tribu observó su {fauna_sys.migration_recurrences(nombre)}ª aparición "
                        f"el día {tp.dia_simulado}."
                    ),
                    intensidad          = 0.55,
                )

    # ── Fin Hito 5 ─────────────────────────────────────────────────────────────

    # ── Hito 7: Linajes, Parentesco y Tabú del Incesto ───────────────────────

    def _process_jealousy(self, tp: TimePoint) -> None:
        """
        Celos como motor de conflicto.

        Si A tiene vínculo exclusivo con B (bond ≥ 0.70) y B a su vez tiene
        otro vínculo fuerte con C ≠ A (bond ≥ 0.50), A activa su complejo
        de abandono y lo registra como 'traicion_vinculo' en memoria cultural.
        Inyecta símbolo 'rebelde' en el ICL → mito_moral emergente.
        """
        for agent_a in list(self.agents.values()):
            if not agent_a.is_alive:
                continue
            # Buscar pareja exclusiva B (bond más alto ≥ 0.70)
            top_bonds = sorted(
                [
                    (oid, self.social_network.get_bond(agent_a.id, oid))
                    for oid in self.agents
                    if oid != agent_a.id and self.agents[oid].is_alive
                ],
                key=lambda x: -x[1],
            )
            if not top_bonds or top_bonds[0][1] < 0.70:
                continue
            partner_id, _ = top_bonds[0]
            partner = self.agents.get(partner_id)
            if partner is None:
                continue

            # ¿B tiene un rival C con bond ≥ 0.50?
            rival_bond = max(
                (self.social_network.get_bond(partner_id, oid)
                 for oid in self.agents
                 if oid not in (agent_a.id, partner_id) and self.agents[oid].is_alive),
                default=0.0,
            )
            if rival_bond < 0.50:
                continue

            delta = rival_bond * 0.08
            agent_a.complexes.abandono = min(1.0, agent_a.complexes.abandono + delta)
            agent_a.ansiedad           = min(1.0, agent_a.ansiedad + delta * 0.40)

            if delta < 0.04:
                continue
            tribe_id = self.tribe_manager.get_tribe_id(agent_a.id)
            if tribe_id:
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is not None:
                    recientes = [r for r in cmem.records
                                 if r.tipo_evento == "traicion_vinculo"
                                 and agent_a.nombre in r.descripcion_actual
                                 and tp.dia_simulado - r.dia_origen < 30]
                    if not recientes:
                        cmem.record_event(
                            dia                 = tp.dia_simulado,
                            agente_nombre       = agent_a.nombre,
                            arquetipo_dominante = "rebelde",
                            tipo_evento         = "traicion_vinculo",
                            descripcion         = (
                                f"{agent_a.nombre} sintió traición cuando "
                                f"{partner.nombre} formó nuevo vínculo el día "
                                f"{tp.dia_simulado}."
                            ),
                            intensidad          = min(1.0, delta * 1.2),
                        )
            lf = self.tribe_manager.get_local_field(agent_a.id) or self.collective_field
            lf.symbols["rebelde"] = min(
                1.0, lf.symbols.get("rebelde", 0.0) + delta * 0.30
            )

    # ── Fin Hito 7 ─────────────────────────────────────────────────────────────

    # ── Hito 8: Zonas Liminales Expandidas ───────────────────────────────────

    def _process_liminal_hex_effects(self, tp: TimePoint, liminal_sys) -> None:
        """
        Aplica efectos de hexes liminales sobre agentes y campo colectivo.

        1. Inyección autónoma de símbolos ICL (sin origen en ningún agente → superstición).
        2. Amplificación no lineal de arquetipos dormidos en visitantes cercanos.
        Ambos efectos contribuyen a perfiles arquetípicos más extremos y mayor
        tasa de proto-mitos en visitantes frecuentes (criterio de salida Hito 8).
        """
        terrain = getattr(self.world_ref, "terrain", None)

        # ── 1. Inyecciones autónomas → ICL + percepción ───────────────────────
        for ev in liminal_sys._last_events:
            coord   = ev["coord"]
            symbol  = ev["symbol"]
            misterio = ev["misterio"]
            for agent in self.agents.values():
                if not agent.is_alive:
                    continue
                dist = abs(agent.posicion[0] - coord[0]) + abs(agent.posicion[1] - coord[1])
                if dist > 3:
                    continue
                perceived = agent._perception.witness(
                    tipo        = "fenomeno_inexplicable",
                    coord       = coord,
                    intensidad  = misterio * 0.80,
                    dia         = tp.dia_simulado,
                    agent_coord = agent.posicion,
                )
                if perceived <= 0.0:
                    continue
                lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                lf.symbols[symbol]    = min(1.0, lf.symbols.get(symbol, 0.0) + perceived * 0.12)
                lf.myth_pressure      = min(1.0, lf.myth_pressure + perceived * 0.08)
                lf.confusion          = min(1.0, lf.confusion      + perceived * 0.05)

        # ── 2. Amplificación no lineal de arquetipos ──────────────────────────
        _arq_attrs = [
            "heroe", "sombra", "madre", "padre", "sabio",
            "trickster", "rebelde", "gobernante", "nino_divino",
        ]
        for lhex in liminal_sys.hexes:
            cell = terrain.get(*lhex.coord) if terrain else None
            if cell is None or not cell.explored:
                continue
            for agent in self.agents.values():
                if not agent.is_alive:
                    continue
                dist = abs(agent.posicion[0] - lhex.coord[0]) + abs(agent.posicion[1] - lhex.coord[1])
                if dist > 2:
                    continue
                dominant = agent.archetypes.dominant()
                for arch in _arq_attrs:
                    if arch == dominant:
                        continue  # no amplificamos el dominante; solo los dormidos
                    current = getattr(agent.archetypes, arch, 0.3)
                    noise   = self._rng.gauss(0, lhex.misterio * 0.018)
                    setattr(agent.archetypes, arch, max(0.0, min(1.0, current + noise)))

    # ── Fin Hito 8 ─────────────────────────────────────────────────────────────

    # ── Hito 9: Psicología Oscura ──────────────────────────────────────────────

    def _register_tribal_attack(self, tribe_id: str, dia: int) -> None:
        lst = self._tribal_attacks.setdefault(tribe_id, [])
        lst.append(dia)

    def _paranoia_score(self, tribe_id: str, dia: int, window: int = 30) -> float:
        lst = self._tribal_attacks.get(tribe_id)
        if not lst:
            return 0.0
        cutoff = dia - window
        # Poda in-place: elimina entradas fuera de la ventana para evitar memoria leak
        self._tribal_attacks[tribe_id] = lst = [d for d in lst if d > cutoff]
        return min(1.0, len(lst) / 4.0)  # 4 ataques = paranoia máxima

    def _process_projection(self, dia: int) -> None:
        """
        Proyección/autoengaño: el agente con complejo activo (> 0.60) no lo
        reconoce en sí mismo — lo atribuye al otro (su vínculo más fuerte).
        Reduce levemente ese vínculo y carga el símbolo arquetípico en el ICL
        sin trazabilidad a ninguna acción concreta → superstición oscura.
        """
        _COMPLEX_TO_ARCH: dict[str, tuple] = {
            "abandono":      ("rebelde", "sombra"),
            "inferioridad":  ("sombra",),
            "poder":         ("gobernante", "padre"),
            "culpa":         ("sombra", "sabio"),
            "materno":       ("madre",),
            "trascendencia": ("sabio", "nino_divino"),
        }
        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            for cn, archs in _COMPLEX_TO_ARCH.items():
                val = getattr(agent.complexes, cn, 0.0)
                if val < 0.60:
                    continue
                # Encontrar el vínculo más fuerte
                best_id, best_bond = None, 0.0
                for oid in self.agents:
                    if oid == agent.id or not self.agents[oid].is_alive:
                        continue
                    b = self.social_network.get_bond(agent.id, oid)
                    if b > best_bond:
                        best_bond, best_id = b, oid
                if best_id is None or best_bond < 0.30:
                    continue
                # Distorsión: reduce levemente el vínculo hacia el "espejo"
                old = self.social_network.get_bond(agent.id, best_id)
                self.social_network.set_bond(
                    agent.id, best_id, max(0.0, old - val * 0.02)
                )
                # Inyección arquetípica sin origen trazable
                lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                for arch in archs:
                    lf.symbols[arch] = min(
                        1.0, lf.symbols.get(arch, 0.0) + val * 0.04
                    )

    def _process_attribution_bias(self, dia: int) -> None:
        """
        Sesgo de atribución:
        - Fracaso propio → causa externa → leve aumento de myth_pressure.
        - Fracaso ajeno visible → causa interna del otro → registro en CulturalMemory.
        Combina con sesgo causal → los fracasos propios acumulan tabúes.
        """
        snap = getattr(self.world_ref, "current_snapshot", None)
        if snap is None:
            return
        results = snap.action_results
        if not results:
            return
        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            own = results.get(agent.id)
            if own is not None and not own.success:
                lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                lf.myth_pressure = min(1.0, lf.myth_pressure + 0.03)
                agent._perception.witness(
                    tipo="causa_externa", coord=None,
                    intensidad=0.30, dia=dia, agent_coord=agent.posicion,
                )
            for oid, res in results.items():
                if oid == agent.id or res.success:
                    continue
                other = self.agents.get(oid)
                if other is None or not other.is_alive:
                    continue
                dist = (abs(other.posicion[0] - agent.posicion[0])
                        + abs(other.posicion[1] - agent.posicion[1]))
                if dist > 2:
                    continue
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                if not tribe_id:
                    continue
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is None:
                    continue
                existing = [
                    r for r in cmem.records
                    if r.tipo_evento == "fracaso_ajeno"
                    and oid in r.descripcion_actual
                    and dia - r.dia_origen < 10
                ]
                if not existing and self._rng.random() < 0.15:
                    arch = agent.archetypes.dominant()
                    cmem.record_event(
                        dia=dia,
                        agente_nombre=agent.nombre,
                        arquetipo_dominante="self_" if arch == "self" else arch,
                        tipo_evento="fracaso_ajeno",
                        descripcion=(
                            f"{agent.nombre} observó que {other.nombre} falló "
                            f"y lo atribuyó a su carácter el día {dia}."
                        ),
                        intensidad=0.25,
                    )

    def _process_tribal_paranoia(self, dia: int) -> None:
        """
        Paranoia tribal: tribu con historial de ataques recientes interpreta
        la presencia de agentes foráneos como amenaza — aunque no hagan nada.
        Criterio de salida Hito 9: evento neutro → percepción hostil en 20 días.
        """
        for tribe_id, members in self.tribe_manager.tribes.items():
            paranoia = self._paranoia_score(tribe_id, dia)
            if paranoia < 0.30:
                continue
            lf = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field
            for aid in members:
                agent = self.agents.get(aid)
                if agent is None or not agent.is_alive:
                    continue
                for oid, other in self.agents.items():
                    if not other.is_alive:
                        continue
                    other_tribe = self.tribe_manager.get_tribe_id(oid)
                    if other_tribe == tribe_id or other_tribe is None:
                        continue
                    dist = (abs(other.posicion[0] - agent.posicion[0])
                            + abs(other.posicion[1] - agent.posicion[1]))
                    if dist > 3:
                        continue
                    # Presencia neutra → percibida como amenaza
                    agent._perception.witness(
                        tipo="amenaza", coord=other.posicion,
                        intensidad=paranoia * 0.60,
                        dia=dia, agent_coord=agent.posicion,
                    )
                    lf.symbols["sombra"] = min(
                        1.0, lf.symbols.get("sombra", 0.0) + paranoia * 0.03
                    )

    def _process_cognitive_dissonance(self, dia: int) -> None:
        """
        Disonancia cognitiva: cuando un mito cristalizado coexiste con muertes
        recientes (el mito "predijo" protección que no llegó), la tribu no
        abandona la creencia — añade una capa explicativa (reforma religiosa).
        Esto sube confusion y reduce levemente myth_pressure sin resolverla.
        """
        if not self.mythology_engine.active_myths:
            return
        for tribe_id, lf in self.tribe_manager.local_fields.items():
            if lf.myth_pressure < 0.45:
                continue
            recent_deaths = [
                d for d in self._death_log
                if d.get("dia", 0) >= dia - 10
                and self.tribe_manager.get_tribe_id(d.get("agent_id", "")) == tribe_id
            ]
            if not recent_deaths:
                continue
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is None:
                continue
            existing = [
                r for r in cmem.records
                if r.tipo_evento == "reforma_religiosa"
                and dia - r.dia_origen < 30
            ]
            if existing:
                continue
            # La tribu reencuadra el mito en lugar de abandonarlo
            lf.myth_pressure = max(0.0, lf.myth_pressure - 0.08)
            lf.confusion = min(1.0, lf.confusion + 0.12)
            primer = next(
                (self.agents[aid].nombre
                 for aid in self.tribe_manager.tribes.get(tribe_id, [])
                 if aid in self.agents and self.agents[aid].is_alive),
                "la tribu",
            )
            cmem.record_event(
                dia=dia,
                agente_nombre=primer,
                arquetipo_dominante="sabio",
                tipo_evento="reforma_religiosa",
                descripcion=(
                    f"Pese a los muertos, el mito no falló: "
                    f"el día {dia} la tribu encontró una nueva explicación. "
                    f"La creencia persiste transformada."
                ),
                intensidad=0.65,
            )

    # ── Fin Hito 9 ─────────────────────────────────────────────────────────────

    # ── Hito 10: Tecnología Emergente y Asimetría de Conocimiento ─────────────

    def _check_discovery_condition(self, agent, snap, cond_key: str) -> bool:
        """Evalúa si el agente cumple la condición contextual de descubrimiento."""
        if cond_key == "fuego_activo":
            return snap is not None and snap.fuego_activo
        elif cond_key == "agua_escasa":
            return snap is not None and snap.resource_pressure > 0.50
        elif cond_key == "planta_cercana":
            if snap is None:
                return False
            pos = agent.posicion
            for coord, res in snap.recursos_por_hex.items():
                dist = abs(coord[0] - pos[0]) + abs(coord[1] - pos[1])
                if dist <= 2 and any(r in res for r in ("planta", "fruto", "fungi")):
                    return True
            return False
        elif cond_key == "caza_exitosa":
            if snap is None:
                return False
            res = snap.action_results.get(agent.id)
            return res is not None and res.success and bool(res.resource_gained)
        elif cond_key == "exploracion_amplia":
            return snap is not None and len(snap.recursos_por_hex) > 15
        elif cond_key == "sabio_dominante":
            return agent.archetypes.dominant() == "sabio"
        elif cond_key == "herida":
            return agent.needs.fatiga > 0.70
        return False

    def _process_knowledge_discovery(self, tp) -> None:
        """
        Descubrimiento accidental de conocimiento técnico.

        Cada agente vivo tiene una pequeña probabilidad de descubrir un
        conocimiento si está expuesto a las condiciones contextuales adecuadas.
        El descubrimiento no requiere intención: emerge de la exposición.
        """
        snap = getattr(self.world_ref, "current_snapshot", None)
        dia  = tp.dia_simulado if hasattr(tp, "dia_simulado") else tp

        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            for cond_key, kname, base_prob in _DISCOVERY_TRIGGERS:
                if self.knowledge.has(agent.id, kname):
                    continue
                if not self._check_discovery_condition(agent, snap, cond_key):
                    continue
                if self._rng.random() >= base_prob:
                    continue
                # Descubrimiento accidental
                self.knowledge.give(agent.id, kname)
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                if tribe_id:
                    cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                    if cmem is not None:
                        cmem.record_event(
                            dia=dia,
                            agente_nombre=agent.nombre,
                            arquetipo_dominante="sabio",
                            tipo_evento="descubrimiento_tecnico",
                            descripcion=(
                                f"{agent.nombre} descubrió '{kname}' "
                                f"por accidente el día {dia}."
                            ),
                            intensidad=0.55,
                        )
                    lf = self.tribe_manager.local_fields.get(tribe_id)
                    if lf is not None:
                        lf.symbols["sabio"] = min(
                            1.0, lf.symbols.get("sabio", 0.0) + 0.08
                        )

    def _process_knowledge_transmission(self, tp) -> None:
        """
        Transmisión imperfecta de conocimiento entre agentes co-ubicados.

        Para cada par (maestro, estudiante) con bond ≥ 0.50 en el mismo hex,
        intenta transmitir cada conocimiento que el maestro tenga y el estudiante no.
        La probabilidad diaria es inversamente proporcional a la complejidad.
        """
        dia = tp.dia_simulado if hasattr(tp, "dia_simulado") else tp

        # Agrupar agentes vivos por posición
        by_pos: dict[tuple, list[str]] = {}
        for aid, agent in self.agents.items():
            if agent.is_alive:
                by_pos.setdefault(agent.posicion, []).append(aid)

        for aids in by_pos.values():
            if len(aids) < 2:
                continue
            for i, teacher_id in enumerate(aids):
                teacher_ks = self.knowledge.get(teacher_id)
                if not teacher_ks:
                    continue
                for student_id in aids[i + 1:]:
                    bond = self.social_network.get_bond(teacher_id, student_id)
                    if bond < 0.50:
                        continue
                    for kname in list(teacher_ks):
                        if self.knowledge.has(student_id, kname):
                            continue
                        if self.knowledge.teach(teacher_id, student_id, kname, self._rng):
                            # Registrar transmisión exitosa
                            tribe_id = self.tribe_manager.get_tribe_id(student_id)
                            if tribe_id:
                                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                                if cmem is not None:
                                    recientes = [
                                        r for r in cmem.records
                                        if r.tipo_evento == "transmision_conocimiento"
                                        and kname in r.descripcion_actual
                                        and dia - r.dia_origen < 30
                                    ]
                                    if not recientes:
                                        teacher = self.agents[teacher_id]
                                        student = self.agents[student_id]
                                        cmem.record_event(
                                            dia=dia,
                                            agente_nombre=teacher.nombre,
                                            arquetipo_dominante="sabio",
                                            tipo_evento="transmision_conocimiento",
                                            descripcion=(
                                                f"{teacher.nombre} enseñó '{kname}' "
                                                f"a {student.nombre} el día {dia}."
                                            ),
                                            intensidad=0.45,
                                        )

    def _process_knowledge_power(self, tp) -> None:
        """
        Asimetría de poder por monopolio de conocimiento.

        El agente que es el único portador de ≥ 1 conocimiento valioso (valor > 0.60)
        dentro de su tribu recibe mayor bond_strength entrante: los demás se vuelven
        dependientes. Si alcanza ≥ 2 conocimientos únicos valiosos, emerge como
        especialista sin intervención programada.
        """
        dia = tp.dia_simulado if hasattr(tp, "dia_simulado") else tp

        for tribe_id, members in self.tribe_manager.tribes.items():
            alive = [
                aid for aid in members
                if self.agents.get(aid) and self.agents[aid].is_alive
            ]
            if len(alive) < 2:
                continue
            for aid in alive:
                unique = self.knowledge.unique_carriers_in_tribe(aid, alive)
                valuable_unique = [
                    k for k in unique
                    if _ALL_KNOWLEDGE.get(k, KnowledgeUnit("", "", 0.0, 0.0)).valor > 0.60
                ]
                if not valuable_unique:
                    continue
                # Otros miembros aumentan su vínculo hacia el especialista
                for oid in alive:
                    if oid == aid:
                        continue
                    old = self.social_network.get_bond(oid, aid)
                    self.social_network.set_bond(oid, aid, min(1.0, old + 0.015))
                # Registro de especialista cuando llega a ≥ 2 conocimientos únicos
                if len(valuable_unique) >= 2:
                    cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                    if cmem is not None:
                        existing = [
                            r for r in cmem.records
                            if r.tipo_evento == "especialista_emergente"
                            and aid in r.descripcion_actual
                            and dia - r.dia_origen < 60
                        ]
                        if not existing:
                            agent = self.agents[aid]
                            cmem.record_event(
                                dia=dia,
                                agente_nombre=agent.nombre,
                                arquetipo_dominante="sabio",
                                tipo_evento="especialista_emergente",
                                descripcion=(
                                    f"{agent.nombre} (id={aid}) se convirtió en el único "
                                    f"portador de {len(valuable_unique)} conocimientos "
                                    f"críticos el día {dia}."
                                ),
                                intensidad=0.75,
                            )

    # ── Fin Hito 10 ────────────────────────────────────────────────────────────

    def on_season_change(self, tp: TimePoint) -> None:
        for agent in self.agents.values():
            agent.schedule.adjust_for_season(tp.estacion)

    # ── Snapshots ─────────────────────────────────────────────────────────────

    def snapshot_all(self) -> list[dict]:
        return [a.snapshot() for a in self.agents.values()]

    @property
    def death_log(self) -> list[dict]:
        return self._death_log

    # ── Factory helpers ───────────────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, path: str, world_ref: WorldCore) -> AgentCore:
        """Load agents from a YAML seed file (Phase 5)."""
        import yaml
        core = cls(world_ref)
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for i, entry in enumerate(data.get("agents", [])):
            posicion = tuple(entry.get("posicion", world_ref.terrain.center))
            agent = Agent(
                agent_id = entry.get("id", f"agente_{i}"),
                nombre   = entry.get("nombre", f"Agente {i}"),
                posicion = posicion,
                rol      = entry.get("rol", "generico"),
                edad     = entry.get("edad", 25),
                sexo     = entry.get("sexo", "M"),
                seed     = i,
            )
            agent.load_psyche_from_yaml(entry)
            core.add_agent(agent)
        return core

    @property
    def birth_log(self) -> list[dict]:
        return self._birth_log

    def to_dict(self) -> dict:
        return {
            "agents":            [a.to_dict() for a in self.agents.values()],
            "death_log":         self._death_log,
            "birth_log":         self._birth_log,
            "nombres_usados":    list(self._nombres_usados),
            "proximo_id_hijo":   self._proximo_id_hijo,
            "social_network":    self.social_network.to_dict(),
            "collective_field":  self.collective_field.to_dict(),
            "mythology_engine":  self.mythology_engine.to_dict(),
            "tribe_manager":     self.tribe_manager.to_dict(),
            "culture_engine":    self.culture_engine.to_dict(),
            "lineage":           self.lineage.to_dict(),
            "tribal_attacks":    {tid: list(ds) for tid, ds in self._tribal_attacks.items()},
            "knowledge":         self.knowledge.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict, world_ref: WorldCore) -> AgentCore:
        core = cls(world_ref)
        for adict in data.get("agents", []):
            core.add_agent(Agent.from_dict(adict))
        core._death_log        = data.get("death_log", [])
        core._birth_log        = data.get("birth_log", [])
        core._nombres_usados   = set(data.get("nombres_usados", []))
        core._proximo_id_hijo  = data.get("proximo_id_hijo", 0)

        # Restauración de capas de Sistemas Sociales (Fase 7)
        if "social_network" in data:
            core.social_network = SocialNetwork.from_dict(data["social_network"])
        else:
            for aid in core.agents:
                core.social_network.add_agent(aid)

        if "collective_field" in data:
            core.collective_field = CollectiveField.from_dict(data["collective_field"])

        if "mythology_engine" in data:
            core.mythology_engine = MythologyEngine.from_dict(data["mythology_engine"])

        if "tribe_manager" in data:
            core.tribe_manager = TribeManager.from_dict(data["tribe_manager"])

        if "culture_engine" in data:
            core.culture_engine = CultureEngine.from_dict(data["culture_engine"])

        if "lineage" in data:
            core.lineage = LineageGraph.from_dict(data["lineage"])

        if "tribal_attacks" in data:
            core._tribal_attacks = {
                tid: list(ds) for tid, ds in data["tribal_attacks"].items()
            }

        if "knowledge" in data:
            core.knowledge = KnowledgeSystem.from_dict(data["knowledge"])

        return core

