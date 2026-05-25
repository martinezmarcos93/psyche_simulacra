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
from core.social.mythology import MythologyEngine, DeityRecord, _deity_name, _ARCH_TO_SPHERE
from core.world.sacred_object import SacredObject, _SACRED_OBJECT_PREFIXES
from core.social.social_roles import SocialRole
from core.social.tribe_manager import TribeManager
from core.world.culture_engine import CultureEngine
from core.social.genealogy import LineageGraph
from core.social.knowledge import KnowledgeSystem, KnowledgeUnit, _ALL_KNOWLEDGE, _DISCOVERY_TRIGGERS, ArtifactSystem
from core.social.emergent_lexicon import EmergentLexiconSystem
from core.world.substances import SUBSTANCES
from .psyche.episodic_memory import EpisodicMemory, MemoryRecord
from .psyche.dissociation import DissociativeState, select_tipo, ANSIEDAD_UMBRAL, DIAS_UMBRAL, DIAS_PERMANENCIA
from .psyche.grief import GriefState, duracion_por_bond
from .psyche.ancestral import UnprocessedGrief, _significance

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

# Hito I — Pares arquetípicos con tensión opuesta (Jung, "Tipos psicológicos")
# Hito C — Objetos Sagrados
_SACRED_OBJ_PROB      = 0.002   # prob/día de entrar en estado creativo
_SACRED_OBJ_THRESHOLD = 0.75    # símbolo ICL mínimo para disparar creación
_SACRED_OBJ_COOLDOWN  = 60      # días entre creaciones por agente
_SACRED_OBJ_HEX_BOOST = 0.003   # carga añadida/día al GraveHex que aloja un objeto

# Hito H — Roles Sociales Emergentes
_ROLE_UPDATE_INTERVAL = 30      # días entre detecciones de rol
_ROLE_TRANSITION_MIN  = 15
_ROLE_TRANSITION_MAX  = 30
_ROLE_LEGITIMACY_GAIN = 0.01
_ROLE_LEGITIMACY_LOSS = 0.05
_ROLE_MIN_LEGITIMACY  = 0.20    # umbral de desafío → inicia transición
_ROLE_ELDER_MIN_BOND  = 0.40    # bond medio mínimo para ser reconocido como anciano

# Hito E — Cristalización de Deidades
_DEITY_ICL_THRESHOLD    = 0.65   # símbolo dominante en ICL para iniciar racha
_DEITY_STREAK_DAYS      = 30     # días consecutivos para emergencia por racha
_DEITY_MYTH_REPEAT      = 3      # nº de cristalizaciones del mismo par → deidad
_DEITY_EFFECT_THRESHOLD = 0.55   # alineación arquetípica mínima para sentir efectos

# Ext. B — Proto-Chamanismo
_CHAMAN_MIN_SABIO        = 0.60   # sabio mínimo para ser candidato
_CHAMAN_MIN_CONSULTAS    = 3      # consultas en ventana → emerge rol formal
_CHAMAN_CONSULT_WINDOW   = 90     # días de ventana de consultas
_CHAMAN_CRISIS_PROB      = 0.15   # prob. de que un miembro consulte en crisis
_CHAMAN_HYSTERIA_DAYS    = 30     # días de histeria post-muerte sin sucesor
_CHAMAN_KNOWLEDGE_TIPOS  = frozenset({"ritual", "medicina"})

