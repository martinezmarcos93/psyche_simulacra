from __future__ import annotations

from typing import TYPE_CHECKING

from core.time import TimePoint
from core.interface import WorldAction
from .agent import Agent
from core.social.network import SocialNetwork
from core.social.interaction import InteractionEngine
from core.social.collective_field import CollectiveField
from core.social.mythology import MythologyEngine

if TYPE_CHECKING:
    from core.world import WorldCore


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

        # Inicialización de Capas de Sistemas Sociales (Fase 7)
        self.social_network     = SocialNetwork()
        self.interaction_engine = InteractionEngine()
        self.collective_field   = CollectiveField()
        self.mythology_engine   = MythologyEngine()

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
            if a.is_alive:
                pos_counts[a.posicion] = pos_counts.get(a.posicion, 0) + 1

        for agent in self.agents.values():
            if not agent.is_alive:
                continue
            agent.update_biological(tp, snapshot)
            hay_aliados = pos_counts.get(agent.posicion, 0) > 1
            # En la hora de interactuar, Agent usará la radiación del campo para collapse
            action = agent.decide_action(tp, snapshot, self.collective_field, hay_aliados)
            if action is not None:
                actions.append(action)

        # Resolución de interacciones sociales en la zona (Fase 7)
        self.interaction_engine.process_zone_interactions(
            self.agents,
            self.social_network,
            self.collective_field,
            self.mythology_engine,
            dia=tp.dia_simulado
        )

        # Propagación de entrelazamientos emocionales (Fase 7)
        self.social_network.propagate_entanglement(self.agents)

        if actions:
            self.world_ref.receive_actions(actions)

    def on_day(self, tp: TimePoint) -> None:
        """Called once per simulated day — runs death checks and social dynamics."""
        # 1. Decaimiento y evolución del campo memético (Fase 7)
        self.collective_field.decay()

        # 2. Cristalización y feedback mítico (Fase 7)
        self.mythology_engine.check_crystallization(self.collective_field, self.agents, tp.dia_simulado)
        self.mythology_engine.apply_myth_effects(self.agents)

        # 3. Control de vitalidad
        for agent in list(self.agents.values()):
            if not agent.is_alive:
                continue
            cause = agent.check_death()
            if cause is not None:
                agent.episodic_log.append(f"Día {tp.dia_simulado}: Falleció a causa de {cause}.")
                self._death_log.append({
                    "tick":     tp.tick,
                    "dia":      tp.dia_simulado,
                    "agent_id": agent.id,
                    "nombre":   agent.nombre,
                    "causa":    cause,
                })

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

    def to_dict(self) -> dict:
        return {
            "agents":    [a.to_dict() for a in self.agents.values()],
            "death_log": self._death_log,
            "social_network": self.social_network.to_dict(),
            "collective_field": self.collective_field.to_dict(),
            "mythology_engine": self.mythology_engine.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict, world_ref: WorldCore) -> AgentCore:
        core = cls(world_ref)
        for adict in data.get("agents", []):
            core.add_agent(Agent.from_dict(adict))
        core._death_log = data.get("death_log", [])

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

        return core

