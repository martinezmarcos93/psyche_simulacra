"""
Catálogo de eventos del EventBus de PSYCHE SIMULACRA.
Cada evento es un dataclass inmutable que viaja por el bus.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.time.simulation_clock import TimePoint


# ── Eventos de mundo ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WorldTickEvent:
    tick:      int
    timepoint: "TimePoint"


@dataclass(frozen=True)
class WorldDayEvent:
    dia:     int
    season:  str
    climate: dict | None = None


@dataclass(frozen=True)
class WorldSeasonChangeEvent:
    old_season: str
    new_season: str
    dia:        int


@dataclass(frozen=True)
class ResourceDepletedEvent:
    hex_coord:     tuple[int, int]
    resource_type: str
    dia:           int


@dataclass(frozen=True)
class CatastropheEvent:
    tipo:           str
    severity:       float
    affected_hexes: tuple
    dia:            int


# ── Eventos de agentes ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AgentBornEvent:
    agent_id: str
    nombre:   str
    tribe_id: str
    dia:      int
    parents:  tuple[str, str] | None = None


@dataclass(frozen=True)
class AgentDiedEvent:
    agent_id: str
    nombre:   str
    tribe_id: str
    causa:    str
    dia:      int


@dataclass(frozen=True)
class AgentActionEvent:
    agent_id:    str
    action_type: str
    hex_coord:   tuple[int, int]
    tick:        int


@dataclass(frozen=True)
class AgentDreamEvent:
    agent_id:  str
    archetype: str
    symbol:    str
    dia:       int


@dataclass(frozen=True)
class AgentTraumaEvent:
    agent_id:    str
    trauma_type: str
    intensity:   float
    dia:         int


# ── Eventos sociales ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TribeFormedEvent:
    tribe_id:    str
    nombre:      str
    founder_ids: tuple
    dia:         int


@dataclass(frozen=True)
class TribeCollapsedEvent:
    tribe_id: str
    nombre:   str
    dia:      int
    causa:    str


@dataclass(frozen=True)
class SchismEvent:
    parent_tribe:  str
    new_tribe:     str
    dia:           int
    cause_agent_id: str


@dataclass(frozen=True)
class BondFormedEvent:
    agent_a:  str
    agent_b:  str
    strength: float
    dia:      int


# ── Eventos culturales ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MythCrystallizedEvent:
    tribe_id:      str
    myth_tipo:     str
    archetype_pair: tuple[str, str]
    dia:           int


@dataclass(frozen=True)
class DeityEmergedEvent:
    tribe_id:    str
    deity_nombre: str
    archetype:   str
    dia:         int


@dataclass(frozen=True)
class KnowledgeDiscoveredEvent:
    agent_id:  str
    knowledge: str
    tribe_id:  str
    dia:       int


@dataclass(frozen=True)
class KnowledgeExtinctEvent:
    knowledge: str
    dia:       int


@dataclass(frozen=True)
class SacredObjectCreatedEvent:
    obj_nombre: str
    tipo:       str
    creador_id: str
    dia:        int


@dataclass(frozen=True)
class SocialRoleAssignedEvent:
    tipo:       str
    portador_id: str
    tribe_id:   str
    dia:        int


@dataclass(frozen=True)
class NarrativeGeneratedEvent:
    tribe_id:     str
    tipo:         str
    texto_preview: str
    dia:          int


# ── Eventos Liminal ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LiminalAgentEnteredEvent:
    agent_id: str
    from_sim: str
    dia:      int


@dataclass(frozen=True)
class LiminalAgentReturnedEvent:
    agent_id: str
    to_sim:   str
    dia:      int


@dataclass(frozen=True)
class LiminalConnectionEvent:
    sim_id:    str
    connected: bool


# ── Eventos de runtime ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ServiceHealthEvent:
    service: str
    state:   str
    detail:  str


@dataclass(frozen=True)
class CheckpointSavedEvent:
    dia:      int
    filepath: str


@dataclass(frozen=True)
class SnapshotEmittedEvent:
    tick:              int
    snapshot_size_bytes: int