_INCOMPATIBLE_ARCH_PAIRS: frozenset = frozenset({
    frozenset({"heroe",      "sombra"}),
    frozenset({"gobernante", "rebelde"}),
    frozenset({"sabio",      "trickster"}),
    frozenset({"padre",      "rebelde"}),
    frozenset({"madre",      "sombra"}),
    frozenset({"nino_divino","muerte"}),
})
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
        # R5-B1: artefactos físicos que materializan conocimiento
        self.artifacts = ArtifactSystem()
        # R5-A4: lenguaje emergente — proto-vocabulario tribal
        self.emergent_lexicon = EmergentLexiconSystem()
        # Presencias ancestrales: duelos tribales sin cierre ritual (Hito K)
        self._tribe_unprocessed_griefs: dict[str, list[UnprocessedGrief]] = {}
        # Proto-chamanismo: rol emergente de mediación simbólica (Ext. B)
        self._proto_chamanes: dict[str, str] = {}   # tribe_id → agent_id
        self._chaman_hysteria: dict[str, int] = {}  # tribe_id → días restantes
        # Deidades emergentes del ICL — Hito E
        self._archetype_streak: dict[str, dict[str, int]] = {}  # tribe_id → {arch: días}
        # Objetos sagrados — Hito C
        self._sacred_objects:   list[SacredObject] = []
        self._objeto_cooldown:  dict[str, int]     = {}  # agent_id → días restantes
        # Roles sociales emergentes — Hito H
        self._social_roles:     list[SocialRole]   = []

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
        # R5-C2: myth_pressure_boost de la sustancia se aplica al campo colectivo local.
        for agent in self.agents.values():
            if not agent._psychoactive_consumed:
                continue
            agent._psychoactive_consumed = False
            agent.archetypes.sabio = min(1.0, agent.archetypes.sabio + 0.02)

            # Aplicar myth_pressure_boost de la sustancia activa al campo local
            lf_sub = self.tribe_manager.get_local_field(agent.id) or self.collective_field
            for sname in agent._active_substances:
                defn = SUBSTANCES.get(sname)
                if defn is not None and defn.myth_pressure_boost > 0:
                    amp = 1.5 if agent.in_liminal else 1.0
                    lf_sub.myth_pressure = min(
                        1.0, lf_sub.myth_pressure + defn.myth_pressure_boost * amp * 0.4
                    )
                    # Enteógenos también amplifican sueños compartidos (flag para on_day)
                    if defn.type.value == "enteogeno":
                        agent._enteogen_active = True

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
        # Snapshot pre-recluster para detectar cismas (Hito I)
        _pre_tribes = {tid: set(members) for tid, members in self.tribe_manager.tribes.items()}
        self.tribe_manager.on_day(
            self.agents,
            self.social_network,
            self.collective_field,
            terrain,
            tp.dia_simulado,
        )
        self._detect_schism_events(_pre_tribes, tp.dia_simulado)

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

        # 3i. Capa narrativa de catástrofes — R5-B4
        if cat_engine is not None:
            self._process_catastrophe_narrative(tp, cat_engine)

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

        # 16b. Muerte cultural y colapso civilizatorio — R5-D3
        self._process_cultural_collapse(tp.dia_simulado)

        # 17a. Descubrimiento accidental de conocimiento técnico (Hito 10)
        self._process_knowledge_discovery(tp)

        # 17b. Transmisión de conocimiento entre co-ubicados (Hito 10)
        self._process_knowledge_transmission(tp)

        # 17c. Asimetría de poder: especialistas atraen dependencia (Hito 10)
        self._process_knowledge_power(tp)

        # 17d. Intercambio inter-tribal de conocimiento (R4-Ext.C)
        self._process_intertribal_knowledge_exchange(tp)

        # 17e. Economía simbólica: deuda ritual y prestigio (R5-D2)
        self._process_symbolic_economy(tp.dia_simulado)

        # 17f. Imprinting infantil y desarrollo por fases (R5-A2)
        self._process_infant_imprinting(tp.dia_simulado)

        # 17g. Geografía psicológica — efectos de marcas en hex (R5-B3)
        self._process_psychic_geography(tp.dia_simulado)

        # 17h. Lenguaje emergente — nombramiento de símbolos dominantes (R5-A4)
        self.emergent_lexicon.on_day(
            self.tribe_manager.local_fields,
            self.tribe_manager.cultural_memories,
            tp.dia_simulado,
        )

        # 18. Re-vivencias de memoria episódica — Hito A (Roadmap 4)
        self._process_episodic_revivals(tp.dia_simulado)

        # 19. Disociación por sombra y cascada de estrés — Hito B (Roadmap 4)
        self._process_dissociation(tp.dia_simulado)

        # 19b. Error cognitivo profundo ampliado — R5-D1
        self._process_cognitive_errors(tp.dia_simulado)

        # 20. Duelo diferenciado y ritual funerario emergente — Hito J (Roadmap 4)
        self._process_grief(tp.dia_simulado)

        # 21. Presencia ancestral: duelo no procesado como perturbación del campo — Hito K
        self._process_unprocessed_grief(tp.dia_simulado)

        # 22. Rencores arquetípicos, cismas y cascadas de lealtad — Hito I
        self._process_resentments(tp.dia_simulado)

        # 23. Proto-chamanismo: mediación simbólica emergente — Ext. B
        self._process_proto_chaman(tp.dia_simulado)

        # 24. Cristalización de deidades desde el ICL — Hito E
        self._process_deity_emergence(tp.dia_simulado)

        # 25. Objetos sagrados y creación compulsiva — Hito C
        self._process_sacred_objects(tp.dia_simulado)

        # 26. Roles sociales emergentes — Hito H
        self._process_social_roles(tp.dia_simulado)

        # 27. R5-B2: bonus de refugio nocturno + actualizar coords ocupadas para WorldCore
        self._process_structure_effects(tp.dia_simulado)

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
            if agent.edad >= 50:
                # Muerte de un anciano: carga padre/sabio además del duelo normal
                local_field.absorb_event("muerte_anciano", intensity=0.8)
            else:
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
                # Memoria episódica estructurada: la pérdida de un ser querido
                # persiste como recuerdo de largo plazo con re-vivencias futuras
                other.episodic_memory.record(MemoryRecord(
                    tipo_evento          = "muerte_vinculo",
                    intensidad_emocional = min(1.0, bond * 0.80 + 0.20),
                    dia_origen           = tp.dia_simulado,
                    agente_protagonista  = agent.nombre,
                    arquetipo_dominante  = arch_norm,
                ))
                # Duelo diferenciado: duración proporcional al bond (Hito J)
                grave_tiene_carga = (
                    agent.posicion in self.world_ref.graves.graves
                    and self.world_ref.graves.graves[agent.posicion].carga_simbolica > 0.10
                )
                other.active_griefs.append(GriefState(
                    agente_fallecido = agent.nombre,
                    arquetipo        = arch_norm,
                    bond_al_morir    = bond,
                    dia_inicio       = tp.dia_simulado,
                    duracion_dias    = duracion_por_bond(bond),
                    grave_coord      = agent.posicion,
                    sin_anclaje      = not grave_tiene_carga,
                ))
            other._perception.witness(
                tipo        = "muerte",
                coord       = agent.posicion,
                intensidad  = min(1.0, 0.40 + bond_medio),
                dia         = tp.dia_simulado,
                agent_coord = other.posicion,
            )

        # Hito K: ¿Es una figura de alta significancia? → UnprocessedGrief tribal
        n_conocimientos = len(self.knowledge.get(agent.id))
        sig = _significance(agent.edad, agent.archetypes.sabio, n_conocimientos)
        if sig >= 0.40:
            tribe_id = self.tribe_manager.get_tribe_id(agent.id)
            if tribe_id:
                ug = UnprocessedGrief(
                    nombre_fallecido = agent.nombre,
                    arquetipo        = arch_norm,
                    dia_muerte       = tp.dia_simulado,
                    grave_coord      = agent.posicion,
                    intensidad       = sig,
                    tribe_id         = tribe_id,
                )
                self._tribe_unprocessed_griefs.setdefault(tribe_id, []).append(ug)

        # Ext. B: si el fallecido era proto-chamán, gestionar sucesión/histeria
        if agent.id in self._proto_chamanes.values():
            self._on_chaman_death(agent.id, tp.dia_simulado)

        # Hito C: transferir objetos sagrados del fallecido
        self._transfer_objects_on_death(agent.id, tp.dia_simulado)

        # R5-A2: trauma infantil por muerte de figura de apego
        for child in self.agents.values():
            if (child.is_alive
                    and child.fase_desarrollo == "niñez"
                    and child._figura_apego_id == agent.id):
                child.complexes.abandono = min(1.0, child.complexes.abandono + 0.50)
                child.ansiedad           = min(1.0, child.ansiedad + 0.40)
                child.episodic_memory.record(MemoryRecord(
                    tipo_evento          = "trauma_abandono_infantil",
                    intensidad_emocional = 0.95,
                    dia_origen           = tp.dia_simulado,
                    agente_protagonista  = agent.nombre,
                    arquetipo_dominante  = "sombra",
                ))
                child.episodic_log.append(
                    f"Día {tp.dia_simulado}: Mi figura de apego, {agent.nombre}, falleció."
                )

        # R5-B3: registrar la muerte en la geografía psíquica del hex
        if hasattr(self.world_ref, "psychic_geography"):
            tribe_id = self.tribe_manager.get_tribe_id(agent.id)
            self.world_ref.psychic_geography.register_death(
                coord = agent.posicion,
                dia   = tp.dia_simulado,
                tribu = tribe_id,
            )

    # ── Hito A: Memorias Persistentes y Trauma que Regresa ───────────────────

    def _process_episodic_revivals(self, dia: int) -> None:
        """
        Procesa re-vivencias de memorias de largo plazo para todos los agentes.

        Mecánica:
        - Cada MemoryRecord en largo plazo tiene probabilidad = intensidad × 0.03 de
          re-activarse hoy.
        - Al re-vivir: ansiedad del agente sube = intensidad × 0.60 × (0.90^n_revivencias).
          El impacto se atenúa con cada re-vivencia (Freud: elaboración progresiva).
        - Se re-inyecta "Falleció" en episodic_log para que el DreamEngine genere
          sueños perturbadores esa noche (traumas activos = sueños con símbolos del muerto).
        - El arquetipo del recuerdo se amplifica en el vector arquetípico del agente
          (distorsión: el muerto se vuelve más héroe o más monstruo con cada recuerdo).
        - Traumas activos (intensidad > 0.80) contribuyen diariamente al ICL tribal.
        """
        for agent in self.agents.values():
            if not agent.is_alive or agent.es_infante:
                continue

            # Re-vivencias del día
            revived = agent.episodic_memory.process_revivals(dia, agent._rng)
            for rec in revived:
                impact = rec.revival_impact()
                # Impacto emocional: sube ansiedad
                agent.ansiedad = min(1.0, agent.ansiedad + impact * 0.35)
                # El arquetipo del recuerdo se amplifica (distorsión progresiva)
                attr = rec.arquetipo_dominante
                if hasattr(agent.archetypes, attr):
                    current = getattr(agent.archetypes, attr)
                    setattr(agent.archetypes, attr, min(1.0, current + 0.015))
                # Re-inyección en log para DreamEngine (sueños perturbadores esa noche)
                if rec.tipo_evento == "muerte_vinculo" and impact > 0.10:
                    agent.episodic_log.append(
                        f"Día {dia}: Revivió el recuerdo de Falleció {rec.agente_protagonista}."
                    )
                # Contribución al ICL tribal (el duelo no procesado carga el campo)
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                lf = (
                    self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
                ) or self.collective_field
                lf.emotional_pressure = min(1.0, lf.emotional_pressure + 0.015)
                if attr in lf.symbols:
                    lf.symbols[attr] = min(1.0, lf.symbols[attr] + 0.010)

            # Traumas activos (intensidad > 0.80): contribución diaria al ICL
            # Carga el símbolo del muerto + myth_pressure sin que haya un evento nuevo
            for trauma in agent.episodic_memory.active_traumas():
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                lf = (
                    self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
                ) or self.collective_field
                lf.myth_pressure = min(1.0, lf.myth_pressure + 0.005)
                attr = trauma.arquetipo_dominante
                if attr in lf.symbols:
                    lf.symbols[attr] = min(1.0, lf.symbols[attr] + 0.003)

    # ── Hito K: Presencia Ancestral ───────────────────────────────────────────

    def _process_unprocessed_grief(self, dia: int) -> None:
        """
        Procesa las presencias ancestrales activas en cada tribu.

        Mientras el duelo no esté procesado:
        - El arquetipo del fallecido se recarga en el ICL sin fuente trazable.
        - Agentes en el GraveHex experimentan presión simbólica (ansiedad).
        - La tribu puede sobrevisitar o evitar compulsivamente el lugar.

        Una vez convertido (integración exitosa):
        - El arquetipo del fallecido carga como protección en lugar de perturbación.
        - Los agentes en el GraveHex reciben atenuación de ansiedad.

        Un agente con sabio > 0.55 puede intentar el ritual de cierre (prob = sabio × 0.35).
        """
        for tribe_id, ugs in list(self._tribe_unprocessed_griefs.items()):
            # Limpiar entradas resueltas
            ugs[:] = [ug for ug in ugs if not ug.resuelto]
            if not ugs:
                continue

            lf = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field
            tribe_agents = [
                a for a in self.agents.values()
                if a.is_alive and not a.es_infante
                and self.tribe_manager.get_tribe_id(a.id) == tribe_id
            ]

            for ug in ugs:
                ug.dias_activo += 1

                if ug.convertido:
                    # Presencia protectora: beneficia al campo
                    lf.emotional_pressure = max(0.0, lf.emotional_pressure - 0.005)
                    if ug.arquetipo in lf.symbols:
                        lf.symbols[ug.arquetipo] = min(
                            1.0, lf.symbols[ug.arquetipo] + 0.004 * ug.intensidad
                        )
                    # Agentes en el GraveHex: leve calma
                    if ug.grave_coord:
                        for a in tribe_agents:
                            if a.posicion == ug.grave_coord:
                                a.ansiedad = max(0.0, a.ansiedad - 0.03)
                else:
                    # Presencia perturbadora: carga el campo diariamente
                    lf.myth_pressure = min(1.0, lf.myth_pressure + 0.006 * ug.intensidad)
                    if ug.arquetipo in lf.symbols:
                        lf.symbols[ug.arquetipo] = min(
                            1.0, lf.symbols[ug.arquetipo] + 0.006 * ug.intensidad
                        )
                    lf.confusion = min(1.0, lf.confusion + 0.003 * ug.intensidad)

                    # Agentes en el GraveHex: ansiedad + posible compulsión de visita
                    if ug.grave_coord:
                        for a in tribe_agents:
                            if a.posicion == ug.grave_coord:
                                a.ansiedad = min(1.0, a.ansiedad + 0.04 * ug.intensidad)

                    # Intento de integración por agente con sabio alto
                    self._try_ancestral_integration(ug, tribe_agents, dia)

                # Efecto transgeneracional: se aplica al nacer (ver _create_child)

    def _try_ancestral_integration(
        self,
        ug:           UnprocessedGrief,
        tribe_agents: list,
        dia:          int,
    ) -> None:
        """
        Un agente con sabio > 0.55 intenta el ritual de integración colectiva.
        Probabilidad = sabio × 0.35 (Roadmap 4, Hito K).
        Éxito → presencia perturbadora se convierte en ancestral protectora.
        """
        for agent in tribe_agents:
            if agent.archetypes.sabio < 0.55:
                continue
            if self._rng.random() >= 0.05:  # solo intenta el 5% de los días por agente
                continue

            # Chamán tribal: probabilidad × 1.5 (acceso privilegiado al ICL)
            is_chaman = self._proto_chamanes.get(ug.tribe_id) == agent.id
            prob_exito = agent.archetypes.sabio * (0.50 if is_chaman else 0.35)
            if agent._rng.random() < prob_exito:
                ug.convertido = True
                agent.episodic_log.append(
                    f"Día {dia}: Realizó ritual de integración para {ug.nombre_fallecido}. "
                    f"La presencia se volvió protectora."
                )
                # El agente gana sabio y la tribu gana cohesión
                agent.archetypes.sabio = min(1.0, agent.archetypes.sabio + 0.03)
                lf = (
                    self.tribe_manager.local_fields.get(ug.tribe_id)
                    or self.collective_field
                )
                lf.emotional_pressure = max(0.0, lf.emotional_pressure - 0.10)

                cmem = self.tribe_manager.cultural_memories.get(ug.tribe_id)
                if cmem is not None:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = agent.nombre,
                        arquetipo_dominante = "sabio",
                        tipo_evento         = "integracion_ancestral",
                        descripcion         = (
                            f"{agent.nombre} integró la presencia de {ug.nombre_fallecido} "
                            f"el día {dia}. La memoria se tornó protectora."
                        ),
                        intensidad          = 0.90,
                    )
                break  # un solo ritual por presencia por día

    # ── Hito J: Duelo Diferenciado y Ritual Funerario Emergente ──────────────

    def _process_grief(self, dia: int) -> None:
        """
        Ciclo diario del sistema de duelo:
        1. Aplica efectos diarios de cada GriefState activo.
        2. Detecta rituales espontáneos (≥ 2 dolientes en el GraveHex en ≤ 5 días).
        3. Resuelve duelos expirados: sin ritual → amplifica revivals; con ritual → proto-mito.
        4. Injección de sueños perturbadores para muertes sin anclaje.
        """
        from collections import defaultdict

        # ── 1. Efectos diarios y detección de rituales ───────────────────────
        # Agrupar agentes dolientes por (coord, nombre_fallecido) para detectar ritual
        ritual_candidates: dict = defaultdict(list)

        for agent in self.agents.values():
            if not agent.is_alive or not agent.active_griefs:
                continue

            expired: list[GriefState] = []
            for gs in agent.active_griefs:
                gs.dias_activo += 1

                # Efectos diarios: ansiedad según intensidad del bond
                agent.ansiedad = min(1.0, agent.ansiedad + gs.ansiedad_delta())

                # Sueños perturbadores: re-inyectar keyword en log periódicamente
                if gs.dias_activo % 7 == 0:
                    agent.episodic_log.append(
                        f"Día {dia}: Revivió el recuerdo de Falleció {gs.agente_fallecido}."
                    )

                # Muertes sin anclaje: sueños perturbadores más frecuentes (× 2)
                if gs.sin_anclaje and gs.dias_activo % 3 == 0 and gs.dias_activo <= 30:
                    agent.episodic_log.append(
                        f"Día {dia}: Presencia inquietante — {gs.agente_fallecido} "
                        f"no tiene lugar de descanso."
                    )

                # Candidato a ritual: agente en el GraveHex dentro de ventana de 5 días
                if (not gs.ritual_realizado
                        and gs.grave_coord is not None
                        and agent.posicion == gs.grave_coord
                        and dia - gs.dia_inicio <= 5):
                    ritual_candidates[(gs.grave_coord, gs.agente_fallecido)].append(
                        (agent, gs)
                    )

                if gs.is_expired():
                    expired.append(gs)

            # Eliminar duelos expirados y aplicar consecuencias
            for gs in expired:
                agent.active_griefs.remove(gs)
                self._resolve_grief(agent, gs, dia)

        # ── 2. Rituales espontáneos ───────────────────────────────────────────
        for (coord, nombre_fallecido), participants in ritual_candidates.items():
            if len(participants) >= 2:
                self._perform_funeral_ritual(coord, nombre_fallecido, participants, dia)

    def _resolve_grief(self, agent, gs: GriefState, dia: int) -> None:
        """
        Cierre de un duelo expirado.
        Sin ritual: amplifica la intensidad de la memoria asociada (revivals × 1.5).
        Con ritual: la memoria se integra y pierde fuerza perturbadora.
        """
        if gs.ritual_realizado:
            # Duelo bien procesado: suavizar el recuerdo de largo plazo
            for rec in agent.episodic_memory.all_long_term():
                if rec.agente_protagonista == gs.agente_fallecido:
                    rec.intensidad_emocional = max(0.10, rec.intensidad_emocional * 0.70)
        else:
            # Sin ritual: el recuerdo vuelve con más fuerza
            for rec in agent.episodic_memory.all_long_term():
                if rec.agente_protagonista == gs.agente_fallecido:
                    rec.intensidad_emocional = min(0.95, rec.intensidad_emocional * 1.50)
            # Añadir ansiedad residual al ICL
            tribe_id = self.tribe_manager.get_tribe_id(agent.id)
            lf = (
                self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
            ) or self.collective_field
            lf.myth_pressure = min(1.0, lf.myth_pressure + 0.04)

    def _perform_funeral_ritual(
        self,
        coord:             tuple[int, int],
        nombre_fallecido:  str,
        participants:      list,
        dia:               int,
    ) -> None:
        """
        Ritual funerario emergente: ≥ 2 dolientes se reúnen en el GraveHex.
        - Reduce duración del duelo × 0.50 para todos los participantes.
        - Registra ceremonia en el GraveHex (→ lugar sagrado tras ≥ 5).
        - Genera myth_pressure y carga simbólica (proto-mito emergente).
        - Registra en CulturalMemory tribal.
        """
        # Marcar ritual realizado y reducir duración restante
        tribe_ids_participantes: set[str] = set()
        nombres: list[str] = []
        for agent, gs in participants:
            if gs.ritual_realizado:
                continue
            gs.ritual_realizado = True
            # Reducir duración restante al 50%
            restante = gs.duracion_dias - gs.dias_activo
            gs.duracion_dias = gs.dias_activo + max(1, restante // 2)
            nombres.append(agent.nombre)
            tid = self.tribe_manager.get_tribe_id(agent.id)
            if tid:
                tribe_ids_participantes.add(tid)

        if not nombres:
            return

        # Hito K: si existe un UnprocessedGrief para este fallecido y
        # el ritual ocurre dentro de 5 días → cancelarlo (muerte procesada)
        for tribe_id in tribe_ids_participantes:
            ugs = self._tribe_unprocessed_griefs.get(tribe_id, [])
            for ug in ugs:
                if (ug.nombre_fallecido == nombre_fallecido
                        and not ug.resuelto
                        and dia - ug.dia_muerte <= 5):
                    ug.resuelto = True

        # Registrar ceremonia en GraveHex
        grave = self.world_ref.graves.graves.get(coord)
        if grave is not None:
            grave.register_ceremony()
            sacred = grave.is_sacred_place
        else:
            sacred = False

        # Boost al ICL tribal: muerte procesada colectivamente → myth_pressure
        for tribe_id in tribe_ids_participantes:
            lf = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field
            # Ritual activa par (muerte, heroe) → condición para cosmogonía o mito moral
            lf.myth_pressure      = min(1.0, lf.myth_pressure      + 0.20)
            lf.emotional_pressure = max(0.0, lf.emotional_pressure  - 0.10)
            # Lugar sagrado: efectos × 2
            multiplier = 2.0 if sacred else 1.0
            lf.symbols["muerte"] = min(1.0, lf.symbols["muerte"] + 0.12 * multiplier)
            lf.symbols["sabio"]  = min(1.0, lf.symbols["sabio"]  + 0.08 * multiplier)

            # Memoria cultural tribal
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is not None:
                desc_sacred = " En lugar sagrado." if sacred else ""
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = nombre_fallecido,
                    arquetipo_dominante = "sabio",
                    tipo_evento         = "ritual_funerario",
                    descripcion         = (
                        f"Ritual por {nombre_fallecido} en el día {dia}. "
                        f"Participantes: {', '.join(nombres[:4])}.{desc_sacred}"
                    ),
                    intensidad          = 0.80,
                )

    # ── Hito B: Cascada de Estrés y Estados de Disociación por Sombra ────────

    def _process_dissociation(self, dia: int) -> None:
        """
        Gestiona el ciclo completo de disociación por sombra.

        Por cada agente vivo:
        1. Acumula días con ansiedad alta; dispara entrada en disociación.
        2. Incrementa días activos; aplica efectos por tipo.
        3. Comprueba resolución natural (ansiedad < 0.50, no permanente).
        4. Intenta intervención de integración de sombra (agente con sabio alto).
        5. Marca permanente tras DIAS_PERMANENCIA sin intervención.
        """
        for agent in self.agents.values():
            if not agent.is_alive or agent.es_infante:
                continue

            ds = agent.dissociation_state

            # ── Conteo de días de ansiedad alta ───────────────────────────────
            if agent.ansiedad >= ANSIEDAD_UMBRAL:
                if ds is None:
                    agent._dias_ansiedad_alta += 1
            else:
                if ds is None:
                    agent._dias_ansiedad_alta = 0

            # ── Entrada en disociación ────────────────────────────────────────
            if ds is None and agent._dias_ansiedad_alta >= DIAS_UMBRAL:
                self._trigger_dissociation(agent, dia)
                continue  # efectos se aplican el próximo día

            if ds is None:
                continue

            ds.dias_activo += 1

            # ── Resolución natural (sólo si no es permanente) ─────────────────
            if not ds.permanente and agent.ansiedad < 0.50:
                agent.dissociation_state  = None
                agent._dias_ansiedad_alta = 0
                agent.episodic_log.append(
                    f"Día {dia}: El estado de disociación ({ds.tipo}) se disolvió."
                )
                continue

            # ── Efectos por tipo ──────────────────────────────────────────────
            if ds.tipo == "amok":
                self._process_amok(agent, dia)
            elif ds.tipo == "melancolia_disociativa":
                # La ansiedad se mantiene alta: el estado se retroalimenta
                agent.ansiedad = max(agent.ansiedad, ANSIEDAD_UMBRAL - 0.05)
            elif ds.tipo == "fuga_disociativa":
                # Desestabiliza el ICL tribal silenciosamente
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                lf = (
                    self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
                ) or self.collective_field
                lf.emotional_pressure = min(1.0, lf.emotional_pressure + 0.008)
            # estupor: decide_action() ya retorna None; sin efectos adicionales aquí

            # ── Intento de integración de sombra (antes de permanencia) ───────
            if not ds.permanente and not ds.intervencion_recibida:
                self._try_shadow_integration(agent, dia)

            # ── Permanencia ───────────────────────────────────────────────────
            if (not ds.permanente
                    and not ds.intervencion_recibida
                    and ds.dias_activo >= DIAS_PERMANENCIA):
                ds.permanente = True
                agent.episodic_log.append(
                    f"Día {dia}: El estado de disociación ({ds.tipo}) se volvió permanente."
                )
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                lf = (
                    self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
                ) or self.collective_field
                lf.absorb_trauma("histeria_colectiva", intensity=0.55)

    def _trigger_dissociation(self, agent, dia: int) -> None:
        """Entra en disociación: selecciona tipo, propaga cascada, registra en ICL."""
        arch     = agent.archetypes.dominant()
        arch_norm = "self_" if arch == "self" else arch
        tipo     = select_tipo(arch_norm, agent._rng)

        agent.dissociation_state  = DissociativeState(tipo=tipo, dia_inicio=dia)
        agent._dias_ansiedad_alta = 0
        agent.ansiedad            = min(1.0, agent.ansiedad + 0.05)

        agent.episodic_log.append(f"Día {dia}: Entró en disociación por sombra — {tipo}.")
        agent.episodic_memory.record(MemoryRecord(
            tipo_evento          = "disociacion_sombra",
            intensidad_emocional = min(1.0, agent.ansiedad),
            dia_origen           = dia,
            agente_protagonista  = agent.nombre,
            arquetipo_dominante  = "sombra",
        ))

        # Cascada: agentes con bond fuerte reciben impacto de ansiedad
        for other in self.agents.values():
            if not other.is_alive or other.id == agent.id:
                continue
            bond = self.social_network.get_bond(other.id, agent.id)
            if bond > 0.50:
                other.ansiedad = min(1.0, other.ansiedad + bond * 0.22)

        # ICL tribal
        tribe_id = self.tribe_manager.get_tribe_id(agent.id)
        lf = (
            self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
        ) or self.collective_field
        lf.absorb_trauma("histeria_colectiva", intensity=0.45)

        # Memoria cultural tribal
        if tribe_id:
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is not None:
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = agent.nombre,
                    arquetipo_dominante = "sombra",
                    tipo_evento         = "disociacion_sombra",
                    descripcion         = (
                        f"{agent.nombre} cayó en {tipo} el día {dia}."
                    ),
                    intensidad          = 0.85,
                )

    def _process_amok(self, agent, dia: int) -> None:
        """
        Amok: cada 3 días el agente ataca al miembro con mayor bond.
        La violencia se dirige a los más cercanos — el ser querido como víctima.
        """
        ds = agent.dissociation_state
        if ds is None or ds.dias_activo % 3 != 0:
            return

        # Target: el agente vivo con mayor bond entrante desde el atacante
        best_target = None
        best_bond   = 0.0
        for other in self.agents.values():
            if not other.is_alive or other.id == agent.id:
                continue
            bond = self.social_network.get_bond(agent.id, other.id)
            if bond > best_bond:
                best_bond   = bond
                best_target = other

        if best_target is None or best_bond < 0.25:
            return

        # Erosión de bond bidireccional
        self.social_network.set_bond(
            agent.id, best_target.id,
            max(0.0, best_bond - 0.35),
        )
        self.social_network.set_bond(
            best_target.id, agent.id,
            max(0.0, self.social_network.get_bond(best_target.id, agent.id) - 0.25),
        )
        best_target.ansiedad = min(1.0, best_target.ansiedad + 0.22)

        agent.episodic_log.append(
            f"Día {dia}: En amok, atacó a {best_target.nombre}."
        )
        best_target.episodic_log.append(
            f"Día {dia}: choque_violento — fue atacado por {agent.nombre} en amok."
        )

        # Carga sombra en el ICL (choque violento)
        tribe_id = self.tribe_manager.get_tribe_id(agent.id)
        lf = (
            self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
        ) or self.collective_field
        lf.absorb_interaction("sombra", "sombra", "choque_violento")

        # ── Cascada de lealtad ─────────────────────────────────────────────
        # Los aliados de la víctima (bond > 0.50) sufren un impacto: pierden
        # bond con el atacante, ganan ansiedad y acumulan rencor arquetípico.
        for witness in self.agents.values():
            if not witness.is_alive or witness.id in (agent.id, best_target.id):
                continue
            bond_to_victim = self.social_network.get_bond(witness.id, best_target.id)
            if bond_to_victim < 0.50:
                continue
            # Erosión del bond witness → atacante
            bond_to_attacker = self.social_network.get_bond(witness.id, agent.id)
            self.social_network.set_bond(
                witness.id, agent.id,
                max(0.0, bond_to_attacker - bond_to_victim * 0.20),
            )
            # Ansiedad secundaria proporcional a la cercanía con la víctima
            witness.ansiedad = min(1.0, witness.ansiedad + bond_to_victim * 0.12)
            # Rencor acumulado hacia el atacante
            witness.resentments[agent.id] = min(
                1.0, witness.resentments.get(agent.id, 0.0) + bond_to_victim * 0.25
            )
            witness.episodic_log.append(
                f"Día {dia}: Testigo del ataque de {agent.nombre} "
                f"a {best_target.nombre}. Lealtad perturbada."
            )

    def _try_shadow_integration(self, agent, dia: int) -> None:
        """
        Un agente con sabio alto intenta integrar la sombra del disociado.
        Probabilidad de éxito = sabio × 0.40 (Roadmap 4, Hito B).
        Si falla, el interventor recibe impacto de ansiedad.
        Solo un intento por día.
        """
        for other in self.agents.values():
            if not other.is_alive or other.id == agent.id or other.es_infante:
                continue
            bond = self.social_network.get_bond(other.id, agent.id)
            if bond < 0.35 or other.archetypes.sabio < 0.45:
                continue

            # Chamán tribal: prob × 1.5 (mediación simbólica privilegiada — Ext. B)
            tribe_id   = self.tribe_manager.get_tribe_id(other.id)
            is_chaman  = tribe_id and self._proto_chamanes.get(tribe_id) == other.id
            prob_exito = other.archetypes.sabio * (0.60 if is_chaman else 0.40)
            if agent._rng.random() < prob_exito:
                # Éxito
                agent.dissociation_state.intervencion_recibida = True
                agent.dissociation_state  = None
                agent._dias_ansiedad_alta = 0
                agent.ansiedad            = max(0.30, agent.ansiedad - 0.40)
                agent.episodic_log.append(
                    f"Día {dia}: {other.nombre} integró su sombra."
                )
                # El interventor gana bond y charge sabio
                self.social_network.set_bond(
                    other.id, agent.id, min(1.0, bond + 0.10)
                )
                other.archetypes.sabio = min(1.0, other.archetypes.sabio + 0.02)
            else:
                # Fallo: el interventor absorbe parte de la sombra
                residual = (1.0 - other.archetypes.sabio) * 0.25
                other.ansiedad = min(1.0, other.ansiedad + residual)
            break  # un solo intento por día

    # ── R5-D1: Error Cognitivo Profundo Ampliado ──────────────────────────────

    def _process_cognitive_errors(self, dia: int) -> None:
        """
        Tres mecánicas de error cognitivo emergente:

        1. Superstición causal: agente con ansiedad alta + evento reciente
           atribuye causas falsas → mito-presión + tabú spatial.
        2. Sesgo de confirmación: agente con mito activo + confusión alta
           suprime evidencia contradictoria → confusion se autoamplifica.
        3. Contagio cognitivo: agente disociado en hex compartido → vecinos
           absorben mayor ansiedad si tienen bond > 0.30.
        """
        _SUPERST_ANSIEDAD_MIN  = 0.65
        _SUPERST_PROB          = 0.04
        _CONFIRM_CONFUSION_MIN = 0.55
        _CONFIRM_PROB          = 0.06
        _CONTAGIO_BOND_MIN     = 0.30
        _CONTAGIO_DELTA        = 0.025

        by_pos: dict[tuple, list] = {}
        for ag in self.agents.values():
            if ag.is_alive and not ag.es_infante:
                by_pos.setdefault(ag.posicion, []).append(ag)

        for agent in self.agents.values():
            if not agent.is_alive or agent.es_infante:
                continue

            lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field

            # 1. Superstición causal
            if (agent.ansiedad >= _SUPERST_ANSIEDAD_MIN
                    and self._rng.random() < _SUPERST_PROB):
                lf.myth_pressure = min(1.0, lf.myth_pressure + 0.025)
                lf.confusion     = min(1.0, lf.confusion     + 0.015)
                # Tabú espacial emergente: el hex actual se vuelve "sospechoso"
                if hasattr(self.world_ref, "psychic_geography"):
                    self.world_ref.psychic_geography.boost(
                        agent.posicion, "zona_traumatica", 0.04
                    )

            # 2. Sesgo de confirmación (mito activo + confusión alta)
            if (lf.confusion >= _CONFIRM_CONFUSION_MIN
                    and len(self.mythology_engine.active_myths) > 0
                    and self._rng.random() < _CONFIRM_PROB):
                lf.confusion = min(1.0, lf.confusion + 0.020)
                agent.ansiedad = max(0.0, agent.ansiedad - 0.010)

        # 3. Contagio cognitivo de agentes disociados
        for pos, group in by_pos.items():
            disociados = [a for a in group if a.dissociation_state is not None]
            if not disociados:
                continue
            for ag_sano in group:
                if ag_sano.dissociation_state is not None:
                    continue
                for dis in disociados:
                    bond = self.social_network.get_bond(ag_sano.id, dis.id)
                    if bond >= _CONTAGIO_BOND_MIN:
                        ag_sano.ansiedad = min(1.0, ag_sano.ansiedad + _CONTAGIO_DELTA * bond)
                        break  # un solo contagio por día por agente

    # ── Hito I: Rencores, Cismas y Cascadas de Lealtad ───────────────────────

    def _process_resentments(self, dia: int) -> None:
        """
        Diariamente:
        1. Pares de arquetipos incompatibles en el mismo hex acumulan rencor.
        2. Rencores activos erosionan bonds lentamente.
        3. Co-presencia con rencor > 0.30 eleva ansiedad.
        4. Si el rencor tribal alcanza umbral de pre-cisma o cisma, se registra
           en la CulturalMemory de la tribu.
        """
        _RENCOR_ACUM_DAILY   = 0.015   # acumulación por co-presencia con par incompatible
        _RENCOR_BOND_EROSION = 0.004   # erosión de bond por rencor activo
        _RENCOR_ANSIE_DELTA  = 0.008   # ansiedad extra por co-presencia tensa
        _PRE_CISMA_THRESH    = 0.55    # rencor medio tribal → pre-cisma
        _CISMA_THRESH        = 0.75    # rencor medio tribal → cisma inminente

        # Agrupar agentes vivos por hex
        hex_groups: dict[tuple, list] = {}
        for agent in self.agents.values():
            if not agent.is_alive or agent.es_infante:
                continue
            hex_groups.setdefault(agent.posicion, []).append(agent)

        # 1 + 2 + 3: interacciones dentro del mismo hex
        for agents_here in hex_groups.values():
            for i, a in enumerate(agents_here):
                for b in agents_here[i + 1:]:
                    pair = frozenset({a.archetypes.dominant(), b.archetypes.dominant()})
                    if pair not in _INCOMPATIBLE_ARCH_PAIRS:
                        continue

                    # Acumular rencor (bidireccionalmente)
                    a.resentments[b.id] = min(
                        1.0, a.resentments.get(b.id, 0.0) + _RENCOR_ACUM_DAILY
                    )
                    b.resentments[a.id] = min(
                        1.0, b.resentments.get(a.id, 0.0) + _RENCOR_ACUM_DAILY
                    )

                    # Ansiedad por co-presencia tensa
                    rencor_ab = (a.resentments[b.id] + b.resentments[a.id]) / 2.0
                    if rencor_ab > 0.30:
                        a.ansiedad = min(1.0, a.ansiedad + _RENCOR_ANSIE_DELTA)
                        b.ansiedad = min(1.0, b.ansiedad + _RENCOR_ANSIE_DELTA)

        # 2: erosión de bonds por rencores (no requiere co-presencia)
        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            for other_id, rencor in list(agent.resentments.items()):
                if rencor < 0.10:
                    continue
                current_bond = self.social_network.get_bond(agent.id, other_id)
                if current_bond > 0.0:
                    self.social_network.set_bond(
                        agent.id, other_id,
                        max(0.0, current_bond - rencor * _RENCOR_BOND_EROSION),
                    )

        # 4: alerta de pre-cisma / cisma por tribu
        for tribe_id, members in self.tribe_manager.tribes.items():
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is None or len(members) < 3:
                continue

            member_list = [
                self.agents[mid] for mid in members if mid in self.agents
            ]
            # Rencor medio de todos los pares intra-tribu
            total_rencor = 0.0
            n_pairs = 0
            for i, a in enumerate(member_list):
                for b in member_list[i + 1:]:
                    total_rencor += (
                        a.resentments.get(b.id, 0.0)
                        + b.resentments.get(a.id, 0.0)
                    ) / 2.0
                    n_pairs += 1
            if n_pairs == 0:
                continue

            rencor_medio = total_rencor / n_pairs

            # Registrar solo una vez al cruzar el umbral (evita spam diario)
            dominant_arch = max(
                member_list, key=lambda ag: ag.archetypes.sabio
            ).archetypes.dominant()

            if rencor_medio >= _CISMA_THRESH:
                # Verificar si ya registrado hoy
                last_events = cmem.records[-3:] if cmem.records else []
                already = any(
                    r.tipo_evento == "tension_social"
                    and "cisma_inminente" in r.descripcion_actual
                    for r in last_events
                )
                if not already:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = "colectivo",
                        arquetipo_dominante = dominant_arch,
                        tipo_evento         = "tension_social",
                        descripcion         = (
                            f"Rencor arquetípico crítico (ρ={rencor_medio:.2f}): "
                            f"cisma inminente en tribu {tribe_id}."
                        ),
                        intensidad          = rencor_medio,
                    )
            elif rencor_medio >= _PRE_CISMA_THRESH:
                last_events = cmem.records[-3:] if cmem.records else []
                already = any(
                    r.tipo_evento == "tension_social"
                    and "pre_cisma" in r.descripcion_actual
                    for r in last_events
                )
                if not already:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = "colectivo",
                        arquetipo_dominante = dominant_arch,
                        tipo_evento         = "tension_social",
                        descripcion         = (
                            f"Tensión arquetípica creciente (ρ={rencor_medio:.2f}): "
                            f"pre_cisma detectado en tribu {tribe_id}."
                        ),
                        intensidad          = rencor_medio,
                    )

    def _detect_schism_events(
        self,
        old_tribes: dict[str, set[str]],
        dia: int,
    ) -> None:
        """
        Compara la composición tribal antes y después del reclúster.
        Si un grupo de agentes que formaba parte de una tribu A ahora constituye
        una tribu B distinta, se registra 'schisma_tribal' en la CulturalMemory
        de ambas tribus resultantes.
        """
        new_tribes = self.tribe_manager.tribes  # {tribe_id: set[agent_id]}

        for new_tid, new_members in new_tribes.items():
            if len(new_members) < 2:
                continue

            # ¿De qué tribu vieja proviene la mayoría de estos agentes?
            origin_counts: dict[str, int] = {}
            for mid in new_members:
                for old_tid, old_members in old_tribes.items():
                    if mid in old_members:
                        origin_counts[old_tid] = origin_counts.get(old_tid, 0) + 1
                        break

            if not origin_counts:
                continue

            primary_origin = max(origin_counts, key=origin_counts.__getitem__)
            primary_count  = origin_counts[primary_origin]

            # Cisma: la tribu nueva no es simplemente la misma tribu renombrada
            # → menos del 90 % de sus miembros vienen de una sola tribu vieja
            # → y la tribu origen OLD ha disminuido significativamente
            old_size     = len(old_tribes.get(primary_origin, set()))
            fraction_old = primary_count / old_size if old_size > 0 else 0.0

            if new_tid == primary_origin:
                continue  # misma tribu, no hay cisma
            if fraction_old < 0.20 or primary_count < 2:
                continue  # grupo demasiado pequeño para llamarse cisma

            # Registrar el cisma en la tribu nueva
            cmem_new = self.tribe_manager.cultural_memories.get(new_tid)
            if cmem_new is not None:
                dominant = (
                    max(
                        (self.agents[mid] for mid in new_members if mid in self.agents),
                        key=lambda ag: ag.archetypes.sabio,
                    ).archetypes.dominant()
                    if any(mid in self.agents for mid in new_members)
                    else "heroe"
                )
                cmem_new.record_event(
                    dia                 = dia,
                    agente_nombre       = "colectivo",
                    arquetipo_dominante = dominant,
                    tipo_evento         = "schisma_tribal",
                    descripcion         = (
                        f"Cisma: {primary_count} agentes se separaron de la tribu "
                        f"'{primary_origin}' y fundaron '{new_tid}' "
                        f"(día {dia})."
                    ),
                    intensidad          = 0.80,
                )

            # Registrar la fractura en la tribu origen
            cmem_old = self.tribe_manager.cultural_memories.get(primary_origin)
            if cmem_old is not None:
                cmem_old.record_event(
                    dia                 = dia,
                    agente_nombre       = "colectivo",
                    arquetipo_dominante = "sombra",
                    tipo_evento         = "schisma_tribal",
                    descripcion         = (
                        f"Fractura: {primary_count} miembros abandonaron la tribu "
                        f"'{primary_origin}' y formaron '{new_tid}' "
                        f"(día {dia})."
                    ),
                    intensidad          = 0.75,
                )

            # Carga sombra en los campos colectivos de ambas tribus
            for tid in (new_tid, primary_origin):
                lf = self.tribe_manager.local_fields.get(tid) or self.collective_field
                lf.absorb_interaction("sombra", "rebelde", "choque_violento")

    # ── Ext. B: Proto-Chamanismo ──────────────────────────────────────────────

    def _is_chaman_candidate(self, agent_id: str) -> bool:
        agent = self.agents.get(agent_id)
        if agent is None or not agent.is_alive or agent.es_infante:
            return False
        if agent.archetypes.sabio < _CHAMAN_MIN_SABIO:
            return False
        ritual_medicine = sum(
            1
            for kname in self.knowledge.get(agent_id)
            if _ALL_KNOWLEDGE.get(kname, KnowledgeUnit("", "", 0, 0)).tipo
            in _CHAMAN_KNOWLEDGE_TIPOS
            and self.knowledge.get_fidelity(agent_id, kname) > 0.50
        )
        return ritual_medicine >= 2

    def _process_proto_chaman(self, dia: int) -> None:
        """
        Ciclo diario del proto-chamanismo (Ext. B):
        1. Detectar chamanes emergentes por acumulación de consultas.
        2. Generar consultas durante crisis tribales.
        3. Chamán responde → gratitud o rencor.
        4. Histeria decae si el chamán murió sin sucesor.
        5. Chamán privilegiado en integraciones simbólicas (aplicado en otros métodos).
        """
        self._detect_proto_chamanes(dia)
        self._generate_chaman_consultations(dia)
        self._tick_chaman_hysteria(dia)

    def _detect_proto_chamanes(self, dia: int) -> None:
        """
        Para tribus sin chamán formal: si un candidato acumula ≥ 3 consultas
        en los últimos 90 días, emerge como proto-chamán.
        """
        for tribe_id, members in self.tribe_manager.tribes.items():
            # Si el chamán actual sigue vivo, no buscar
            current = self._proto_chamanes.get(tribe_id)
            if current and self.agents.get(current) and self.agents[current].is_alive:
                continue

            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is None:
                continue

            # Contar consultas recientes por agente (usando nombre en descripcion_actual)
            consult_count: dict[str, int] = {}
            for rec in cmem.records:
                if rec.tipo_evento != "consulta_chaman":
                    continue
                if dia - rec.dia_origen > _CHAMAN_CONSULT_WINDOW:
                    continue
                # El chamán consultado aparece en agente_origen del registro
                consult_count[rec.agente_origen] = (
                    consult_count.get(rec.agente_origen, 0) + 1
                )

            best_id   = None
            best_count = 0
            for mid in members:
                if not self._is_chaman_candidate(mid):
                    continue
                agent = self.agents[mid]
                cnt = consult_count.get(agent.nombre, 0)
                if cnt > best_count:
                    best_count = cnt
                    best_id    = mid

            if best_id is not None and best_count >= _CHAMAN_MIN_CONSULTAS:
                self._proto_chamanes[tribe_id] = best_id
                chaman_agent = self.agents[best_id]
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = chaman_agent.nombre,
                    arquetipo_dominante = "sabio",
                    tipo_evento         = "emergencia_chaman",
                    descripcion         = (
                        f"{chaman_agent.nombre} emergió como proto-chamán de la tribu "
                        f"'{tribe_id}' tras {best_count} consultas (día {dia})."
                    ),
                    intensidad          = 0.85,
                )
                # Boost ICL tribal
                lf = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field
                lf.absorb_event("ritual", intensity=0.70)
                print(f"  [🌀] Día {dia}: {chaman_agent.nombre} emerge como proto-chamán "
                      f"de la tribu '{tribe_id}'.")

    def _generate_chaman_consultations(self, dia: int) -> None:
        """
        Durante crisis tribales, los miembros buscan espontáneamente al candidato/chamán.
        El chamán responde según su conocimiento → gratitud o rencor en consecuencia.
        """
        for tribe_id, members in self.tribe_manager.tribes.items():
            alive = [
                mid for mid in members
                if mid in self.agents and self.agents[mid].is_alive
                and not self.agents[mid].es_infante
            ]
            if len(alive) < 2:
                continue

            # ¿Hay crisis activa en esta tribu?
            n_ansiosos = sum(
                1 for mid in alive if self.agents[mid].ansiedad > 0.70
            )
            ugs_activos = [
                ug for ug in self._tribe_unprocessed_griefs.get(tribe_id, [])
                if not ug.resuelto and not ug.convertido
            ]
            in_crisis = n_ansiosos >= 2 or len(ugs_activos) >= 1

            if not in_crisis:
                continue

            # Encontrar chamán o candidato más apto
            chaman_id = self._proto_chamanes.get(tribe_id)
            if chaman_id is None or not (
                self.agents.get(chaman_id) and self.agents[chaman_id].is_alive
            ):
                # Buscar mejor candidato aunque aún no formal
                best_id, best_sabio = None, 0.0
                for mid in alive:
                    if self._is_chaman_candidate(mid):
                        s = self.agents[mid].archetypes.sabio
                        if s > best_sabio:
                            best_sabio = s
                            best_id    = mid
                chaman_id = best_id

            if chaman_id is None:
                continue

            chaman = self.agents[chaman_id]
            cmem   = self.tribe_manager.cultural_memories.get(tribe_id)

            # Conocimiento de respuesta (ritual o medicina)
            chaman_knows = [
                kn for kn in self.knowledge.get(chaman_id)
                if _ALL_KNOWLEDGE.get(kn, KnowledgeUnit("", "", 0, 0)).tipo
                in _CHAMAN_KNOWLEDGE_TIPOS
                and self.knowledge.get_fidelity(chaman_id, kn) > 0.35
            ]
            puede_responder = len(chaman_knows) > 0

            for mid in alive:
                if mid == chaman_id:
                    continue
                if self._rng.random() >= _CHAMAN_CRISIS_PROB:
                    continue

                consultor = self.agents[mid]

                if puede_responder:
                    # Respuesta exitosa: reduce ansiedad, consolida bond
                    consultor.ansiedad = max(0.0, consultor.ansiedad - 0.06)
                    old_bond = self.social_network.get_bond(mid, chaman_id)
                    self.social_network.set_bond(
                        mid, chaman_id, min(1.0, old_bond + 0.03)
                    )
                    resultado = "resolucion"
                else:
                    # Silencio: el chamán no sabe → resentimiento
                    consultor.resentments[chaman_id] = min(
                        1.0, consultor.resentments.get(chaman_id, 0.0) + 0.05
                    )
                    resultado = "silencio"

                if cmem is not None:
                    # Registrar solo si no hay registro reciente del mismo par
                    reciente = any(
                        r.tipo_evento == "consulta_chaman"
                        and chaman.nombre in r.descripcion_actual
                        and dia - r.dia_origen < 7
                        for r in cmem.records[-5:]
                    )
                    if not reciente:
                        cmem.record_event(
                            dia                 = dia,
                            agente_nombre       = chaman.nombre,
                            arquetipo_dominante = "sabio",
                            tipo_evento         = "consulta_chaman",
                            descripcion         = (
                                f"{consultor.nombre} consultó a {chaman.nombre} "
                                f"en crisis ({resultado}, día {dia})."
                            ),
                            intensidad          = 0.50,
                        )

    def _on_chaman_death(self, dead_agent_id: str, dia: int) -> None:
        """
        Llamado desde _register_death() cuando muere un proto-chamán.
        Si no hay sucesor inmediato → histeria colectiva + regresión tecnológica.
        """
        # Encontrar la tribu del chamán fallecido
        tribe_id = None
        for tid, cid in list(self._proto_chamanes.items()):
            if cid == dead_agent_id:
                tribe_id = tid
                del self._proto_chamanes[tid]
                break
        if tribe_id is None:
            return

        dead = self.agents[dead_agent_id]

        # ¿Hay sucesor inmediato?
        members = self.tribe_manager.tribes.get(tribe_id, set())
        sucesor = next(
            (
                mid for mid in members
                if mid != dead_agent_id
                and self._is_chaman_candidate(mid)
            ),
            None,
        )

        cmem = self.tribe_manager.cultural_memories.get(tribe_id)
        lf   = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field

        if sucesor is not None:
            self._proto_chamanes[tribe_id] = sucesor
            suc_agent = self.agents[sucesor]
            if cmem is not None:
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = suc_agent.nombre,
                    arquetipo_dominante = "sabio",
                    tipo_evento         = "sucesion_chaman",
                    descripcion         = (
                        f"Tras la muerte de {dead.nombre}, "
                        f"{suc_agent.nombre} asumió el rol de mediador simbólico "
                        f"en la tribu '{tribe_id}' (día {dia})."
                    ),
                    intensidad          = 0.70,
                )
        else:
            # Sin sucesor → histeria
            self._chaman_hysteria[tribe_id] = _CHAMAN_HYSTERIA_DAYS
            for mid in members:
                ag = self.agents.get(mid)
                if ag and ag.is_alive:
                    ag.ansiedad = min(1.0, ag.ansiedad + 0.20)
                    ag.episodic_log.append(
                        f"Día {dia}: La muerte de {dead.nombre} "
                        f"dejó a la tribu sin guía. Histeria colectiva."
                    )
            lf.absorb_event("catastrofe", intensity=0.80)
            if cmem is not None:
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = dead.nombre,
                    arquetipo_dominante = "muerte",
                    tipo_evento         = "muerte_chaman",
                    descripcion         = (
                        f"{dead.nombre}, proto-chamán de '{tribe_id}', "
                        f"murió sin sucesor el día {dia}. "
                        f"La tribu entra en histeria y pierde su mediador simbólico."
                    ),
                    intensidad          = 0.90,
                )
            print(f"  [💀] Día {dia}: {dead.nombre} (chamán de '{tribe_id}') "
                  f"murió sin sucesor — histeria tribal activada.")

    def _tick_chaman_hysteria(self, dia: int) -> None:
        """Decae la histeria tribal día a día; aplica perturbación al ICL."""
        for tribe_id in list(self._chaman_hysteria):
            remaining = self._chaman_hysteria[tribe_id]
            if remaining <= 0:
                del self._chaman_hysteria[tribe_id]
                continue
            self._chaman_hysteria[tribe_id] = remaining - 1
            lf = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field
            lf.absorb_interaction("sombra", "muerte", "duelo_colectivo")

    # ── Hito E: Cristalización de Deidades desde el ICL ──────────────────────

    def _process_deity_emergence(self, dia: int) -> None:
        """
        Ciclo diario:
        1. Actualiza racha de dominancia arquetípica por tribu.
        2. Detecta emergencia por racha ≥ 30 días (ICL) o por 3ª cristalización del par.
        3. Aplica efectos cotidianos de deidades ya existentes.
        4. Detecta conflicto teológico inter-tribal.
        """
        self._update_archetype_streaks(dia)
        self._check_deity_from_streak(dia)
        self._check_deity_from_myth_repeat(dia)
        self._apply_deity_effects(dia)
        self._check_deity_conflict(dia)

    def _update_archetype_streaks(self, dia: int) -> None:
        """Contabiliza días consecutivos en que un arquetipo domina el ICL tribal."""
        for tribe_id, members in self.tribe_manager.tribes.items():
            lf = self.tribe_manager.local_fields.get(tribe_id)
            if lf is None:
                continue
            tribe_streaks = self._archetype_streak.setdefault(tribe_id, {})
            # Encontrar el arquetipo dominante en el campo local
            dominant = max(lf.symbols.items(), key=lambda x: x[1], default=(None, 0.0))
            dom_arch, dom_val = dominant
            if dom_arch is None or dom_val < _DEITY_ICL_THRESHOLD:
                # Sin dominancia clara → resetear todas las rachas
                tribe_streaks.clear()
                continue
            # Incrementar la racha del dominante y resetear los demás
            for arch in list(tribe_streaks):
                if arch != dom_arch:
                    tribe_streaks[arch] = 0
            tribe_streaks[dom_arch] = tribe_streaks.get(dom_arch, 0) + 1

    def _check_deity_from_streak(self, dia: int) -> None:
        """Cristaliza deidad cuando un arquetipo domina ≥ 30 días consecutivos."""
        for tribe_id, streaks in self._archetype_streak.items():
            for arch, days in streaks.items():
                if days < _DEITY_STREAK_DAYS:
                    continue
                # ¿Ya existe una deidad de este arquetipo en esta tribu?
                already = any(
                    d.arquetipo_fundacional == arch and d.tribu_origen == tribe_id
                    for d in self.mythology_engine.deities
                )
                if already:
                    continue
                self._crystallize_deity(
                    arquetipo  = arch,
                    tribe_id   = tribe_id,
                    dia        = dia,
                    causa      = "icl_streak",
                    intensidad = min(1.0, days / 60.0 + 0.50),
                )
                # Resetear la racha tras la cristalización
                streaks[arch] = 0

    def _check_deity_from_myth_repeat(self, dia: int) -> None:
        """
        Cristaliza deidad cuando el mismo par mítico cristaliza por 3ª vez.
        La deidad se atribuye a la tribu con mayor ICL del arquetipo protagonista.
        """
        for myth in self.mythology_engine.active_myths:
            if not (myth.active or myth.es_leyenda):
                continue
            arch1, arch2 = myth.par
            count = self.mythology_engine.pair_crystallization_count(arch1, arch2)
            if count < _DEITY_MYTH_REPEAT:
                continue
            # ¿Ya existe deidad de alguno de estos arquetipos por este par?
            already = any(
                d.arquetipo_fundacional in (arch1, arch2)
                and d.causa == "myth_repeat"
                for d in self.mythology_engine.deities
            )
            if already:
                continue
            # Arquetipo protagonista = el que tiene mayor carga ICL en el campo global
            global_val_1 = self.collective_field.symbols.get(arch1, 0.0)
            global_val_2 = self.collective_field.symbols.get(arch2, 0.0)
            dominant_arch = arch1 if global_val_1 >= global_val_2 else arch2
            # Tribu con mayor ICL de ese arquetipo
            best_tribe, best_val = None, -1.0
            for tid in self.tribe_manager.tribes:
                lf = self.tribe_manager.local_fields.get(tid)
                if lf is None:
                    continue
                val = lf.symbols.get(dominant_arch, 0.0)
                if val > best_val:
                    best_val  = val
                    best_tribe = tid
            if best_tribe is None:
                best_tribe = next(iter(self.tribe_manager.tribes), "global")
            self._crystallize_deity(
                arquetipo  = dominant_arch,
                tribe_id   = best_tribe,
                dia        = dia,
                causa      = "myth_repeat",
                intensidad = min(1.0, count * 0.20 + 0.40),
            )

    def _crystallize_deity(
        self,
        arquetipo:  str,
        tribe_id:   str,
        dia:        int,
        causa:      str,
        intensidad: float,
    ) -> None:
        """Crea la DeityRecord, actualiza CulturalMemory e ICL, y activa proto-sacerdocio."""
        nombre = _deity_name(arquetipo, tribe_id)
        esfera = _ARCH_TO_SPHERE.get(arquetipo, "poder_primordial")

        deity = DeityRecord(
            nombre                = nombre,
            arquetipo_fundacional = arquetipo,
            esfera_de_influencia  = esfera,
            intensidad            = intensidad,
            dia_cristalizacion    = dia,
            tribu_origen          = tribe_id,
            causa                 = causa,
        )
        self.mythology_engine.deities.append(deity)

        # Registrar en CulturalMemory
        cmem = self.tribe_manager.cultural_memories.get(tribe_id)
        if cmem is not None:
            cmem.record_event(
                dia                 = dia,
                agente_nombre       = nombre,
                arquetipo_dominante = arquetipo,
                tipo_evento         = "emergencia_deidad",
                descripcion         = (
                    f"'{nombre}' emergió como deidad de la tribu '{tribe_id}'. "
                    f"Esfera: {esfera}. Causa: {causa}. Día {dia}."
                ),
                intensidad          = min(1.0, intensidad + 0.10),
            )

        # Boost ICL: la deidad estabiliza su arquetipo
        lf = self.tribe_manager.local_fields.get(tribe_id) or self.collective_field
        lf.symbols[arquetipo] = min(1.0, lf.symbols.get(arquetipo, 0.0) + 0.20)
        lf.myth_pressure  = max(0.0, lf.myth_pressure  - 0.30)
        lf.confusion      = max(0.0, lf.confusion      - 0.20)

        print(f"  [🕊️] Día {dia}: '{nombre}' cristalizó como deidad en tribu "
              f"'{tribe_id}' ({causa}, arq={arquetipo}).")

        # Proto-sacerdocio: el agente con mayor alineación asume/consolida el rol
        members = self.tribe_manager.tribes.get(tribe_id, set())
        best_agent_id, best_val = None, -1.0
        for mid in members:
            ag = self.agents.get(mid)
            if ag is None or not ag.is_alive or ag.es_infante:
                continue
            val = getattr(ag.archetypes, arquetipo if arquetipo != "muerte" else "sombra", 0.0)
            if val > best_val:
                best_val      = val
                best_agent_id = mid

        if best_agent_id is not None:
            current_chaman = self._proto_chamanes.get(tribe_id)
            if current_chaman is None:
                self._proto_chamanes[tribe_id] = best_agent_id
                ag = self.agents[best_agent_id]
                if cmem is not None:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = ag.nombre,
                        arquetipo_dominante = "sabio",
                        tipo_evento         = "proto_sacerdocio",
                        descripcion         = (
                            f"{ag.nombre} se convirtió en proto-sacerdote de '{nombre}' "
                            f"en la tribu '{tribe_id}' (día {dia})."
                        ),
                        intensidad          = 0.80,
                    )
            else:
                # Consolidar el sacerdocio existente
                ag = self.agents.get(current_chaman)
                if ag and cmem is not None:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = ag.nombre,
                        arquetipo_dominante = "sabio",
                        tipo_evento         = "consolidacion_sacerdocio",
                        descripcion         = (
                            f"{ag.nombre} consolidó su autoridad sagrada "
                            f"como guardián de '{nombre}' (día {dia})."
                        ),
                        intensidad          = 0.65,
                    )

    def _apply_deity_effects(self, dia: int) -> None:
        """
        Efectos cotidianos de deidades activas:
        - Agentes con alineación > 0.55 al arquetipo reciben protección (ansiedad -0.003).
        - Deidades oscuras (sombra, muerte) invierten el efecto sobre sus fieles.
        - El ICL tribal decae un 5% más lento mientras exista la deidad.
        """
        _DARK_ARCHETYPES = {"sombra", "muerte", "trickster"}

        for deity in self.mythology_engine.deities:
            if not deity.is_active:
                continue
            arch     = deity.arquetipo_fundacional
            is_dark  = arch in _DARK_ARCHETYPES
            tribe_id = deity.tribu_origen
            members  = self.tribe_manager.tribes.get(tribe_id, set())

            for mid in members:
                ag = self.agents.get(mid)
                if ag is None or not ag.is_alive or ag.es_infante:
                    continue
                alignment = getattr(ag.archetypes, arch if arch != "muerte" else "sombra", 0.0)
                if alignment < _DEITY_EFFECT_THRESHOLD:
                    continue
                if is_dark:
                    # Deidad oscura refuerza la tensión en sus fieles
                    ag.ansiedad = min(1.0, ag.ansiedad + 0.002 * alignment)
                else:
                    # Deidad protectora atenúa la ansiedad
                    ag.ansiedad = max(0.0, ag.ansiedad - 0.003 * alignment)

    def _check_deity_conflict(self, dia: int) -> None:
        """
        Dos tribus con deidades del mismo arquetipo pero nombres distintos →
        tensión inter-tribal: ICL pressure aumenta, resentimientos entre miembros.
        Solo se registra una vez cada 30 días para evitar spam.
        """
        active_deities = [d for d in self.mythology_engine.deities if d.is_active]
        checked: set[frozenset] = set()

        for i, d1 in enumerate(active_deities):
            for d2 in active_deities[i + 1:]:
                if d1.tribu_origen == d2.tribu_origen:
                    continue
                if d1.arquetipo_fundacional != d2.arquetipo_fundacional:
                    continue
                if d1.nombre == d2.nombre:
                    continue  # mismo nombre → sincretismo, no conflicto
                pair = frozenset({d1.tribu_origen, d2.tribu_origen})
                if pair in checked:
                    continue
                checked.add(pair)

                # Tensión en los campos locales
                for tid in (d1.tribu_origen, d2.tribu_origen):
                    lf = self.tribe_manager.local_fields.get(tid) or self.collective_field
                    lf.myth_pressure     = min(1.0, lf.myth_pressure     + 0.005)
                    lf.emotional_pressure = min(1.0, lf.emotional_pressure + 0.003)

                # Registro en CulturalMemory cada 30 días
                if dia % 30 != 0:
                    continue
                for tid, deity in ((d1.tribu_origen, d1), (d2.tribu_origen, d2)):
                    cmem = self.tribe_manager.cultural_memories.get(tid)
                    if cmem is None:
                        continue
                    other_name = d2.nombre if tid == d1.tribu_origen else d1.nombre
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = deity.nombre,
                        arquetipo_dominante = deity.arquetipo_fundacional,
                        tipo_evento         = "conflicto_teologico",
                        descripcion         = (
                            f"'{deity.nombre}' y '{other_name}' son deidades rivales "
                            f"del mismo arquetipo. Tensión teológica creciente (día {dia})."
                        ),
                        intensidad          = 0.60,
                    )

    # ── Hito C: Objetos Sagrados y Creación Compulsiva ───────────────────────

    def _process_sacred_objects(self, dia: int) -> None:
        # Decrementar cooldowns
        for aid in list(self._objeto_cooldown):
            self._objeto_cooldown[aid] = max(0, self._objeto_cooldown[aid] - 1)

        self._try_create_objects(dia)
        self._apply_sacred_object_effects(dia)

    def _try_create_objects(self, dia: int) -> None:
        for agent in self.agents.values():
            if not agent.is_alive or agent.es_infante:
                continue
            if self._objeto_cooldown.get(agent.id, 0) > 0:
                continue

            lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
            dominant = max(lf.symbols.items(), key=lambda x: x[1], default=(None, 0.0))
            dom_arch, dom_val = dominant

            triggered = dom_val > _SACRED_OBJ_THRESHOLD or agent.ansiedad > 0.80
            if not triggered:
                continue
            if self._rng.random() >= _SACRED_OBJ_PROB:
                continue

            # Determinar tipo según estado psicológico del creador
            if agent.dissociation_state is not None or agent.archetypes.sombra > 0.65:
                tipo = "perturbador"
            elif agent.active_griefs:
                tipo = "duelo"
            elif dom_arch in ("sombra", "muerte", "trickster") and dom_val > 0.50:
                tipo = "ambiguo"
            else:
                tipo = "protector"

            arquetipo = dom_arch or agent.archetypes.dominant()
            prefix    = self._rng.choice(_SACRED_OBJECT_PREFIXES.get(tipo, ["Objeto"]))
            nombre    = f"{prefix} de {arquetipo.replace('_', ' ').capitalize()}"

            obj = SacredObject(
                nombre               = nombre,
                tipo                 = tipo,
                arquetipo_dominante  = arquetipo,
                intensidad_simbolica = min(1.0, dom_val * 0.70 + agent.ansiedad * 0.30),
                creador_id           = agent.id,
                creador_nombre       = agent.nombre,
                dia_creacion         = dia,
                propietario_id       = agent.id,
                hex_coord            = agent.posicion,
                historial            = [{"agent_id": agent.id, "nombre": agent.nombre,
                                         "dia": dia, "evento": "creacion"}],
            )
            self._sacred_objects.append(obj)
            self._objeto_cooldown[agent.id] = _SACRED_OBJ_COOLDOWN

            agent.episodic_log.append(
                f"Día {dia}: Creó '{nombre}' (tipo={tipo}) en estado compulsivo."
            )

            # GraveHex de duelo: ancla la memoria al hex
            if tipo == "duelo" and agent.active_griefs:
                grave_coord = agent.active_griefs[0].grave_coord
                if grave_coord and grave_coord in self.world_ref.graves.graves:
                    self.world_ref.graves.graves[grave_coord].carga_simbolica = min(
                        1.0,
                        self.world_ref.graves.graves[grave_coord].carga_simbolica + 0.15,
                    )

            # Registrar creación en CulturalMemory
            tribe_id = self.tribe_manager.get_tribe_id(agent.id)
            if tribe_id:
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is not None:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = agent.nombre,
                        arquetipo_dominante = arquetipo,
                        tipo_evento         = "creacion_objeto_sagrado",
                        descripcion         = (
                            f"{agent.nombre} creó '{nombre}' en estado compulsivo "
                            f"(tipo={tipo}, día {dia})."
                        ),
                        intensidad          = obj.intensidad_simbolica,
                    )
            print(f"  [🪬] Día {dia}: {agent.nombre} creó '{nombre}' ({tipo}).")

    def _apply_sacred_object_effects(self, dia: int) -> None:
        """Aplica efectos diarios de objetos sagrados a portadores y hexes."""
        for obj in self._sacred_objects:
            intensidad = obj.intensidad_simbolica

            # Objeto con portador
            if obj.propietario_id is not None:
                portador = self.agents.get(obj.propietario_id)
                if portador is None or not portador.is_alive:
                    continue
                arch = obj.arquetipo_dominante
                alignment = getattr(
                    portador.archetypes, arch if arch != "muerte" else "sombra", 0.0
                )

                if obj.tipo == "protector":
                    if alignment > 0.45:
                        portador.ansiedad = max(0.0, portador.ansiedad - 0.004 * intensidad)

                elif obj.tipo == "perturbador":
                    portador.ansiedad = min(1.0, portador.ansiedad + 0.006 * intensidad)
                    # Sueños perturbadores periódicos
                    if dia % 5 == 0:
                        portador.episodic_log.append(
                            f"Día {dia}: El '{obj.nombre}' genera presagios inquietantes."
                        )

                elif obj.tipo == "ambiguo":
                    if alignment > 0.50:
                        portador.ansiedad = max(0.0, portador.ansiedad - 0.003 * intensidad)
                    else:
                        portador.ansiedad = min(1.0, portador.ansiedad + 0.001 * intensidad)

                elif obj.tipo == "duelo":
                    # Mantiene vivo el duelo; sueños perturbadores cada 7 días
                    if dia % 7 == 0 and portador.active_griefs:
                        fallecido = portador.active_griefs[0].agente_fallecido
                        portador.episodic_log.append(
                            f"Día {dia}: El '{obj.nombre}' evoca a Falleció {fallecido}."
                        )
                    # Boost diario al GraveHex asociado
                    if obj.hex_coord and obj.hex_coord in self.world_ref.graves.graves:
                        self.world_ref.graves.graves[obj.hex_coord].carga_simbolica = min(
                            1.0,
                            self.world_ref.graves.graves[obj.hex_coord].carga_simbolica
                            + _SACRED_OBJ_HEX_BOOST,
                        )

                # Actualizar hex_coord al hex del portador
                obj.hex_coord = portador.posicion

            else:
                # Objeto en hex sin portador: efecto débil a todos en ese hex
                if obj.hex_coord is None:
                    continue
                arch = obj.arquetipo_dominante
                for other in self.agents.values():
                    if not other.is_alive or other.posicion != obj.hex_coord:
                        continue
                    if obj.tipo == "perturbador":
                        other.ansiedad = min(1.0, other.ansiedad + 0.002 * intensidad)
                    elif obj.tipo == "protector":
                        alignment = getattr(other.archetypes, arch if arch != "muerte" else "sombra", 0.0)
                        if alignment > 0.45:
                            other.ansiedad = max(0.0, other.ansiedad - 0.001 * intensidad)

                # Boost al GraveHex (carga × 1.5 efectiva via boost diario)
                if obj.hex_coord in self.world_ref.graves.graves:
                    self.world_ref.graves.graves[obj.hex_coord].carga_simbolica = min(
                        1.0,
                        self.world_ref.graves.graves[obj.hex_coord].carga_simbolica
                        + _SACRED_OBJ_HEX_BOOST * 1.5,
                    )

    def _transfer_objects_on_death(self, dead_id: str, dia: int) -> None:
        """Transfiere objetos sagrados del fallecido al sobreviviente con mayor bond."""
        dead = self.agents.get(dead_id)
        for obj in self._sacred_objects:
            if obj.propietario_id != dead_id:
                continue
            best_id, best_bond = None, 0.0
            for aid, ag in self.agents.items():
                if not ag.is_alive or aid == dead_id:
                    continue
                b = self.social_network.get_bond(aid, dead_id)
                if b > best_bond:
                    best_bond, best_id = b, aid

            if best_id is not None:
                obj.propietario_id = best_id
                obj.hex_coord      = self.agents[best_id].posicion
                obj.historial.append({
                    "agent_id": best_id,
                    "nombre":   self.agents[best_id].nombre,
                    "dia":      dia,
                    "evento":   "herencia",
                })
                # Perturbador: el heredero recibe impacto de ansiedad
                if obj.tipo == "perturbador":
                    self.agents[best_id].ansiedad = min(
                        1.0, self.agents[best_id].ansiedad + obj.intensidad_simbolica * 0.15
                    )
            else:
                # Cae al hex
                obj.propietario_id = None
                obj.hex_coord      = dead.posicion if dead else obj.hex_coord
                obj.historial.append({
                    "agent_id": None, "nombre": "hex",
                    "dia": dia, "evento": "perdido_en_muerte",
                })

    # ── Hito H: Roles Sociales Emergentes ────────────────────────────────────

    def _process_social_roles(self, dia: int) -> None:
        self._tick_role_transitions(dia)
        self._update_role_legitimacy(dia)
        if dia % _ROLE_UPDATE_INTERVAL == 0:
            self._detect_social_roles(dia)

    def _detect_social_roles(self, dia: int) -> None:
        """
        Detecta candidatos para los tres roles sociales en cada tribu.
        Solo actúa si el rol no existe o si su portador está muerto/inelegible.
        """
        for tribe_id, members in self.tribe_manager.tribes.items():
            alive = [
                self.agents[mid] for mid in members
                if mid in self.agents and self.agents[mid].is_alive
                and not self.agents[mid].es_infante
            ]
            if len(alive) < 2:
                continue

            active_tipos = {r.tipo for r in self._social_roles if r.tribe_id == tribe_id and r.is_active}

            # ── Elder ────────────────────────────────────────────────────────
            if "anciano" not in active_tipos:
                candidate = max(alive, key=lambda a: a.edad)
                if candidate.edad >= 40:
                    # Verificar que tiene bonds medios ≥ umbral
                    avg_bond = (
                        sum(self.social_network.get_bond(mid, candidate.id) for mid in members if mid != candidate.id)
                        / max(1, len(members) - 1)
                    )
                    if avg_bond >= _ROLE_ELDER_MIN_BOND:
                        self._social_roles.append(SocialRole(
                            tipo            = "anciano",
                            portador_id     = candidate.id,
                            portador_nombre = candidate.nombre,
                            tribe_id        = tribe_id,
                            dia_inicio      = dia,
                            legitimidad     = 0.30,
                        ))
                        self._announce_role(tribe_id, candidate, "anciano", dia)

            # ── Big Man ──────────────────────────────────────────────────────
            if "big_man" not in active_tipos:
                # Proxy: agente con mayor suma de bonds salientes hacia la tribu
                def outgoing_sum(ag):
                    return sum(self.social_network.get_bond(ag.id, mid) for mid in members if mid != ag.id)
                candidate = max(alive, key=outgoing_sum)
                if outgoing_sum(candidate) >= 0.50 * (len(alive) - 1):
                    self._social_roles.append(SocialRole(
                        tipo            = "big_man",
                        portador_id     = candidate.id,
                        portador_nombre = candidate.nombre,
                        tribe_id        = tribe_id,
                        dia_inicio      = dia,
                        legitimidad     = 0.30,
                    ))
                    self._announce_role(tribe_id, candidate, "big_man", dia)

            # ── Cazador focal ────────────────────────────────────────────────
            if "cazador_focal" not in active_tipos:
                subsistence_agents = [
                    a for a in alive
                    if self.knowledge.has(a.id, "caza_avanzada")
                    or self.knowledge.has(a.id, "conservacion_agua")
                ]
                if subsistence_agents:
                    candidate = min(subsistence_agents, key=lambda a: a.needs.hambre)
                    if candidate.needs.hambre < 0.25:
                        self._social_roles.append(SocialRole(
                            tipo            = "cazador_focal",
                            portador_id     = candidate.id,
                            portador_nombre = candidate.nombre,
                            tribe_id        = tribe_id,
                            dia_inicio      = dia,
                            legitimidad     = 0.30,
                        ))
                        self._announce_role(tribe_id, candidate, "cazador_focal", dia)

    def _announce_role(self, tribe_id: str, agent, tipo: str, dia: int) -> None:
        cmem = self.tribe_manager.cultural_memories.get(tribe_id)
        if cmem is not None:
            cmem.record_event(
                dia                 = dia,
                agente_nombre       = agent.nombre,
                arquetipo_dominante = agent.archetypes.dominant(),
                tipo_evento         = "rol_social_emergente",
                descripcion         = (
                    f"{agent.nombre} emergió como '{tipo}' en la tribu "
                    f"'{tribe_id}' (día {dia})."
                ),
                intensidad          = 0.65,
            )

    def _update_role_legitimacy(self, dia: int) -> None:
        """
        Verifica si el portador sigue cumpliendo los criterios del rol.
        Si la legitimidad cae por debajo del umbral → inicia transición.
        """
        for role in self._social_roles:
            if not role.is_active or role.dias_transicion > 0:
                continue
            portador = self.agents.get(role.portador_id)
            if portador is None or not portador.is_alive:
                self._start_role_transition(role, dia)
                continue

            members = self.tribe_manager.tribes.get(role.tribe_id, set())
            alive = [
                self.agents[mid] for mid in members
                if mid in self.agents and self.agents[mid].is_alive
                and not self.agents[mid].es_infante
            ]

            still_valid = False
            if role.tipo == "anciano":
                if alive:
                    oldest = max(alive, key=lambda a: a.edad)
                    still_valid = oldest.id == role.portador_id
            elif role.tipo == "big_man":
                if alive:
                    def outgoing_sum(ag):
                        return sum(self.social_network.get_bond(ag.id, mid) for mid in members if mid != ag.id)
                    best = max(alive, key=outgoing_sum)
                    still_valid = best.id == role.portador_id
            elif role.tipo == "cazador_focal":
                still_valid = (
                    portador.needs.hambre < 0.30
                    and (self.knowledge.has(role.portador_id, "caza_avanzada")
                         or self.knowledge.has(role.portador_id, "conservacion_agua"))
                )

            if still_valid:
                role.legitimidad = min(1.0, role.legitimidad + _ROLE_LEGITIMACY_GAIN)
                # Elder con alta legitimidad refuerza bonds tribales levemente
                if role.tipo == "anciano" and role.legitimidad > 0.70:
                    for mid in members:
                        if mid == role.portador_id:
                            continue
                        old = self.social_network.get_bond(mid, role.portador_id)
                        self.social_network.set_bond(mid, role.portador_id, min(1.0, old + 0.002))
            else:
                role.legitimidad = max(0.0, role.legitimidad - _ROLE_LEGITIMACY_LOSS)
                if role.legitimidad < _ROLE_MIN_LEGITIMACY:
                    self._start_role_transition(role, dia)

    def _start_role_transition(self, role: SocialRole, dia: int) -> None:
        """Inicia período de transición: el rol queda vacante."""
        duration = self._rng.randint(_ROLE_TRANSITION_MIN, _ROLE_TRANSITION_MAX)
        role.dias_transicion = duration

        # Buscar candidato
        members = self.tribe_manager.tribes.get(role.tribe_id, set())
        alive = [
            self.agents[mid] for mid in members
            if mid in self.agents and self.agents[mid].is_alive
            and not self.agents[mid].es_infante
            and mid != role.portador_id
        ]
        if alive:
            if role.tipo == "anciano":
                cand = max(alive, key=lambda a: a.edad)
            elif role.tipo == "big_man":
                cand = max(alive, key=lambda a: sum(
                    self.social_network.get_bond(a.id, mid) for mid in members if mid != a.id
                ))
            else:
                subsistence = [a for a in alive if self.knowledge.has(a.id, "caza_avanzada")
                               or self.knowledge.has(a.id, "conservacion_agua")]
                cand = min(subsistence, key=lambda a: a.needs.hambre) if subsistence else alive[0]
            role.candidato_id = cand.id

        # Perturbación ICL durante la transición
        lf = self.tribe_manager.local_fields.get(role.tribe_id) or self.collective_field
        lf.emotional_pressure = min(1.0, lf.emotional_pressure + 0.12)
        lf.confusion          = min(1.0, lf.confusion          + 0.08)

        cmem = self.tribe_manager.cultural_memories.get(role.tribe_id)
        if cmem is not None:
            cmem.record_event(
                dia                 = dia,
                agente_nombre       = role.portador_nombre,
                arquetipo_dominante = "muerte",
                tipo_evento         = "transicion_rol",
                descripcion         = (
                    f"El rol de '{role.tipo}' quedó vacante tras la pérdida de "
                    f"{role.portador_nombre}. Transición de {duration} días iniciada "
                    f"en tribu '{role.tribe_id}' (día {dia})."
                ),
                intensidad          = 0.75,
            )

    def _tick_role_transitions(self, dia: int) -> None:
        """Decae la transición día a día y asigna el candidato cuando termina."""
        for role in self._social_roles:
            if not role.is_active or role.dias_transicion <= 0:
                continue

            role.dias_transicion -= 1

            # Inestabilidad diaria durante transición
            lf = self.tribe_manager.local_fields.get(role.tribe_id) or self.collective_field
            lf.emotional_pressure = min(1.0, lf.emotional_pressure + 0.005)

            if role.dias_transicion == 0 and role.candidato_id:
                cand = self.agents.get(role.candidato_id)
                if cand and cand.is_alive:
                    role.portador_id     = cand.id
                    role.portador_nombre = cand.nombre
                    role.legitimidad     = 0.30
                    role.candidato_id    = None
                    cmem = self.tribe_manager.cultural_memories.get(role.tribe_id)
                    if cmem is not None:
                        cmem.record_event(
                            dia                 = dia,
                            agente_nombre       = cand.nombre,
                            arquetipo_dominante = cand.archetypes.dominant(),
                            tipo_evento         = "sucesion_rol",
                            descripcion         = (
                                f"{cand.nombre} absorbió el rol de '{role.tipo}' "
                                f"en la tribu '{role.tribe_id}' (día {dia})."
                            ),
                            intensidad          = 0.60,
                        )
                else:
                    role.is_active = False  # rol extinto sin sucesor

    def _check_reproduccion(self, tp: TimePoint) -> None:
        if self.alive_count() >= _LIMITE_POBLACION:
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
        self.lineage.register(
            hijo_id, parent_a.id, parent_b.id, dia, tribe_nac,
            dominant_arch=child.archetypes.dominant(),
        )

        # ── R5-A3: Arquetipos recesivos de abuelos ────────────────────────────
        # Si un abuelo tenía un arquetipo muy fuerte que los padres no heredaron,
        # puede re-emerger en el nieto con probabilidad reducida.
        _RECESSIVE_PROB    = 0.20
        _RECESSIVE_THRESH  = 0.68   # abuelo debe tener arquetipo ≥ este nivel
        _PARENT_SUPPRESSED = 0.40   # ambos padres deben estar por debajo
        _RECESSIVE_VALUE   = 0.45   # valor que hereda el nieto si el rasgo re-emerge

        grandparent_ids: set[str] = set()
        for parent_id in (parent_a.id, parent_b.id):
            prec = self.lineage.records.get(parent_id)
            if prec:
                for gp in (prec.parent_a, prec.parent_b):
                    if gp:
                        grandparent_ids.add(gp)

        for gp_id in grandparent_ids:
            gp_agent = self.agents.get(gp_id)
            gp_rec   = self.lineage.records.get(gp_id)
            if gp_agent is None and gp_rec is None:
                continue
            # Obtener arquetipos del abuelo (vivo → directo; muerto → dominant_arch del registro)
            if gp_agent is not None and gp_agent.is_alive:
                for raw_name in ARCHETYPE_NAMES:
                    attr = "self_" if raw_name == "self" else raw_name
                    gp_val = getattr(gp_agent.archetypes, attr, 0.0)
                    if gp_val < _RECESSIVE_THRESH:
                        continue
                    pa_val = getattr(parent_a.archetypes, attr, 1.0)
                    pb_val = getattr(parent_b.archetypes, attr, 1.0)
                    if pa_val > _PARENT_SUPPRESSED or pb_val > _PARENT_SUPPRESSED:
                        continue
                    if self._rng.random() < _RECESSIVE_PROB:
                        current = getattr(child.archetypes, attr, 0.0)
                        setattr(child.archetypes, attr, max(current, _RECESSIVE_VALUE))
            elif gp_rec is not None:
                # Abuelo muerto: solo su dominant_arch puede re-emerger
                attr = "self_" if gp_rec.dominant_arch == "self" else gp_rec.dominant_arch
                pa_val = getattr(parent_a.archetypes, attr, 1.0)
                pb_val = getattr(parent_b.archetypes, attr, 1.0)
                if pa_val <= _PARENT_SUPPRESSED and pb_val <= _PARENT_SUPPRESSED:
                    if self._rng.random() < _RECESSIVE_PROB * 0.5:
                        current = getattr(child.archetypes, attr, 0.0)
                        setattr(child.archetypes, attr, max(current, _RECESSIVE_VALUE - 0.08))

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

        # Hito K: trauma transgeneracional — presencias no resueltas en la tribu
        # elevan el complejo de culpa del recién nacido (Faimberg, "El telescopaje")
        tribe_id = self.tribe_manager.get_tribe_id(parent_a.id)
        if tribe_id:
            ugs = self._tribe_unprocessed_griefs.get(tribe_id, [])
            culpa_extra = sum(
                ug.intensidad * 0.08
                for ug in ugs
                if not ug.resuelto and not ug.convertido
            )
            if culpa_extra > 0:
                child.complexes.culpa = min(
                    1.0, child.complexes.culpa + min(0.15, culpa_extra)
                )
                child.episodic_log.append(
                    f"Día {dia}: Nació bajo la sombra de presencias no resueltas."
                )

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

        # R5-C2 — Enteógenos amplifican sueños compartidos:
        # Si ≥2 agentes en el mismo hex tienen _enteogen_active, se fuerza resonancia mutua.
        hex_enteogen: dict[tuple, list[str]] = {}
        for aid, agent in self.agents.items():
            if agent.is_alive and agent._enteogen_active:
                hex_enteogen.setdefault(agent.posicion, []).append(aid)
                agent._enteogen_active = False  # reset transient flag
        for hex_aids in hex_enteogen.values():
            if len(hex_aids) < 2:
                continue
            # El agente con mayor tensión arquetípica emite el símbolo
            emitter_id = max(hex_aids, key=lambda a: self.agents[a].archetypes.tension())
            emitter    = self.agents[emitter_id]
            arch       = emitter.archetypes.dominant()
            pool       = _ARCHETYPE_SYMBOLS.get(arch, [_DEFAULT_SYMBOL])
            sym        = emitter._rng.choice(pool)
            for aid in hex_aids:
                if resonances.get(aid) is None:
                    resonances[aid] = sym

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
                # Registro cultural y episódico al primer día de catástrofe
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
                    # Trauma episódico: la catástrofe queda como recuerdo de largo plazo
                    arch_ct = agent.archetypes.dominant()
                    arch_ct_norm = "self_" if arch_ct == "self" else arch_ct
                    agent.episodic_memory.record(MemoryRecord(
                        tipo_evento          = f"trauma_{cat.tipo}",
                        intensidad_emocional = min(1.0, cat.severidad * 0.85),
                        dia_origen           = tp.dia_simulado,
                        agente_protagonista  = cat.tipo,
                        arquetipo_dominante  = arch_ct_norm,
                    ))

    def _process_catastrophe_narrative(self, tp: "TimePoint", cat_engine) -> None:
        """R5-B4: Catástrofes narrativas profundas. Absorbe trauma en campos colectivos
        y registra el fin de catástrofe como evento cultural permanente."""
        _CAT_TO_TRAUMA: dict[str, str | None] = {
            "sequia_prolongada": "deshidratacion",
            "invierno_brutal":   "clima_extremo",
            "incendio":          "muerte_masiva",
            "plaga":             "muerte_masiva",
            "eclipse":           None,
        }
        cat = cat_engine.active
        dia = tp.dia_simulado

        if cat is not None and cat.dias_transcurridos == 1:
            trauma_tipo = _CAT_TO_TRAUMA.get(cat.tipo)
            if trauma_tipo:
                self.collective_field.absorb_trauma(trauma_tipo, intensity=cat.severidad)
                for lf in self.tribe_manager.local_fields.values():
                    lf.absorb_trauma(trauma_tipo, intensity=cat.severidad)
            if cat.tipo == "eclipse":
                self.collective_field.myth_pressure = min(
                    1.0, self.collective_field.myth_pressure + 0.35
                )
                self.collective_field.confusion = min(
                    1.0, self.collective_field.confusion + 0.40
                )
                for lf in self.tribe_manager.local_fields.values():
                    lf.myth_pressure = min(1.0, lf.myth_pressure + 0.35)
                    lf.confusion     = min(1.0, lf.confusion     + 0.40)

        ended = cat_engine.just_ended
        if ended is not None:
            for tribe_id, members in self.tribe_manager.tribes.items():
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is None:
                    continue
                alive_in_tribe = sum(
                    1 for aid in members
                    if self.agents.get(aid) and self.agents[aid].is_alive
                )
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = "colectivo",
                    arquetipo_dominante = "sabio",
                    tipo_evento         = f"catastrofe_{ended.tipo}",
                    descripcion         = (
                        f"La {ended.tipo.replace('_', ' ')} duró {ended.duracion_dias} días "
                        f"(severidad {ended.severidad:.2f}). "
                        f"La tribu sobrevivió con {alive_in_tribe} miembros."
                    ),
                    intensidad          = ended.severidad,
                )

            # R5-B3: marcar cicatriz ecológica/traumática en hexes ocupados por agentes vivos
            if hasattr(self.world_ref, "psychic_geography"):
                occupied: set[tuple[int, int]] = {
                    a.posicion for a in self.agents.values() if a.is_alive
                }
                for coord in occupied:
                    self.world_ref.psychic_geography.register_catastrophe(
                        coord = coord,
                        tipo  = ended.tipo,
                        sev   = ended.severidad,
                        dia   = dia,
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

        # ── 2b. Bestias míticas únicas (R4-D) ─────────────────────────────────
        for fauna_info in fauna_activa:
            if fauna_info.get("tipo") != "bestia_mitica":
                continue
            nombre = fauna_info.get("nombre", "")
            fcoord = tuple(fauna_info.get("coord", [0, 0]))
            for agent in self.agents.values():
                if not agent.is_alive:
                    continue
                dist = abs(agent.posicion[0] - fcoord[0]) + abs(agent.posicion[1] - fcoord[1])
                if dist > 6:
                    continue
                tribe_id = self.tribe_manager.get_tribe_id(agent.id) or ""
                fauna_sys.register_sighting(tribe_id, nombre)
                lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                lf.myth_pressure = min(1.0, lf.myth_pressure + 0.55 * 0.20)
                lf.symbols["sombra"] = min(1.0, lf.symbols.get("sombra", 0.0) + 0.12)
                lf.symbols["muerte"] = min(1.0, lf.symbols.get("muerte", 0.0) + 0.08)

        # Bestias olvidadas: registrar en CulturalMemory + PsychicGeography
        fauna_events = getattr(self.world_ref, "_fauna_events", [])
        for ev in fauna_events:
            if ev.get("tipo") != "bestia_olvidada":
                continue
            nombre  = ev.get("nombre", "bestia")
            ev_dia  = ev.get("dia",    tp.dia_simulado)
            ev_coord = tuple(ev.get("coord", [0, 0]))
            # Registrar en todas las tribus que la observaron
            for tribe_id in list(self.tribe_manager.tribes.keys()):
                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                if cmem is None:
                    continue
                obs = fauna_sys._tribe_obs.get(tribe_id, {}).get(nombre, 0)
                if obs == 0:
                    continue
                cmem.record_event(
                    dia                 = ev_dia,
                    agente_nombre       = "colectivo",
                    arquetipo_dominante = "muerte",
                    tipo_evento         = "bestia_olvidada",
                    descripcion         = (
                        f"El {nombre} desapareció el día {ev_dia}. "
                        f"Ya nadie lo volvió a ver. Su memoria se convierte en leyenda."
                    ),
                    intensidad          = 0.80,
                )
            # Marcar el hex donde vivía como lugar_sagrado/zona_maldita
            pg = getattr(self.world_ref, "psychic_geography", None)
            if pg is not None:
                pg.register_mark(
                    coord       = ev_coord,
                    tipo        = "lugar_sagrado",
                    carga       = 0.70,
                    dia         = ev_dia,
                    descripcion = f"El {nombre}, bestia olvidada, habitó aquí.",
                )

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

        # ── 3. R5-E1: Efectos físicos sobre agentes DENTRO del hex liminal ───────
        # Un agente que duerme en el hex recibe: ansiedad aumentada, presión mítica
        # directa al campo, y probabilidad de muerte ambiental inexplicable.
        for lhex in liminal_sys.hexes:
            cell = terrain.get(*lhex.coord) if terrain else None
            if cell is None or not cell.explored:
                continue
            for agent in self.agents.values():
                if not agent.is_alive or agent.posicion != lhex.coord:
                    continue
                # Presión mítica directa (más intensa que el efecto de proximidad)
                lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                lf.myth_pressure = min(1.0, lf.myth_pressure + lhex.misterio * 0.06)
                lf.confusion     = min(1.0, lf.confusion     + lhex.misterio * 0.04)
                # Ansiedad individual: el lugar no es comprensible
                agent.ansiedad = min(1.0, agent.ansiedad + lhex.misterio * 0.03)
                agent.in_liminal = True

                # Muerte ambiental inexplicable (fauna liminal, microclima extremo)
                # prob = misterio × 0.002 — baja, pero no nula → terror epistemológico
                if self._rng.random() < lhex.misterio * 0.002:
                    tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                    self._register_death(agent, tp, "causa_liminal_inexplicable")
                    # Registrar en memoria cultural: muerte sin causa = tabú
                    if tribe_id:
                        cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                        if cmem is not None:
                            cmem.record_event(
                                dia                 = tp.dia_simulado,
                                agente_nombre       = agent.nombre,
                                arquetipo_dominante = "sombra",
                                tipo_evento         = "muerte_liminal",
                                descripcion         = (
                                    f"{agent.nombre} murió sin causa aparente en el "
                                    f"lugar misterioso {lhex.coord} el día {tp.dia_simulado}."
                                ),
                                intensidad          = lhex.misterio,
                            )

    # ── Fin Hito 8 + R5-E1 ────────────────────────────────────────────────────

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

    # ── R5-D3: Muerte cultural y colapso civilizatorio ────────────────────────

    def _process_cultural_collapse(self, dia: int) -> None:
        """
        Una tribu entra en colapso cultural cuando pierde:
        - La mayoría de su conocimiento técnico (extinción epistémica), O
        - Todos sus mitos activos (vacío simbólico), O
        - Todos sus miembros excepto 1-2 (extinción demográfica inminente).

        Efectos del colapso:
        1. El campo local sufre un reset traumático (alta confusión + mito_pressure residual).
        2. Los hexes donde vivía la tribu se marcan como ruinas en PsychicGeography.
        3. Los miembros supervivientes cargan un nuevo complejo de abandono.
        4. Las estructuras de la tribu pasan a "abandonadas" en PersistentStructureSystem.
        5. Se registra en CulturalMemory como evento histórico permanente.
        """
        _COLLAPSE_MIN_MEMBERS    = 2    # menos de esto → colapso demográfico
        _COLLAPSE_MIN_KNOWLEDGE  = 1    # menos de este n° de saberes vivos → epistémico
        _COLLAPSE_ANSIEDAD_BONUS = 0.40

        pg  = getattr(self.world_ref, "psychic_geography",    None)
        pss = getattr(self.world_ref, "persistent_structures", None)

        for tribe_id, members in list(self.tribe_manager.tribes.items()):
            alive = [
                aid for aid in members
                if self.agents.get(aid) and self.agents[aid].is_alive
            ]
            if not alive:
                continue

            # Verificar si ya se registró un colapso reciente (últimos 90 días)
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is not None:
                recent_collapse = [
                    r for r in cmem.records
                    if r.tipo_evento == "colapso_civilizatorio"
                    and dia - r.dia_origen < 90
                ]
                if recent_collapse:
                    continue

            # ── Condiciones de colapso ─────────────────────────────────────────
            colapso_demografico   = len(alive) < _COLLAPSE_MIN_MEMBERS
            colapso_epistemico    = sum(
                1 for aid in alive
                if self.knowledge.knowledge_count(aid) > 0
            ) < _COLLAPSE_MIN_KNOWLEDGE
            colapso_simbolico     = (
                len(self.mythology_engine.active_myths) == 0
                and len(alive) <= 3
            )

            if not (colapso_demografico or colapso_epistemico or colapso_simbolico):
                continue

            # ── Determinar tipo de colapso ─────────────────────────────────────
            if colapso_demografico:
                tipo_colapso = "colapso_demografico"
                descripcion  = (
                    f"La tribu {tribe_id} quedó con {len(alive)} supervivientes "
                    f"el día {dia}. Su civilización se disuelve."
                )
            elif colapso_epistemico:
                tipo_colapso = "colapso_epistemico"
                descripcion  = (
                    f"La tribu {tribe_id} perdió todo su conocimiento técnico "
                    f"el día {dia}. El saber se extinguió con sus portadores."
                )
            else:
                tipo_colapso = "colapso_simbolico"
                descripcion  = (
                    f"La tribu {tribe_id} perdió todos sus mitos activos "
                    f"el día {dia}. El vacío simbólico es total."
                )

            # ── Efectos en el campo local ──────────────────────────────────────
            lf = self.tribe_manager.local_fields.get(tribe_id)
            if lf is not None:
                lf.confusion     = min(1.0, lf.confusion     + 0.45)
                lf.myth_pressure = max(0.0, lf.myth_pressure - 0.20)
                lf.absorb_trauma("muerte_masiva", intensity=0.90)

            # ── Efectos en supervivientes ──────────────────────────────────────
            for aid in alive:
                agent = self.agents[aid]
                agent.ansiedad           = min(1.0, agent.ansiedad + _COLLAPSE_ANSIEDAD_BONUS)
                agent.complexes.abandono = min(1.0, agent.complexes.abandono + 0.35)
                agent.episodic_log.append(
                    f"Día {dia}: El colapso de nuestra tribu. Solo quedamos {len(alive)}."
                )
                agent.episodic_memory.record(MemoryRecord(
                    tipo_evento          = "colapso_civilizatorio",
                    intensidad_emocional = 0.95,
                    dia_origen           = dia,
                    agente_protagonista  = tribe_id,
                    arquetipo_dominante  = "muerte",
                ))

            # ── Marcar hexes tribales como ruinas ─────────────────────────────
            tribal_coords: set[tuple[int, int]] = {
                self.agents[aid].posicion for aid in alive
            }
            if pg is not None:
                for coord in tribal_coords:
                    pg.register_ruin(coord=coord, dia=dia, tribu_caida=tribe_id)

            # ── Pasar estructuras a "abandonadas" ─────────────────────────────
            if pss is not None:
                for coord, structs in pss._structures.items():
                    for s in structs:
                        if s.tribu_origen == tribe_id and s.estado == "activo":
                            s.estado = "abandonado"

            # ── Registro histórico ─────────────────────────────────────────────
            if cmem is not None:
                cmem.record_event(
                    dia                 = dia,
                    agente_nombre       = "colectivo",
                    arquetipo_dominante = "muerte",
                    tipo_evento         = "colapso_civilizatorio",
                    descripcion         = descripcion,
                    intensidad          = 1.00,
                )

            # ── Presión al campo colectivo global ──────────────────────────────
            self.collective_field.absorb_trauma("muerte_masiva", intensity=0.70)

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
            tribe_id_disc = self.tribe_manager.get_tribe_id(agent.id)
            for cond_key, kname, base_prob in _DISCOVERY_TRIGGERS:
                if self.knowledge.has(agent.id, kname):
                    continue
                if not self._check_discovery_condition(agent, snap, cond_key):
                    continue
                # Regresión tecnológica: histeria post-muerte de chamán (Ext. B)
                prob_efectiva = base_prob
                if tribe_id_disc and tribe_id_disc in self._chaman_hysteria:
                    prob_efectiva *= 0.50
                if self._rng.random() >= prob_efectiva:
                    continue
                # Descubrimiento accidental
                self.knowledge.give(agent.id, kname)
                if tribe_id_disc:
                    cmem = self.tribe_manager.cultural_memories.get(tribe_id_disc)
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
                    lf = self.tribe_manager.local_fields.get(tribe_id_disc)
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
                        success, fidelidad = self.knowledge.teach(
                            teacher_id, student_id, kname, self._rng, bond
                        )
                        if success:
                            # Transmisión exitosa: carga sabio/gobernante en el campo local
                            tribe_id = self.tribe_manager.get_tribe_id(student_id)
                            lf = (self.tribe_manager.local_fields.get(tribe_id)
                                  if tribe_id else None) or self.collective_field
                            lf.absorb_event("transmision_conocimiento", intensity=0.5)
                            if tribe_id:
                                cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                                if cmem is not None:
                                    recientes = [
                                        r for r in cmem.records
                                        if r.tipo_evento in (
                                            "transmision_conocimiento",
                                            "supersticion_tecnica",
                                        )
                                        and kname in r.descripcion_actual
                                        and dia - r.dia_origen < 30
                                    ]
                                    if not recientes:
                                        teacher_ag = self.agents[teacher_id]
                                        student_ag = self.agents[student_id]
                                        nombre_actual = self.knowledge.get_nombre_actual(
                                            student_id, kname
                                        )
                                        # Detectar superstición
                                        is_super = self.knowledge.get_fidelity(
                                            student_id, kname
                                        ) < 0.20
                                        cmem.record_event(
                                            dia=dia,
                                            agente_nombre=teacher_ag.nombre,
                                            arquetipo_dominante=(
                                                "trickster" if is_super else "sabio"
                                            ),
                                            tipo_evento=(
                                                "supersticion_tecnica"
                                                if is_super
                                                else "transmision_conocimiento"
                                            ),
                                            descripcion=(
                                                f"{teacher_ag.nombre} transmitió '{nombre_actual}' "
                                                f"a {student_ag.nombre} "
                                                f"(fidelidad={fidelidad:.2f}, día {dia})."
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

    # ── R4-Ext.C: Intercambio inter-tribal de conocimiento ────────────────────

    def _process_intertribal_knowledge_exchange(self, tp) -> None:
        """
        Transmisión diplomática de conocimiento entre agentes de tribus distintas
        que comparten hex con algún vínculo mínimo.

        Diferencias respecto a la transmisión intra-tribal:
        - Umbral de bond menor (0.20 vs 0.50)
        - Probabilidad de éxito reducida (× 0.35 vs × 1.0)
        - Fidelidad usa bond × 0.50 como bond efectivo → mayor degradación
        - Se registra en CulturalMemory de AMBAS tribus
        """
        dia = tp.dia_simulado if hasattr(tp, "dia_simulado") else tp

        by_pos: dict[tuple, list[str]] = {}
        for aid, agent in self.agents.items():
            if agent.is_alive:
                by_pos.setdefault(agent.posicion, []).append(aid)

        for aids in by_pos.values():
            if len(aids) < 2:
                continue
            for i, teacher_id in enumerate(aids):
                t_tribe = self.tribe_manager.get_tribe_id(teacher_id)
                teacher_ks = self.knowledge.get(teacher_id)
                if not teacher_ks:
                    continue
                for student_id in aids[i + 1:]:
                    s_tribe = self.tribe_manager.get_tribe_id(student_id)
                    if t_tribe is None or s_tribe is None or t_tribe == s_tribe:
                        continue  # sólo inter-tribal
                    bond = self.social_network.get_bond(teacher_id, student_id)
                    if bond < 0.20:
                        continue
                    effective_bond = bond * 0.50  # degradación mayor por barrera cultural
                    for kname in list(teacher_ks):
                        if self.knowledge.has(student_id, kname):
                            continue
                        ku = _ALL_KNOWLEDGE.get(kname)
                        if ku is None:
                            continue
                        prob = (1.0 - ku.complejidad) * 0.15 * 0.35
                        if self._rng.random() >= prob:
                            continue

                        success, fidelidad = self.knowledge.teach(
                            teacher_id, student_id, kname, self._rng, effective_bond
                        )
                        if not success:
                            continue

                        # Aumentar vínculo entre los dos embajadores del conocimiento
                        b_ts = self.social_network.get_bond(teacher_id, student_id)
                        b_st = self.social_network.get_bond(student_id, teacher_id)
                        self.social_network.set_bond(teacher_id, student_id, min(1.0, b_ts + 0.04))
                        self.social_network.set_bond(student_id, teacher_id, min(1.0, b_st + 0.04))

                        teacher_ag = self.agents[teacher_id]
                        student_ag = self.agents[student_id]
                        nombre_actual = self.knowledge.get_nombre_actual(student_id, kname)

                        # Registro en la tribu del estudiante
                        cmem_s = self.tribe_manager.cultural_memories.get(s_tribe)
                        if cmem_s is not None:
                            cmem_s.record_event(
                                dia                 = dia,
                                agente_nombre       = student_ag.nombre,
                                arquetipo_dominante = "sabio",
                                tipo_evento         = "intercambio_diplomatico",
                                descripcion         = (
                                    f"{student_ag.nombre} aprendió '{nombre_actual}' de "
                                    f"{teacher_ag.nombre} (tribu {t_tribe}), "
                                    f"fidelidad {fidelidad:.2f}."
                                ),
                                intensidad          = 0.55,
                            )
                        # Registro en la tribu del maestro (prestigio por difundir conocimiento)
                        cmem_t = self.tribe_manager.cultural_memories.get(t_tribe)
                        if cmem_t is not None:
                            cmem_t.record_event(
                                dia                 = dia,
                                agente_nombre       = teacher_ag.nombre,
                                arquetipo_dominante = "sabio",
                                tipo_evento         = "difusion_diplomatica",
                                descripcion         = (
                                    f"{teacher_ag.nombre} enseñó '{nombre_actual}' a "
                                    f"{student_ag.nombre} (tribu {s_tribe}) el día {dia}."
                                ),
                                intensidad          = 0.45,
                            )

                        # R5-A4: spread léxico en contacto inter-tribal
                        if t_tribe and s_tribe:
                            self.emergent_lexicon.spread_across_tribes(t_tribe, s_tribe)

    # ── R5-A2: Infancia, Desarrollo e Imprinting ─────────────────────────────

    def _process_infant_imprinting(self, dia: int) -> None:
        """
        Durante la niñez (edad < 6): el agente con mayor bond entrante hacia
        el infante se convierte en su figura de apego. Su arquetipo dominante
        se imprime con plasticidad = 1 - (edad / 6). Al entrar en adolescencia
        (6-14), el arquetipo dominante del ICL tribal sesga la cristalización.
        Al entrar en la adultez (15), el imprinting se bloquea definitivamente.

        Trauma infantil: si la figura de apego muere mientras el infante está
        en niñez, se activa el complejo de abandono a nivel máximo.
        """
        _PLASTICITY_NINEZ = 6.0  # años de alta plasticidad
        _ARCH_ATTRS = [
            "heroe", "sombra", "madre", "padre", "sabio",
            "trickster", "rebelde", "gobernante", "nino_divino",
        ]

        for agent in self.agents.values():
            if not agent.is_alive:
                continue

            fase = agent.fase_desarrollo

            # Bloquear imprinting una vez adulto
            if fase == "adulto" and not agent._imprinting_locked:
                agent._imprinting_locked = True
                continue
            if agent._imprinting_locked:
                continue

            if fase == "niñez":
                plasticity = max(0.0, 1.0 - agent.edad / _PLASTICITY_NINEZ)
                if plasticity < 0.02:
                    continue

                # Encontrar figura de apego (agente con mayor bond hacia el infante)
                mejor_bond, mejor_id = 0.0, None
                for oid in self.agents:
                    if oid == agent.id:
                        continue
                    b = self.social_network.get_bond(oid, agent.id)
                    if b > mejor_bond:
                        mejor_bond, mejor_id = b, oid

                if mejor_id is None:
                    continue
                agent._figura_apego_id = mejor_id
                figura = self.agents[mejor_id]
                if not figura.is_alive:
                    continue

                # Imprinting: arquetipo dominante de la figura de apego se imprime
                arch_apego = figura.archetypes.dominant()
                attr = "self_" if arch_apego == "self" else arch_apego
                current = getattr(agent.archetypes, attr, 0.3)
                delta   = mejor_bond * plasticity * 0.012
                setattr(agent.archetypes, attr, min(1.0, current + delta))

            elif fase == "adolescencia":
                # En adolescencia: cristalización por contexto tribal
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                lf = self.tribe_manager.local_fields.get(tribe_id) if tribe_id else None
                if lf is None:
                    continue
                dom_arch, _ = lf.dominant_archetype_pair()
                attr = "self_" if dom_arch == "self" else dom_arch
                current = getattr(agent.archetypes, attr, 0.3)
                # Efecto débil: el contexto tribal sesga ligeramente el arquetipo
                setattr(agent.archetypes, attr, min(1.0, current + 0.002))

    # ── R5-B3: Geografía Psicológica ──────────────────────────────────────────

    def _process_psychic_geography(self, dia: int) -> None:
        """
        Aplica los efectos de las marcas psíquicas del hex donde está cada agente.

        Los agentes no saben por qué sienten lo que sienten — los efectos llegan
        como ansiedad inexplicable, confusión o mito-presión elevada.
        Eso genera superstición y tabú espacial de forma emergente.
        """
        if not hasattr(self.world_ref, "psychic_geography"):
            return
        pg = self.world_ref.psychic_geography

        for agent in self.agents.values():
            if not agent.is_alive or agent.in_liminal:
                continue

            effect = pg.get_effect(agent.posicion)
            if not effect:
                continue

            agent.ansiedad = min(1.0, agent.ansiedad + effect.get("ansiedad_delta", 0.0))

            myth_delta = effect.get("myth_pressure_delta", 0.0)
            if myth_delta > 0:
                lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                lf.myth_pressure = min(1.0, lf.myth_pressure + myth_delta * 0.5)

            confusion_delta = effect.get("confusion_delta", 0.0)
            if confusion_delta > 0:
                lf = self.tribe_manager.get_local_field(agent.id) or self.collective_field
                lf.confusion = min(1.0, lf.confusion + confusion_delta * 0.5)

            if effect.get("es_maldita") and agent._rng.random() < 0.002:
                self._register_death(agent, type("_TP", (), {
                    "tick": dia * 12,
                    "dia_simulado": dia,
                    "hora_del_dia": 0,
                    "estacion": "desconocida",
                })(), "muerte_inexplicable_zona_maldita")

    # ── R5-B2: Estructuras Persistentes ──────────────────────────────────────

    def _process_structure_effects(self, dia: int) -> None:
        """
        Aplica el bonus de refugio y gestiona artefactos de conocimiento (R5-B1/B2).
        Actualiza las coords ocupadas en WorldCore para el ciclo diario de estructuras.
        """
        pss = getattr(self.world_ref, "persistent_structures", None)

        occupied: set[tuple[int, int]] = set()
        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            occupied.add(agent.posicion)

            # R5-B2: bonus de refugio nocturno
            if pss is not None:
                bonus = pss.shelter_bonus(agent.posicion)
                if bonus > 0:
                    agent.ansiedad = max(0.0, agent.ansiedad - bonus)

            # R5-B1: agente habilidoso en hex con estructura → deposita artefacto (prob baja)
            if (pss is not None
                    and pss.has_active(agent.posicion, "refugio")
                    and self.knowledge.has(agent.id, "tecnica_constructiva")
                    and self._rng.random() < 0.003):
                fidelidad = self.knowledge.get_fidelity(agent.id, "tecnica_constructiva")
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                self.artifacts.deposit(
                    coord          = agent.posicion,
                    knowledge_name = "tecnica_constructiva",
                    fidelidad      = fidelidad,
                    tribu          = tribe_id,
                    dia            = dia,
                )

            # R5-B1: agente en hex con artefactos → intenta aprender
            learned = self.artifacts.try_learn(agent.posicion, agent.id, self.knowledge, self._rng)
            for kname in learned:
                tribe_id = self.tribe_manager.get_tribe_id(agent.id)
                if tribe_id:
                    cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                    if cmem is not None:
                        cmem.record_event(
                            dia                 = dia,
                            agente_nombre       = agent.nombre,
                            arquetipo_dominante = "sabio",
                            tipo_evento         = "aprendizaje_artefacto",
                            descripcion         = (
                                f"{agent.nombre} aprendió '{kname}' de un artefacto "
                                f"dejado por antepasados en el día {dia}."
                            ),
                            intensidad          = 0.60,
                        )

        if hasattr(self.world_ref, "update_occupied_coords"):
            self.world_ref.update_occupied_coords(occupied)

        # Ciclo diario de artefactos
        self.artifacts.on_day()

    # ── R5-D2: Economía Simbólica ─────────────────────────────────────────────

    def _process_symbolic_economy(self, dia: int) -> None:
        """
        Deuda ritual y prestigio acumulado.

        1. Registro de deuda cuando un agente cura/protege/rescata a otro.
        2. El prestador de la acción acumula prestigio proporcional a testigos vinculados.
        3. El prestigio modula el techo máximo de bonds entrantes y la lectura de
           las acciones futuras del agente (acciones de alto prestigio = interpretación +).
        4. La deuda no saldada en 60+ días genera resentimiento de baja intensidad.
        5. Decaimiento lento del prestigio (−0.001/día) para mantener competencia.
        """
        _DEBT_CAP     = 0.90   # máximo de deuda bilateral
        _PRESTIGE_CAP = 1.00
        _DEBT_DECAY   = 0.004  # decaimiento diario de la deuda (se resuelve con tiempo)
        _PRESTIGE_DECAY = 0.001

        for agent in self.agents.values():
            if not agent.is_alive:
                continue

            # Decaimiento de prestigio
            agent.prestigio = max(0.0, agent.prestigio - _PRESTIGE_DECAY)

            # Decaimiento y resentimiento por deudas antiguas
            to_remove = []
            for other_id, intensity in list(agent.deuda_ritual.items()):
                new_intensity = intensity - _DEBT_DECAY
                if new_intensity <= 0.0:
                    to_remove.append(other_id)
                else:
                    agent.deuda_ritual[other_id] = new_intensity
                    # Resentimiento pasivo si la deuda persiste demasiado
                    if intensity > 0.50 and self._rng.random() < 0.01:
                        lf = self.tribe_manager.get_local_field(agent.id)
                        if lf is not None:
                            lf.confusion = min(1.0, lf.confusion + 0.005)
            for oid in to_remove:
                del agent.deuda_ritual[oid]

            # El prestigio del agente amplifica su ICL local: presencia dominante
            if agent.prestigio > 0.60:
                lf = self.tribe_manager.get_local_field(agent.id)
                if lf is not None:
                    arch = agent.archetypes.dominant()
                    lf.symbols[arch] = min(
                        1.0, lf.symbols.get(arch, 0.0) + agent.prestigio * 0.002
                    )

        # Generación de deuda por rescate/curación observable
        # Ocurre cuando un agente con necesidades críticas está en el mismo hex que otro
        # que acaba de donar recursos (medido por necesidades por encima del umbral crítico)
        for aid, agent in self.agents.items():
            if not agent.is_alive:
                continue
            # Agente en estado crítico = potencial receptor de ayuda
            if agent.needs.hambre > 0.80 or agent.needs.sed > 0.80:
                tribe_id = self.tribe_manager.get_tribe_id(aid)
                for oid, other in self.agents.items():
                    if oid == aid or not other.is_alive:
                        continue
                    if other.posicion != agent.posicion:
                        continue
                    bond = self.social_network.get_bond(oid, aid)
                    if bond < 0.40:
                        continue
                    # El otro agente "rescata" si tiene mejor estado
                    if other.needs.hambre < 0.40 and other.needs.sed < 0.40:
                        # Registro de deuda: agent debe a other
                        existing = agent.deuda_ritual.get(oid, 0.0)
                        agent.deuda_ritual[oid] = min(_DEBT_CAP, existing + 0.15)

                        # Prestigio para el rescatador proporcional a testigos con bond
                        testigos = sum(
                            1 for wid, w in self.agents.items()
                            if w.is_alive and w.posicion == other.posicion
                            and self.social_network.get_bond(wid, oid) > 0.30
                        )
                        gain = 0.03 * max(1, testigos)
                        other.prestigio = min(_PRESTIGE_CAP, other.prestigio + gain)

                        # Registro cultural en la tribu del rescatado
                        if tribe_id:
                            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
                            if cmem is not None:
                                recientes = [
                                    r for r in cmem.records
                                    if r.tipo_evento == "deuda_ritual"
                                    and oid in r.descripcion_actual
                                    and dia - r.dia_origen < 20
                                ]
                                if not recientes:
                                    cmem.record_event(
                                        dia                 = dia,
                                        agente_nombre       = other.nombre,
                                        arquetipo_dominante = other.archetypes.dominant(),
                                        tipo_evento         = "deuda_ritual",
                                        descripcion         = (
                                            f"{other.nombre} socorrió a {agent.nombre} "
                                            f"en situación crítica el día {dia}. "
                                            f"Deuda ritual registrada."
                                        ),
                                        intensidad          = 0.60,
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
            "unprocessed_griefs": {
                tid: [ug.to_dict() for ug in ugs]
                for tid, ugs in self._tribe_unprocessed_griefs.items()
                if ugs
            },
            "proto_chamanes":    dict(self._proto_chamanes),
            "chaman_hysteria":   dict(self._chaman_hysteria),
            "archetype_streak":  {
                tid: dict(s) for tid, s in self._archetype_streak.items()
            },
            "sacred_objects":    [o.to_dict() for o in self._sacred_objects],
            "objeto_cooldown":   {k: int(v) for k, v in self._objeto_cooldown.items()},
            "social_roles":      [r.to_dict() for r in self._social_roles],
            "artifacts":         self.artifacts.to_dict(),
            "emergent_lexicon":  self.emergent_lexicon.to_dict(),
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

        if "unprocessed_griefs" in data:
            for tid, ugs in data["unprocessed_griefs"].items():
                core._tribe_unprocessed_griefs[tid] = [
                    UnprocessedGrief.from_dict(ug) for ug in ugs
                ]

        if "proto_chamanes" in data:
            core._proto_chamanes = dict(data["proto_chamanes"])

        if "chaman_hysteria" in data:
            core._chaman_hysteria = {
                tid: int(d) for tid, d in data["chaman_hysteria"].items()
            }

        if "archetype_streak" in data:
            core._archetype_streak = {
                tid: {arch: int(days) for arch, days in s.items()}
                for tid, s in data["archetype_streak"].items()
            }

        if "sacred_objects" in data:
            core._sacred_objects = [SacredObject.from_dict(o) for o in data["sacred_objects"]]

        if "objeto_cooldown" in data:
            core._objeto_cooldown = {k: int(v) for k, v in data["objeto_cooldown"].items()}

        if "social_roles" in data:
            core._social_roles = [SocialRole.from_dict(r) for r in data["social_roles"]]

        if "artifacts" in data:
            core.artifacts = ArtifactSystem.from_dict(data["artifacts"])

        if "emergent_lexicon" in data:
            core.emergent_lexicon = EmergentLexiconSystem.from_dict(data["emergent_lexicon"])

        return core

