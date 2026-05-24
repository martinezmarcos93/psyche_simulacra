import pytest
import os
import tempfile
from core.time import TimePoint
from core.agents.agent import Agent
from core.agents.agent_core import AgentCore
from core.social.network import SocialNetwork
from core.social.collective_field import CollectiveField
from core.social.mythology import MythologyEngine, MythCrystal, ProtoMito
from core.social.interaction import InteractionEngine
from core.world import WorldCore
from core.simulation import SimulationRunner

# 1. test_social_network_structure
def test_social_network_structure():
    net = SocialNetwork()
    net.add_agent("agent_a")
    net.add_agent("agent_b")
    
    # Check default attributes
    assert net.get_bond("agent_a", "agent_b") == 0.0
    assert net.get_attribute("agent_a", "agent_b", "intimacy") == 0.0
    assert net.get_attribute("agent_a", "agent_b", "entangled") is False

    # Modify and check
    net.set_bond("agent_a", "agent_b", 0.5)
    assert net.get_bond("agent_a", "agent_b") == 0.5
    
    net.set_attribute("agent_a", "agent_b", "intimacy", 0.8)
    assert net.get_attribute("agent_a", "agent_b", "intimacy") == 0.8
    
    net.modify_bond("agent_a", "agent_b", -0.2)
    assert net.get_bond("agent_a", "agent_b") == 0.3
    
    # Node Syncing / Removal
    net.remove_agent("agent_b")
    assert "agent_b" not in net.graph.nodes
    # Verify getting bond after node is removed returns 0.0 safely
    assert net.get_bond("agent_a", "agent_b") == 0.0

# 2. test_emotional_entanglement_propagation
def test_emotional_entanglement_propagation():
    net = SocialNetwork()
    agent_a = Agent("a", "Agent A", (0, 0), seed=42)
    agent_b = Agent("b", "Agent B", (0, 0), seed=43)
    agents = {"a": agent_a, "b": agent_b}
    
    # Establish entanglement
    net.entangle("a", "b")
    assert net.are_entangled("a", "b") is True
    
    # Set different emotional levels
    agent_a.humor = 0.8
    agent_b.humor = 0.2
    
    agent_a.ansiedad = 0.1
    agent_b.ansiedad = 0.9
    
    agent_a.energia = 0.9
    agent_b.energia = 0.3
    
    # Propagate (thermodynamic relaxation)
    net.propagate_entanglement(agents, rate=0.1)
    
    # Check that they moved closer to each other's state
    # Diff_hum = 0.8 - 0.2 = 0.6. rate=0.1 => delta = 0.06
    # a.humor = 0.8 - 0.06 = 0.74, b.humor = 0.2 + 0.06 = 0.26
    assert abs(agent_a.humor - 0.74) < 1e-5
    assert abs(agent_b.humor - 0.26) < 1e-5
    
    # Diff_ans = 0.1 - 0.9 = -0.8. rate=0.1 => delta = -0.08
    # a.ansiedad = 0.1 - (-0.08) = 0.18, b.ansiedad = 0.9 + (-0.08) = 0.82
    assert abs(agent_a.ansiedad - 0.18) < 1e-5
    assert abs(agent_b.ansiedad - 0.82) < 1e-5

