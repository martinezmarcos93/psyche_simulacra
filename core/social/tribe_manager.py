from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

from .collective_field import CollectiveField
from .mythology import MythologyEngine

if TYPE_CHECKING:
    from core.agents import Agent
    from core.social.network import SocialNetwork
    from core.world.terrain import TerrainGrid

# Positive bond threshold to include an edge in the tribe graph
_MIN_BOND = 0.15
# How often to re-cluster (simulated days)
_RECLUSTER_INTERVAL = 30

# Archetype drift delta per day per tribe member based on home biome
# Key: biome name → {archetype_attr: delta}
BIOME_AFFINITIES: dict[str, dict[str, float]] = {
    "bosque_templado":   {"sabio": 0.0008, "madre": 0.0008},
    "pradera_humeda":    {"heroe": 0.0008, "self_": 0.0008},
    "rio_lago":          {"madre": 0.0010, "nino_divino": 0.0006},
    "montana_alta":      {"heroe": 0.0010, "sombra": 0.0008},
    "sabana_abierta":    {"gobernante": 0.0008, "heroe": 0.0006},
    "pantano_costero":   {"sombra": 0.0010, "trickster": 0.0008},
    "cueva":             {"sombra": 0.0010, "nino_divino": 0.0008},
    "valle_fertil":      {"madre": 0.0010, "self_": 0.0008},
    "costa_abierta":     {"rebelde": 0.0008, "anima_animus": 0.0008},
    "desierto_borde":    {"heroe": 0.0008, "padre": 0.0008},
    "colinas_suaves":    {"padre": 0.0008, "gobernante": 0.0006},
    "lago_interior":     {"madre": 0.0008, "sabio": 0.0008},
}

_ARCHETYPE_DISPLAY_ES: dict[str, str] = {
    "self_":        "del Self",
    "persona":      "de la Persona",
    "sombra":       "de la Sombra",
    "anima_animus": "del Ánima-Ánimus",
    "heroe":        "del Héroe",
    "sabio":        "del Sabio",
    "trickster":    "del Trickster",
    "madre":        "de la Madre",
    "padre":        "del Padre",
    "nino_divino":  "del Niño Divino",
    "gobernante":   "del Gobernante",
    "rebelde":      "del Rebelde",
}


