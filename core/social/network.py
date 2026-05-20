from __future__ import annotations

import networkx as nx
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents import Agent

DEFAULT_EDGE_ATTRS = {
    "bond_strength": 0.0,
    "intimacy": 0.0,
    "dependency": 0.0,
    "resonance": 0.0,
    "alignment": 0.0,
    "entangled": False,
}


class SocialNetwork:
    """
    Grafo único dirigido (Multi-layered a través de atributos de arcos) que
    representa la red social y emocional de los agentes en la simulación.
    Utiliza NetworkX para el almacenamiento y análisis eficiente de la estructura.
    """

    def __init__(self, agent_ids: list[str] | None = None) -> None:
        self.graph = nx.DiGraph()
        if agent_ids:
            for aid in agent_ids:
                self.add_agent(aid)

    # ── Gestión de Nodos ──────────────────────────────────────────────────────

    def add_agent(self, agent_id: str) -> None:
        if not self.graph.has_node(agent_id):
            self.graph.add_node(agent_id)

    def remove_agent(self, agent_id: str) -> None:
        if self.graph.has_node(agent_id):
            self.graph.remove_node(agent_id)

    # ── Gestión de Arcos y Atributos ──────────────────────────────────────────

    def _ensure_edge(self, u: str, v: str) -> None:
        """Asegura que exista el arco u -> v con los atributos por defecto."""
        self.add_agent(u)
        self.add_agent(v)
        if not self.graph.has_edge(u, v):
            self.graph.add_edge(u, v, **dict(DEFAULT_EDGE_ATTRS))

    def get_bond(self, u: str, v: str) -> float:
        """Retorna la fuerza del vínculo emocional u -> v (entre -1.0 y 1.0)."""
        if not self.graph.has_edge(u, v):
            return 0.0
        return self.graph[u][v].get("bond_strength", 0.0)

    def set_bond(self, u: str, v: str, value: float) -> None:
        """Establece la fuerza del vínculo emocional u -> v, recortándolo a [-1, 1]."""
        self._ensure_edge(u, v)
        self.graph[u][v]["bond_strength"] = max(-1.0, min(1.0, float(value)))

    def modify_bond(self, u: str, v: str, delta: float) -> None:
        """Modifica la fuerza del vínculo emocional u -> v sumando un delta y recortando."""
        self._ensure_edge(u, v)
        current = self.graph[u][v].get("bond_strength", 0.0)
        self.set_bond(u, v, current + delta)

    def get_attribute(self, u: str, v: str, attr: str) -> float | bool:
        """Retorna el valor de un atributo específico del arco u -> v."""
        if not self.graph.has_edge(u, v):
            return DEFAULT_EDGE_ATTRS.get(attr, 0.0)
        return self.graph[u][v].get(attr, DEFAULT_EDGE_ATTRS.get(attr, 0.0))

    def set_attribute(self, u: str, v: str, attr: str, value: float | bool) -> None:
        """Establece el valor de un atributo del arco u -> v, limitándolo al rango correcto."""
        self._ensure_edge(u, v)
        if attr == "entangled":
            self.graph[u][v]["entangled"] = bool(value)
        elif attr == "bond_strength":
            self.set_bond(u, v, float(value))
        else:
            # Los demás atributos del roadmap técnico van de 0.0 a 1.0
            self.graph[u][v][attr] = max(0.0, min(1.0, float(value)))

    def entangle(self, u: str, v: str) -> None:
        """Entrelaza cuánticamente a dos agentes (bidireccional)."""
        self._ensure_edge(u, v)
        self._ensure_edge(v, u)
        self.graph[u][v]["entangled"] = True
        self.graph[v][u]["entangled"] = True

    def are_entangled(self, u: str, v: str) -> bool:
        """Verifica si u y v están entrelazados."""
        if not self.graph.has_edge(u, v) or not self.graph.has_edge(v, u):
            return False
        return bool(self.graph[u][v].get("entangled", False) or self.graph[v][u].get("entangled", False))

    # ── Dinámica Cuántica ─────────────────────────────────────────────────────

    def propagate_entanglement(self, agents: dict[str, Agent], rate: float = 0.05) -> None:
        """
        Propaga los cambios emocionales (humor, ansiedad, energía) de forma bidireccional
        entre parejas de agentes entrelazados cuánticamente.
        """
        entangled_pairs = set()
        for u, v, data in self.graph.edges(data=True):
            if data.get("entangled", False):
                pair = tuple(sorted([u, v]))
                entangled_pairs.add(pair)

        for u, v in entangled_pairs:
            if u in agents and v in agents:
                au = agents[u]
                av = agents[v]
                if au.is_alive and av.is_alive:
                    # Sincronización termodinámica de humor
                    diff_hum = au.humor - av.humor
                    au.humor = max(0.0, min(1.0, au.humor - diff_hum * rate))
                    av.humor = max(0.0, min(1.0, av.humor + diff_hum * rate))

                    # Sincronización de ansiedad
                    diff_ans = au.ansiedad - av.ansiedad
                    au.ansiedad = max(0.0, min(1.0, au.ansiedad - diff_ans * rate))
                    av.ansiedad = max(0.0, min(1.0, av.ansiedad + diff_ans * rate))

                    # Sincronización de energía
                    diff_ene = au.energia - av.energia
                    au.energia = max(0.0, min(1.0, au.energia - diff_ene * rate))
                    av.energia = max(0.0, min(1.0, av.energia + diff_ene * rate))

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "nodes": list(self.graph.nodes),
            "edges": [
                {
                    "u": u,
                    "v": v,
                    "bond_strength": data.get("bond_strength", 0.0),
                    "intimacy": data.get("intimacy", 0.0),
                    "dependency": data.get("dependency", 0.0),
                    "resonance": data.get("resonance", 0.0),
                    "alignment": data.get("alignment", 0.0),
                    "entangled": data.get("entangled", False),
                }
                for u, v, data in self.graph.edges(data=True)
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> SocialNetwork:
        net = cls()
        for node in data.get("nodes", []):
            net.add_agent(node)
        for edge in data.get("edges", []):
            u = edge["u"]
            v = edge["v"]
            net.graph.add_edge(
                u, v,
                bond_strength = edge.get("bond_strength", 0.0),
                intimacy      = edge.get("intimacy", 0.0),
                dependency    = edge.get("dependency", 0.0),
                resonance     = edge.get("resonance", 0.0),
                alignment     = edge.get("alignment", 0.0),
                entangled     = edge.get("entangled", False),
            )
        return net