# 3. test_interaction_engine_resolution
def test_interaction_engine_resolution():
    engine = InteractionEngine()
    net = SocialNetwork()
    field = CollectiveField()
    
    agent_a = Agent("a", "Agent A", (0, 0), seed=1)
    agent_b = Agent("b", "Agent B", (0, 0), seed=2)
    
    # Case 1: Cooperate - Cooperate
    agent_a.behavioral_state.ultimo_colapso = "cooperacion"
    agent_b.behavioral_state.ultimo_colapso = "cooperacion"
    agent_a.humor = 0.5
    agent_b.humor = 0.5
    agent_a.ansiedad = 0.5
    agent_b.ansiedad = 0.5
    net.set_bond("a", "b", 0.0)
    net.set_bond("b", "a", 0.0)
    
    engine.resolve_encounter(agent_a, agent_b, net, field)
    
    assert net.get_bond("a", "b") == 0.08
    assert net.get_bond("b", "a") == 0.08
    assert agent_a.humor == 0.55
    assert agent_a.ansiedad == 0.45
    assert field.symbols["heroe"] == 0.08
    assert field.symbols["madre"] == 0.04
    assert field.emotional_pressure == 0.0 # Decays or drops below 0 is capped at 0.0
    
    # Case 2: Cooperate - Compete (exploitation)
    agent_a.behavioral_state.ultimo_colapso = "cooperacion"
    agent_b.behavioral_state.ultimo_colapso = "competencia"
    agent_a.humor = 0.5
    agent_b.humor = 0.5
    agent_a.ansiedad = 0.5
    agent_b.ansiedad = 0.5
    net.set_bond("a", "b", 0.0)
    net.set_bond("b", "a", 0.0)
    
    # Ensure food is available for transfer
    agent_a.needs.hambre = 0.2
    agent_b.needs.hambre = 0.8
    
    engine.resolve_encounter(agent_a, agent_b, net, field)
    
    assert net.get_bond("a", "b") == -0.18  # Victim's bond drop
    assert net.get_bond("b", "a") == -0.02  # Exploiter's bond drop
    assert agent_a.humor == 0.38            # 0.5 - 0.12
    assert agent_a.ansiedad == 0.65         # 0.5 + 0.15
    assert agent_b.humor == 0.55            # 0.5 + 0.05
    assert agent_a.needs.hambre == 0.35     # 0.2 + 0.15
    assert agent_b.needs.hambre == 0.65     # 0.8 - 0.15
    assert field.symbols["sombra"] == 0.10
    
    # Case 3: Compete - Compete (Violent clash)
    agent_a.behavioral_state.ultimo_colapso = "competencia"
    agent_b.behavioral_state.ultimo_colapso = "competencia"
    agent_a.humor = 0.5
    agent_b.humor = 0.5
    agent_a.ansiedad = 0.5
    agent_b.ansiedad = 0.5
    net.set_bond("a", "b", 0.0)
    net.set_bond("b", "a", 0.0)
    
    engine.resolve_encounter(agent_a, agent_b, net, field)
    assert net.get_bond("a", "b") == -0.22
    assert net.get_bond("b", "a") == -0.22
    assert agent_a.humor == 0.35
    assert agent_a.ansiedad == 0.70
    assert field.symbols["sombra"] == 0.28   # 0.10 + 0.18
    
    # Case 4: Isolation (No interaction)
    agent_a.behavioral_state.ultimo_colapso = "aislamiento"
    agent_b.behavioral_state.ultimo_colapso = "cooperacion"
    net.set_bond("a", "b", 0.0)
    net.set_bond("b", "a", 0.0)
    
    engine.resolve_encounter(agent_a, agent_b, net, field)
    assert net.get_bond("a", "b") == 0.0
    assert net.get_bond("b", "a") == 0.0

# 4. test_collective_field_decay_and_radiation
def test_collective_field_decay_and_radiation():
    field = CollectiveField()
    field.symbols["heroe"] = 0.8
    field.symbols["sombra"] = 0.6
    field.symbols["trickster"] = 0.4
    field.emotional_pressure = 0.5
    
    # Radiate bias influence
    rad = field.radiate()
    # "cooperacion": (0.8 + 0.0) * 0.25 - 0.5 * 0.10 = 0.2 - 0.05 = 0.15
    # "competencia": 0.6 * 0.20 + 0.5 * 0.25 = 0.12 + 0.125 = 0.245
    # "aislamiento": 0.5 * 0.20 + 0.6 * 0.15 = 0.10 + 0.09 = 0.19
    # "manipulacion": 0.4 * 0.25 = 0.10
    assert abs(rad["cooperacion"] - 0.15) < 1e-5
    assert abs(rad["competencia"] - 0.245) < 1e-5
    assert abs(rad["aislamiento"] - 0.19) < 1e-5
    assert abs(rad["manipulacion"] - 0.10) < 1e-5
    
    # Decay with rate=0.02
    field.decay(rate=0.02)
    assert abs(field.symbols["heroe"] - 0.8 * 0.98) < 1e-5
    assert abs(field.emotional_pressure - 0.5 * 0.98) < 1e-5