class TribeManager:
    """
    Gestiona el clustering tribal, los campos colectivos locales (ICL),
    los motores de mitología por tribu y la divergencia cultural por bioma.
    """

    def __init__(self) -> None:
        self.tribes:          dict[str, list[str]]    = {}  # tribe_id → [agent_ids]
        self.agent_to_tribe:  dict[str, str]          = {}  # agent_id → tribe_id
        self.local_fields:    dict[str, CollectiveField]  = {}
        self.local_myths:     dict[str, MythologyEngine]  = {}
        self._last_recluster: int = -1

    # ── Clustering ────────────────────────────────────────────────────────────

    def update_tribes(
        self,
        agents:      dict[str, Agent],
        network:     SocialNetwork,
        current_day: int,
    ) -> None:
        """Re-clusteriza agentes en tribus usando detección de comunidades."""
        if self._last_recluster >= 0 and current_day - self._last_recluster < _RECLUSTER_INTERVAL:
            return
        self._last_recluster = current_day

        alive_ids = {aid for aid, a in agents.items() if a.is_alive}
        if not alive_ids:
            return

        # Grafo no dirigido con pesos de vínculo positivo
        G: nx.Graph = nx.Graph()
        G.add_nodes_from(alive_ids)
        for u, v, data in network.graph.edges(data=True):
            if u not in alive_ids or v not in alive_ids:
                continue
            b_uv = max(data.get("bond_strength", 0.0), 0.0)
            b_vu = max(network.get_bond(v, u), 0.0)
            w = (b_uv + b_vu) / 2.0
            if w >= _MIN_BOND:
                if G.has_edge(u, v):
                    G[u][v]["weight"] = max(G[u][v]["weight"], w)
                else:
                    G.add_edge(u, v, weight=w)

        # Detectar comunidades (solo nodos con al menos un enlace fuerte)
        connected = {n for n in alive_ids if G.degree(n) > 0}
        isolates  = alive_ids - connected

        communities: list[frozenset[str]] = []
        if connected:
            G_conn = G.subgraph(connected).copy()
            try:
                raw = nx.community.greedy_modularity_communities(G_conn, weight="weight")
                communities = [frozenset(c) for c in raw]
            except Exception:
                communities = [frozenset(connected)]

        for aid in isolates:
            communities.append(frozenset({aid}))

        # Construir nuevos mapeos (tribe_id = primer ID ordenado de la comunidad)
        new_tribes:         dict[str, list[str]] = {}
        new_agent_to_tribe: dict[str, str]       = {}

        for community in communities:
            tribe_id = f"tribe_{sorted(community)[0]}"
            new_tribes[tribe_id] = sorted(community)
            for aid in community:
                new_agent_to_tribe[aid] = tribe_id

        # Mantener campos históricos para IDs que persisten; crear para los nuevos
        for tribe_id in new_tribes:
            if tribe_id not in self.local_fields:
                self.local_fields[tribe_id] = CollectiveField()
            if tribe_id not in self.local_myths:
                self.local_myths[tribe_id] = MythologyEngine()

        # Eliminar tribus extintas
        for old_id in set(self.tribes) - set(new_tribes):
            self.local_fields.pop(old_id, None)
            self.local_myths.pop(old_id, None)

        self.tribes         = new_tribes
        self.agent_to_tribe = new_agent_to_tribe

    # ── Acceso a campos locales ───────────────────────────────────────────────

    def get_local_field(self, agent_id: str) -> CollectiveField | None:
        tid = self.agent_to_tribe.get(agent_id)
        return self.local_fields.get(tid) if tid else None

    def get_tribe_id(self, agent_id: str) -> str | None:
        return self.agent_to_tribe.get(agent_id)

    def same_tribe(self, id_a: str, id_b: str) -> bool:
        ta = self.agent_to_tribe.get(id_a)
        return ta is not None and ta == self.agent_to_tribe.get(id_b)

    def get_tribe_display_name(self, tribe_id: str, agents: dict[str, Agent]) -> str:
        members = self.tribes.get(tribe_id, [])
        best_val = -1.0
        dom_attr = "heroe"
        for aid in members:
            agent = agents.get(aid)
            if agent is None or not agent.is_alive:
                continue
            raw = agent.archetypes.dominant()
            attr = "self_" if raw == "self" else raw
            val = getattr(agent.archetypes, attr, 0.0)
            if val > best_val:
                best_val = val
                dom_attr = attr
        label = _ARCHETYPE_DISPLAY_ES.get(dom_attr, dom_attr)
        return f"Tribu {label}"

    # ── Actualización diaria ──────────────────────────────────────────────────

    def on_day(
        self,
        agents:       dict[str, Agent],
        network:      SocialNetwork,
        global_field: CollectiveField,
        terrain:      TerrainGrid | None,
        day:          int,
    ) -> None:
        """Mecánicas tribales diarias: re-clustering, decaimiento, mitos, deriva cultural."""
        # 1. Re-clustering
        self.update_tribes(agents, network, day)

        # 2. Decaimiento de campos locales
        for field in self.local_fields.values():
            field.decay()

        # 3. Mitología local por tribu
        for tribe_id, myth_engine in self.local_myths.items():
            member_ids = self.tribes.get(tribe_id, [])
            tribe_agents = {aid: agents[aid] for aid in member_ids if aid in agents}
            local_field  = self.local_fields.get(tribe_id)
            if local_field and tribe_agents:
                # check_crystallization → on_day() ya incluye apply_myth_effects()
                myth_engine.check_crystallization(local_field, tribe_agents, day)

        # 4. Deriva arquetípica por bioma
        if terrain is not None:
            self._apply_biome_drift(agents, terrain)

    def _apply_biome_drift(
        self,
        agents:  dict[str, Agent],
        terrain: TerrainGrid,
    ) -> None:
        """Empuja levemente los arquetipos de cada miembro hacia las afinidades de su bioma tribal."""
        for tribe_id, member_ids in self.tribes.items():
            # Calcular bioma dominante de la tribu
            biome_counts: dict[str, int] = {}
            for aid in member_ids:
                agent = agents.get(aid)
                if agent is None or not agent.is_alive:
                    continue
                hex_cell = terrain.get(*agent.posicion)
                if hex_cell is not None:
                    b = hex_cell.biome
                    biome_counts[b] = biome_counts.get(b, 0) + 1

            if not biome_counts:
                continue
            home_biome = max(biome_counts, key=biome_counts.__getitem__)
            affinities = BIOME_AFFINITIES.get(home_biome, {})
            if not affinities:
                continue

            for aid in member_ids:
                agent = agents.get(aid)
                if agent is None or not agent.is_alive or agent.es_infante:
                    continue
                for arch_attr, delta in affinities.items():
                    current = getattr(agent.archetypes, arch_attr, None)
                    if current is not None:
                        setattr(agent.archetypes, arch_attr, min(1.0, current + delta))

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "tribes":          {k: list(v) for k, v in self.tribes.items()},
            "agent_to_tribe":  dict(self.agent_to_tribe),
            "local_fields":    {k: v.to_dict() for k, v in self.local_fields.items()},
            "local_myths":     {k: v.to_dict() for k, v in self.local_myths.items()},
            "last_recluster":  self._last_recluster,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TribeManager:
        tm = cls()
        tm.tribes          = {k: list(v) for k, v in data.get("tribes", {}).items()}
        tm.agent_to_tribe  = dict(data.get("agent_to_tribe", {}))
        tm._last_recluster = data.get("last_recluster", -1)
        for k, fd in data.get("local_fields", {}).items():
            tm.local_fields[k] = CollectiveField.from_dict(fd)
        for k, md in data.get("local_myths", {}).items():
            tm.local_myths[k] = MythologyEngine.from_dict(md)
        return tm
