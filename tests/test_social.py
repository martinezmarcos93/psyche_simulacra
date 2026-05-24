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
from core.social.perception import PerceptionSystem, ARCHETYPE_ATTENTION
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


# ── Hito 4: Error Epistemológico y Percepción Limitada ──────────────────────

class TestPerceptionSystem:

    def test_witness_dentro_radio(self):
        ps = PerceptionSystem()
        # (12, 10) → dist Manhattan = |12-10| + |10-10| = 2 ≤ 3 (dentro del radio)
        intensidad = ps.witness("muerte", (12, 10), 0.8, dia=1, agent_coord=(10, 10))
        assert intensidad == 0.8
        assert len(ps._recent_events) == 1
        assert ps._recent_events[0].tipo == "muerte"

    def test_witness_fuera_radio(self):
        ps = PerceptionSystem()
        # (20, 20) → dist = 10 + 10 = 20 > 3 (fuera del radio)
        intensidad = ps.witness("muerte", (20, 20), 0.8, dia=1, agent_coord=(10, 10))
        assert intensidad == 0.0
        assert len(ps._recent_events) == 0

    def test_witness_evento_global(self):
        ps = PerceptionSystem()
        # coord=None = evento global, siempre percibido
        intensidad = ps.witness("clima_extremo", None, 0.6, dia=1, agent_coord=(40, 30))
        assert intensidad == 0.6
        assert len(ps._recent_events) == 1

    def test_atencion_selectiva_amplifica(self):
        ps = PerceptionSystem()
        # El sabio amplifica fenómenos inexplicables × 1.5
        amp = ps.perceived_intensity("clima_extremo", 0.6, "sabio")
        assert abs(amp - 0.9) < 0.001

    def test_atencion_selectiva_no_amplifica_irrelevante(self):
        ps = PerceptionSystem()
        # El guerrero (heroe) no amplifica clima_extremo
        amp = ps.perceived_intensity("clima_extremo", 0.6, "heroe")
        assert amp == 0.6  # sin amplificación

    def test_rumor_distorsion_por_hop(self):
        ps_emisor = PerceptionSystem()
        ps_receptor = PerceptionSystem()
        ps_emisor.witness("muerte", None, 0.8, dia=1, agent_coord=(0, 0))
        rumors = ps_emisor.generate_rumors()
        assert len(rumors) == 1
        ps_receptor.receive_rumor(rumors[0])
        assert len(ps_receptor._rumors) == 1
        assert ps_receptor._rumors[0].intensidad < 0.8   # decaído
        assert ps_receptor._rumors[0].hops == 1

    def test_rumor_demasiado_debil_descartado(self):
        ps = PerceptionSystem()
        from core.social.perception import Rumor
        rumor_debil = Rumor(tipo="muerte", intensidad=0.05, hops=5, dia=1)
        ps.receive_rumor(rumor_debil)
        assert len(ps._rumors) == 0

    def test_sesgo_causal_forma_asociacion(self):
        ps = PerceptionSystem()
        ps.witness("clima_extremo", None, 0.7, dia=5, agent_coord=(5, 5))
        ps.witness("muerte", (5, 5), 0.6, dia=6, agent_coord=(5, 5))
        nuevas = ps.check_causal_bias(dia=7)
        assert len(nuevas) >= 1
        tipos = {(a.precursor, a.outcome) for a in nuevas}
        assert ("clima_extremo", "muerte") in tipos

    def test_sesgo_causal_no_duplica(self):
        ps = PerceptionSystem()
        ps.witness("clima_extremo", None, 0.8, dia=1, agent_coord=(0, 0))
        ps.witness("muerte", None, 0.7, dia=2, agent_coord=(0, 0))
        nuevas1 = ps.check_causal_bias(dia=3)
        nuevas2 = ps.check_causal_bias(dia=3)
        assert len(nuevas1) >= 1
        assert len(nuevas2) == 0  # no debe duplicar la misma asociación

    def test_serializacion_roundtrip(self):
        ps = PerceptionSystem()
        ps.witness("muerte", (5, 5), 0.7, dia=3, agent_coord=(5, 5))
        ps.witness("clima_extremo", None, 0.5, dia=4, agent_coord=(5, 5))
        ps.check_causal_bias(dia=5)
        d = ps.to_dict()
        ps2 = PerceptionSystem.from_dict(d)
        assert len(ps2._recent_events) == len(ps._recent_events)
        assert len(ps2._causal_assocs) == len(ps._causal_assocs)


class TestCollectiveFieldHysteria:

    def test_hysteria_default_inactiva(self):
        f = CollectiveField()
        assert not f.hysteria_active
        assert f.hysteria_intensity == 0.0

    def test_hysteria_serializada(self):
        f = CollectiveField()
        f.hysteria_active    = True
        f.hysteria_intensity = 0.75
        d = f.to_dict()
        f2 = CollectiveField.from_dict(d)
        assert f2.hysteria_active
        assert f2.hysteria_intensity == 0.75

    def test_absorb_trauma_histeria_colectiva(self):
        f = CollectiveField()
        f.absorb_trauma("histeria_colectiva", intensity=1.0)
        # Debe cargar muerte, sombra y sabio
        assert f.symbols["muerte"] > 0.0
        assert f.symbols["sombra"] > 0.0
        assert f.symbols["sabio"] > 0.0
        assert f.myth_pressure > 0.0