# 5. test_mythology_crystallization
def test_mythology_crystallization():
    engine = MythologyEngine()
    field = CollectiveField()
    
    agent_h = Agent("hero_agent", "Hero", (0, 0), seed=1)
    agent_m = Agent("monster_agent", "Monster", (0, 0), seed=2)
    
    # Setup archetypes
    agent_h.archetypes.heroe = 0.85
    agent_m.archetypes.sombra = 0.90
    
    agents = {"hero_agent": agent_h, "monster_agent": agent_m}
    
    # Test checking crystallization before thresholds are met
    engine.check_crystallization(field, agents, dia=1)
    assert len(engine.get_active_myths()) == 0

    # Set thresholds and pre-load a proto-myth with enough coherencia to crystallize
    field.symbols["heroe"] = 0.80
    field.symbols["sombra"] = 0.70
    engine.proto_myths.append(ProtoMito(
        tipo="mito_moral", par=("heroe", "sombra"), coherencia=5.0, dia_origen=0,
        intensidad_contexto=0.80,  # intensidad_cristal = min(1.0, 0.80+0.20) = 1.0
    ))

    # Crystallize! — the generated name is "{tipo}_dia{n}"
    engine.check_crystallization(field, agents, dia=1)
    active = engine.get_active_myths()
    assert len(active) == 1
    assert active[0].tipo == "mito_moral"
    assert engine.is_myth_active(active[0].name) is True

    hero_id, monster_id = engine.get_myth_hero_monster()
    assert hero_id == "hero_agent"
    assert monster_id == "monster_agent"
    
    # Apply feedback effects
    agent_h.humor = 0.5
    agent_h.ansiedad = 0.5
    agent_m.humor = 0.5
    agent_m.ansiedad = 0.5
    
    engine.apply_myth_effects(agents)
    
    # Hero gets bonifications: humor +0.05, ansiedad -0.05
    assert agent_h.humor == 0.55
    assert agent_h.ansiedad == 0.45
    
    # Monster gets penalties: humor -0.05, ansiedad +0.08
    assert agent_m.humor == 0.45
    assert agent_m.ansiedad == 0.58

# 6. test_social_integration_and_serialization
def test_social_integration_and_serialization():
    # Setup agent core
    world = WorldCore(seed=42)
    core = AgentCore(world)
    
    agent_a = Agent("a", "Agent A", (0, 0), seed=1)
    agent_b = Agent("b", "Agent B", (0, 0), seed=2)
    
    core.add_agent(agent_a)
    core.add_agent(agent_b)
    
    # Mutate social state
    core.social_network.set_bond("a", "b", 0.7)
    core.social_network.entangle("a", "b")
    core.collective_field.symbols["heroe"] = 0.65
    core.collective_field.emotional_pressure = 0.45
    
    core.mythology_engine.active_myths.append(MythCrystal(
        name="heroe_vs_monstruo",
        tipo="mito_moral",
        par=("heroe", "sombra"),
        active=True,
        day_crystallized=3,
        protagonista_id="a",
        antagonista_id="b",
    ))
    
    # Serialize to dict
    serialized = core.to_dict()
    
    # Restore to new agent core
    core2 = AgentCore.from_dict(serialized, world)
    
    # Verify exact match
    assert core2.social_network.get_bond("a", "b") == 0.7
    assert core2.social_network.are_entangled("a", "b") is True
    assert core2.collective_field.symbols["heroe"] == 0.65
    assert core2.collective_field.emotional_pressure == 0.45
    assert core2.mythology_engine.is_myth_active("heroe_vs_monstruo") is True
    hero_id, monster_id = core2.mythology_engine.get_myth_hero_monster()
    assert hero_id == "a"
    assert monster_id == "b"
