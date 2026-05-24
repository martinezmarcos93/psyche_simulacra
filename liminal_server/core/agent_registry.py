"""
core/agent_registry.py — Registro de agentes presentes en la Zona Liminal.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class LiminalAgent:
    agent_id:        str
    nombre:          str
    from_sim:        str
    pos:             tuple[int, int]
    archetypes:      dict
    traits:          dict
    arrived_at:      float = field(default_factory=time.monotonic)
    arrived_at_tick: int   = 0   # tick liminal al momento de llegada
    encounters:      list  = field(default_factory=list)  # encuentros cross-sim registrados

    @property
    def dominant_archetype(self) -> str:
        if not self.archetypes:
            return "desconocido"
        return max(self.archetypes, key=lambda k: self.archetypes[k])


class AgentRegistry:
    """Mantiene el estado de todos los agentes actualmente en la Zona Liminal."""

    def __init__(self) -> None:
        self._agents: dict[str, LiminalAgent] = {}

    def register(
        self,
        agent_id:        str,
        nombre:          str,
        from_sim:        str,
        pos:             tuple[int, int],
        archetypes:      dict,
        traits:          dict,
        arrived_at_tick: int = 0,
    ) -> LiminalAgent:
        agent = LiminalAgent(
            agent_id=agent_id,
            nombre=nombre,
            from_sim=from_sim,
            pos=pos,
            archetypes=archetypes,
            traits=traits,
            arrived_at_tick=arrived_at_tick,
        )
        self._agents[agent_id] = agent
        return agent

    def get(self, agent_id: str) -> LiminalAgent | None:
        return self._agents.get(agent_id)

    def remove(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)

    def all(self) -> list[LiminalAgent]:
        return list(self._agents.values())

    def by_sim(self, sim_id: str) -> list[LiminalAgent]:
        return [a for a in self._agents.values() if a.from_sim == sim_id]

    def count(self) -> int:
        return len(self._agents)