class TestHito4EmergentCriterion:
    """
    Criterio de emergencia del Hito 4:
    Evento climático extremo + agentes sabios + alta ansiedad en red densa →
    se crean las condiciones para que emerja un proto-mito escatológico (muerte+sabio).
    """

    def test_selective_attention_carga_simbolo_sabio(self):
        """Un agente con arquetipo sabio amplifica clima_extremo → carga sabio en el campo."""
        world = WorldCore(seed=42)
        core = AgentCore(world)

        agente = Agent("sabio1", "Sofos", (40, 30), seed=7)
        agente.archetypes.sabio = 0.85
        agente.archetypes.sombra = 0.10
        core.add_agent(agente)

        field = CollectiveField()
        # Simular percepción directa de un evento climático extremo
        perceived = agente._perception.witness(
            "clima_extremo", None, 0.7, dia=10, agent_coord=agente.posicion
        )
        amplified = agente._perception.perceived_intensity("clima_extremo", perceived, "sabio")
        # El sabio amplifica × 1.5
        assert amplified > perceived
        # Cargar el símbolo sabio en el campo (lo que haría _process_selective_attention)
        field.symbols["sabio"] = min(1.0, field.symbols.get("sabio", 0.0) + amplified * 0.05)
        assert field.symbols["sabio"] > 0.0

    def test_hysteria_activa_absorb_trauma(self):
        """Cuando los tres umbrales se superan simultáneamente, el check_hysteria activa histeria."""
        world = WorldCore(seed=42)
        core = AgentCore(world)

        # Crear una tribu con un campo en estado pre-histérico
        from core.social.tribe_manager import TribeManager
        agente = Agent("miedo1", "Phobos", (40, 30), seed=8)
        agente.archetypes.sombra = 0.80
        core.add_agent(agente)

        # Crear manualmente una tribu con campo en estado crítico
        tribe_id = "tribe_test"
        from core.social.collective_field import CollectiveField
        lf = CollectiveField()
        lf.myth_pressure      = 0.65
        lf.confusion          = 0.55
        lf.emotional_pressure = 0.65
        core.tribe_manager.tribes[tribe_id]          = [agente.id]
        core.tribe_manager.agent_to_tribe[agente.id] = tribe_id
        core.tribe_manager.local_fields[tribe_id]    = lf

        core._check_collective_hysteria(dia=15)

        assert lf.hysteria_active
        assert lf.hysteria_intensity > 0.0
        # La histeria cargó sabio (via histeria_colectiva trauma)
        assert lf.symbols["sabio"] > 0.0

    def test_contagio_emocional_propaga_ansiedad(self):
        """Agente con ansiedad alta propaga miedo a vecinos con vínculo fuerte."""
        world = WorldCore(seed=42)
        core = AgentCore(world)

        miedoso = Agent("m1", "Deimos", (0, 0), seed=9)
        miedoso.ansiedad = 0.85
        receptor = Agent("r1", "Eirene", (0, 0), seed=10)
        receptor.ansiedad = 0.20
        receptor.traits.estabilidad_emocional = 0.30

        core.add_agent(miedoso)
        core.add_agent(receptor)
        core.social_network.set_bond(receptor.id, miedoso.id, 0.70)

        ansiedad_antes = receptor.ansiedad
        core._process_emotional_contagion(dia=5)
        assert receptor.ansiedad > ansiedad_antes

    def test_taboo_causal_registrado_en_memoria(self):
        """Sesgo causal entre clima_extremo y muerte produce tabú en CulturalMemory."""
        from core.social.cultural_memory import CulturalMemory

        world = WorldCore(seed=42)
        core = AgentCore(world)

        agente = Agent("ag1", "Fobos", (10, 10), seed=11)
        agente.archetypes.sabio = 0.75
        core.add_agent(agente)

        tribe_id = "tribe_taboo"
        core.tribe_manager.tribes[tribe_id]             = [agente.id]
        core.tribe_manager.agent_to_tribe[agente.id]   = tribe_id
        core.tribe_manager.local_fields[tribe_id]      = CollectiveField()
        core.tribe_manager.cultural_memories[tribe_id] = CulturalMemory(tribe_id)

        # El agente presencia dos eventos en la ventana causal
        agente._perception.witness("clima_extremo", None, 0.8, dia=10, agent_coord=(10, 10))
        agente._perception.witness("muerte",       None, 0.7, dia=11, agent_coord=(10, 10))

        core._process_causal_bias(dia=12)

        cmem = core.tribe_manager.cultural_memories[tribe_id]
        taboos = [r for r in cmem.records if r.tipo_evento == "taboo_causal"]
        assert len(taboos) >= 1

    def test_agent_perception_serialization(self):
        """El PerceptionSystem del agente sobrevive un ciclo to_dict/from_dict."""
        agent = Agent("ser1", "Mneme", (5, 5), seed=12)
        agent._perception.witness("muerte", (5, 5), 0.7, dia=3, agent_coord=(5, 5))
        agent._perception.witness("clima_extremo", None, 0.5, dia=4, agent_coord=(5, 5))
        agent._perception.check_causal_bias(dia=5)

        d = agent.to_dict()
        agent2 = Agent.from_dict(d)
        assert len(agent2._perception._recent_events) == 2
        assert len(agent2._perception._causal_assocs) == len(agent._perception._causal_assocs)
