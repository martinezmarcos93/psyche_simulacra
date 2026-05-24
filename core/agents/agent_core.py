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

    # ── Population management ─────────────────────────────────────────────────

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.id] = agent
        # Sincronizar nodo en red social
        self.social_network.add_agent(agent.id)

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

    def on_day(self, tp: TimePoint) -> None:
        """Called once per simulated day — runs death checks and social dynamics."""
        # 1. Decaimiento y evolución del campo memético global (Fase 7)
        self.collective_field.decay()

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

        # 3b. Orfandad: infantes cuyos dos padres han muerto
        for agent in list(self.agents.values()):
            if not agent.is_alive or not agent.es_infante or agent._padres is None:
                continue
            pa = self.agents.get(agent._padres[0])
            pb = self.agents.get(agent._padres[1])
            if (pa is None or not pa.is_alive) and (pb is None or not pb.is_alive):
                self._register_death(agent, tp, "orfandad")

        # 4. Envejecimiento anual (un año simulado = 365 días)
        if tp.dia_simulado > 0 and tp.dia_simulado % 365 == 0:
            for agent in self.agents.values():
                if agent.is_alive:
                    agent.edad += 1

        # 5. Decrementar cooldowns de reproducción
        for agent in self.agents.values():
            if agent.is_alive and agent._cooldown_reproduccion > 0:
                agent._cooldown_reproduccion -= 1

        # 6. Reproducción
        self._check_reproduccion(tp)

        # 7. Sueños nocturnos con entrelazamiento
        self._process_nightly_dreams(tp.dia_simulado)

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
        # La muerte sacude el campo tribal local
        local_field = self.tribe_manager.get_local_field(agent.id)
        if local_field is not None:
            local_field.absorb_event("muerte", intensity=0.8)

        # Registrar la muerte en la memoria cultural de la tribu
        tribe_id = self.tribe_manager.get_tribe_id(agent.id)
        if tribe_id:
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is not None:
                arch = agent.archetypes.dominant()
                arch_norm = "self_" if arch == "self" else arch
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

    def _check_reproduccion(self, tp: TimePoint) -> None:
        if len(self.agents) >= _LIMITE_POBLACION:
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

        # ── Herencia de memoria cultural: la CulturalMemory tribal empuja arquetipos ──
        tribe_id = self.tribe_manager.get_tribe_id(parent_a.id)
        if tribe_id:
            cmem = self.tribe_manager.cultural_memories.get(tribe_id)
            if cmem is not None:
                for arch_attr, delta in cmem.get_inheritance_effects().items():
                    current = getattr(child.archetypes, arch_attr, None)
                    if current is not None:
                        setattr(child.archetypes, arch_attr, max(0.0, min(1.0, current + delta)))

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
        for aid, agent in self.agents.items():
            if not agent.is_alive:
                continue
            bioma = "tierra"
            if terrain is not None:
                hx = terrain.get(*agent.posicion)
                if hx is not None:
                    bioma = hx.biome
            agent.bioma_actual = bioma
            agent._process_dream(
                dia,
                bioma             = bioma,
                resonancia_grupal = resonances.get(aid),
            )

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

        return core

