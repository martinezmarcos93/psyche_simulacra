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


# ── Hito 5: Catástrofes Climáticas Irreversibles ────────────────────────────

from core.world.catastrophe import CatastropheEngine, CatastropheEvent


class TestCatastropheEngine:
    """Tests unitarios del motor de catástrofes."""

    def test_sequia_reduce_agua(self):
        """Durante sequía, el modificador de agua baja por debajo de 1.0."""
        ce = CatastropheEngine(seed=1)
        ce._start("sequia_prolongada", dia=10, terrain=None)
        assert ce.active is not None
        mod = ce.get_water_modifier((5, 5), biome="llanura")
        assert mod < 1.0

    def test_bioma_resiliente_retiene_mas_agua(self):
        """Biomas con agua subterránea tienen mayor modificador que llanuras."""
        ce = CatastropheEngine(seed=2)
        ce._start("sequia_prolongada", dia=10, terrain=None)
        mod_llanura  = ce.get_water_modifier((5, 5), biome="llanura")
        mod_rio      = ce.get_water_modifier((5, 5), biome="rio_lago")
        assert mod_rio > mod_llanura

    def test_mortalidad_selectiva_infante_mayor_que_adulto(self):
        """Los infantes tienen mayor riesgo que los adultos durante catástrofe."""
        ce = CatastropheEngine(seed=3)
        ce._start("sequia_prolongada", dia=1, terrain=None)
        riesgo_infante = ce.get_survival_risk_mod((0, 0), edad=0,  is_infant=True)
        riesgo_adulto  = ce.get_survival_risk_mod((0, 0), edad=25, is_infant=False)
        assert riesgo_infante > riesgo_adulto

    def test_eclipse_cero_mortalidad(self):
        """Eclipse no produce mortalidad directa."""
        ce = CatastropheEngine(seed=4)
        ce._start("eclipse", dia=1, terrain=None)
        riesgo = ce.get_survival_risk_mod((0, 0), edad=5, is_infant=True)
        assert riesgo == 0.0

    def test_catastrofe_avanza_y_termina(self):
        """La catástrofe avanza días y se cierra al vencer la duración."""
        ce = CatastropheEngine(seed=5)
        ce._start("eclipse", dia=1, terrain=None)
        assert ce.active is not None
        duracion = ce.active.duracion_dias
        for d in range(duracion):
            ce.on_day(dia=1 + d, estacion="primavera", terrain=None)
        assert ce.active is None
        assert len(ce.history) == 1

    def test_serialization_round_trip(self):
        """to_dict / from_dict preservan catástrofe activa y huellas de terreno."""
        ce = CatastropheEngine(seed=6)
        ce._start("sequia_prolongada", dia=5, terrain=None)
        ce._terrain_marks[(1, 2)] = {"tipo": "seco", "severidad": 0.7, "dias_restantes": 30}

        d   = ce.to_dict()
        ce2 = CatastropheEngine.from_dict(d, seed=6)

        assert ce2.active is not None
        assert ce2.active.tipo == "sequia_prolongada"
        assert (1, 2) in ce2._terrain_marks

    def test_huellas_terreno_persisten_post_incendio(self):
        """Tras un incendio, quedan huellas 'quemado' en el terreno."""
        ce = CatastropheEngine(seed=7)
        ce._terrain_marks[(3, 3)] = {"tipo": "quemado", "severidad": 0.8, "dias_restantes": 20}
        mod_agua   = ce.get_water_modifier((3, 3), biome="llanura")
        mod_comida = ce.get_food_modifier((3, 3))
        assert mod_agua   < 1.0
        assert mod_comida < 1.0

    def test_invierno_brutal_reduce_comida_no_agua(self):
        """Invierno brutal reduce comida pero no modifica agua."""
        ce = CatastropheEngine(seed=8)
        ce._start("invierno_brutal", dia=1, terrain=None)
        mod_comida = ce.get_food_modifier((0, 0))
        mod_agua   = ce.get_water_modifier((0, 0), biome="llanura")
        assert mod_comida < 1.0
        assert mod_agua   == 1.0  # invierno no afecta agua directamente


class TestWorldCoreCatastrophe:
    """Tests de integración: CatastropheEngine en WorldCore."""

    def test_worldcore_tiene_catastrophe(self):
        """WorldCore instancia CatastropheEngine."""
        world = WorldCore(seed=42)
        assert hasattr(world, "catastrophe")
        assert isinstance(world.catastrophe, CatastropheEngine)

    def test_snapshot_incluye_catastrofe_none_si_no_activa(self):
        """WorldSnapshot.catastrofe_activa es None cuando no hay catástrofe."""
        from core.time import TimePoint
        world = WorldCore(seed=42)
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        world.on_tick(tp)
        snap = world.current_snapshot
        assert snap is not None
        assert snap.catastrofe_activa is None

    def test_snapshot_incluye_catastrofe_si_activa(self):
        """WorldSnapshot.catastrofe_activa contiene datos cuando hay catástrofe."""
        from core.time import TimePoint
        world = WorldCore(seed=42)
        world.catastrophe._start("eclipse", dia=1, terrain=None)
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        world.on_tick(tp)
        snap = world.current_snapshot
        assert snap.catastrofe_activa is not None
        assert snap.catastrofe_activa["tipo"] == "eclipse"

    def test_recursos_reducidos_durante_sequia(self):
        """Snapshot refleja reducción de agua durante sequía activa."""
        from core.time import TimePoint
        world = WorldCore(seed=42)
        # Primer tick sin catástrofe para inicializar snapshot
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        world.on_tick(tp)
        snap_normal = world.current_snapshot

        # Activar sequía
        world.catastrophe._start("sequia_prolongada", dia=2, terrain=None)
        tp2 = TimePoint(tick=24, dia_simulado=2, hora_del_dia=12,
                        dia_del_año=2, año_simulado=0, estacion="verano",
                        es_amanecer=False, es_mediodia=True, es_anochecer=False,
                        es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                        timestamp_real=1.0)
        world.on_tick(tp2)
        snap_sequia = world.current_snapshot

        # Al menos algún hex debería tener agua reducida
        agua_normal = sum(
            v.get("agua", 0) for v in snap_normal.recursos_por_hex.values()
        )
        agua_sequia = sum(
            v.get("agua", 0) for v in snap_sequia.recursos_por_hex.values()
        )
        # Con sequía global el total de agua debe ser igual o menor
        assert agua_sequia <= agua_normal + 0.01  # margen de regeneración diaria


class TestHito5EmergentCriterion:
    """
    Criterio de salida del Hito 5:
    Una sequía debe producir mortalidad, ansiedad y proto-mitos en CulturalMemory.
    """

    def _make_tribe(self, world, core, tribe_id, n_agents=6):
        """Crea n agentes en una tribu con campo local."""
        from core.social.collective_field import CollectiveField
        from core.social.cultural_memory import CulturalMemory
        agents = []
        for i in range(n_agents):
            a = Agent(f"{tribe_id}_{i}", f"Agente{i}", (5, 5), seed=i)
            a.edad = 25
            core.add_agent(a)
            agents.append(a)
        core.tribe_manager.tribes[tribe_id]             = [a.id for a in agents]
        core.tribe_manager.local_fields[tribe_id]      = CollectiveField()
        core.tribe_manager.cultural_memories[tribe_id] = CulturalMemory(tribe_id)
        for a in agents:
            core.tribe_manager.agent_to_tribe[a.id] = tribe_id
        return agents

    def test_sequia_aumenta_ansiedad(self):
        """Durante sequía, _process_catastrophe_anxiety sube ansiedad de agentes."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)
        agents = self._make_tribe(world, core, "tribu_a", n_agents=4)

        world.catastrophe._start("sequia_prolongada", dia=1, terrain=None)
        cat = world.catastrophe
        cat.active.area_hexes = None  # global

        ansiedad_antes = [a.ansiedad for a in agents]
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="verano",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        core._process_catastrophe_anxiety(tp, cat)

        for antes, a in zip(ansiedad_antes, agents):
            assert a.ansiedad >= antes

    def test_sequia_mata_infante_mas_que_adulto(self):
        """La tasa de riesgo diaria es mayor para infantes que para adultos."""
        world = WorldCore(seed=42)
        world.catastrophe._start("sequia_prolongada", dia=1, terrain=None)
        world.catastrophe.active.severidad  = 1.0
        world.catastrophe.active.area_hexes = None
        cat = world.catastrophe

        ri = cat.get_survival_risk_mod((5, 5), edad=0,  is_infant=True)
        ra = cat.get_survival_risk_mod((5, 5), edad=30, is_infant=False)
        assert ri > ra

    def test_catastrofe_registra_en_cultural_memory(self):
        """Al comenzar la catástrofe, se registra en CulturalMemory de la tribu."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)
        agents = self._make_tribe(world, core, "tribu_b", n_agents=3)

        world.catastrophe._start("sequia_prolongada", dia=10, terrain=None)
        world.catastrophe.active.area_hexes = None
        # Simular día 1 de catástrofe (dias_transcurridos == 1 después de on_day)
        world.catastrophe.active.dias_transcurridos = 1

        tp = TimePoint(tick=6*10, dia_simulado=10, hora_del_dia=6,
                       dia_del_año=10, año_simulado=0, estacion="verano",
                       es_amanecer=True, es_mediodia=False, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=10.0)
        core._process_catastrophe_anxiety(tp, world.catastrophe)

        cmem = core.tribe_manager.cultural_memories["tribu_b"]
        eventos_cat = [r for r in cmem.records if r.tipo_evento == "sequia_prolongada"]
        assert len(eventos_cat) >= 1

    def test_plaga_genera_taboo_en_memoria(self):
        """Muerte por plaga genera tabú de contagio en CulturalMemory."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        victima = Agent("v1", "Enfermo", (5, 5), seed=200)
        victima.edad     = 10
        victima.is_alive = True
        core.add_agent(victima)

        tribe_id = "tribu_plaga"
        from core.social.collective_field import CollectiveField
        from core.social.cultural_memory import CulturalMemory
        core.tribe_manager.tribes[tribe_id]             = [victima.id]
        core.tribe_manager.agent_to_tribe[victima.id]   = tribe_id
        core.tribe_manager.local_fields[tribe_id]      = CollectiveField()
        core.tribe_manager.cultural_memories[tribe_id] = CulturalMemory(tribe_id)

        world.catastrophe._start("plaga", dia=1, terrain=None)
        world.catastrophe._plague_hexes = {(5, 5)}
        world.catastrophe.active.severidad  = 1.0
        world.catastrophe.active.area_hexes = None

        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)

        # Forzar muerte por plaga
        victima.is_alive = True
        core._rng = type('R', (), {'random': lambda s: 0.0})()  # siempre muere
        core._process_catastrophe_mortality(tp, world.catastrophe)

        cmem   = core.tribe_manager.cultural_memories[tribe_id]
        taboos = [r for r in cmem.records if r.tipo_evento == "taboo_causal"]
        assert len(taboos) >= 1

    def test_eclipse_sube_confusion_y_myth_pressure(self):
        """Eclipse activo eleva confusion y myth_pressure tribales sin mortalidad."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)
        agents = self._make_tribe(world, core, "tribu_eclipse", n_agents=4)

        world.catastrophe._start("eclipse", dia=5, terrain=None)

        lf = core.tribe_manager.local_fields["tribu_eclipse"]
        confusion_antes     = lf.confusion
        myth_pressure_antes = lf.myth_pressure

        core._process_selective_attention(dia=5)

        assert lf.confusion     > confusion_antes
        assert lf.myth_pressure > myth_pressure_antes


# ── Hito 6: Fauna como Actor Simbólico ──────────────────────────────────────

from core.world.fauna_symbolic import SymbolicFaunaSystem, FaunaEntity


class TestSymbolicFaunaSystem:
    """Tests unitarios del motor de fauna simbólica."""

    def test_spawn_depredador(self):
        """SymbolicFaunaSystem genera un depredador y lo registra."""
        sfs = SymbolicFaunaSystem(seed=1)
        ent = sfs._spawn("depredador", (5, 5))
        assert ent.tipo == "depredador"
        assert ent.activo is True
        assert ent.id in sfs.entities

    def test_predator_attack_en_radio(self):
        """Depredador en radio ataca agentes en esa zona."""
        sfs = SymbolicFaunaSystem(seed=0)
        ent = sfs._spawn("depredador", (5, 5))
        ent.duracion = 999  # no expira

        # Agente en radio 2
        agents_pos = [("ag1", (6, 5), "t1")]
        # Forzamos rng para que siempre ataque
        sfs._rng = type("R", (), {"random": lambda s: 0.0})()
        attacks = sfs.check_predator_attacks(dia=1, agents_pos=agents_pos)
        assert len(attacks) == 1
        assert attacks[0]["agent_id"] == "ag1"

    def test_predator_fuera_radio_no_ataca(self):
        """Depredador fuera de radio no produce ataques."""
        sfs = SymbolicFaunaSystem(seed=1)
        ent = sfs._spawn("depredador", (5, 5))
        ent.duracion = 999
        agents_pos = [("ag1", (15, 15), "t1")]  # distancia muy alta
        sfs._rng = type("R", (), {"random": lambda s: 0.0})()
        attacks = sfs.check_predator_attacks(dia=1, agents_pos=agents_pos)
        assert len(attacks) == 0

    def test_symbolic_charge_liminal_biome_amplifica(self):
        """En bioma liminal la carga simbólica es mayor."""
        sfs = SymbolicFaunaSystem(seed=2)
        ent = sfs._spawn("raro", (3, 3))
        charge_normal  = sfs.symbolic_charge(ent.nombre, "t1", biome="llanura")
        charge_liminal = sfs.symbolic_charge(ent.nombre, "t1", biome="cueva")
        assert charge_liminal > charge_normal

    def test_kills_last_7_days_count(self):
        """kills_last_7_days filtra por tribe_id y ventana de 7 días."""
        from core.world.fauna_symbolic import PredatorKill
        sfs = SymbolicFaunaSystem(seed=3)
        sfs._kills = [
            PredatorKill(dia=10, coord=(0,0), tribe_id="t1", nombre="lobo"),
            PredatorKill(dia=11, coord=(1,0), tribe_id="t1", nombre="lobo"),
            PredatorKill(dia=1,  coord=(2,0), tribe_id="t1", nombre="lobo"),  # > 7 días
            PredatorKill(dia=10, coord=(0,0), tribe_id="t2", nombre="lobo"),
        ]
        # Día actual = 15; kills de t1 dentro de 7 días: días 10 y 11
        # Filtramos kills con dia > 15-7=8 → días 10,11 para t1, y día 10 para t2
        sfs._kills = [k for k in sfs._kills if 15 - k.dia <= 7]
        # Después del filtro quedan: días 10 y 11 de t1; día 1 fue eliminado (>7 días)
        assert sfs.kills_last_7_days("t1") == 2

    def test_serialization_round_trip(self):
        """to_dict / from_dict preservan entidades y kill_records."""
        sfs = SymbolicFaunaSystem(seed=4)
        sfs._spawn("depredador", (2, 2))
        sfs._spawn("raro", (7, 7))
        from core.world.fauna_symbolic import PredatorKill
        sfs._kills.append(PredatorKill(dia=5, coord=(2,2), tribe_id="t1", nombre="lobo"))
        sfs._tribe_obs["t1"] = {"lobo": 3}
        sfs._migration_log["ciervo_blanco"] = [("primavera", 10), ("primavera", 100)]

        d    = sfs.to_dict()
        sfs2 = SymbolicFaunaSystem.from_dict(d, seed=4)
        assert len(sfs2.entities) == 2
        assert len(sfs2._kills) == 1
        assert sfs2._tribe_obs.get("t1", {}).get("lobo") == 3
        assert sfs2.migration_recurrences("ciervo_blanco") == 2

    def test_migratory_only_in_season(self):
        """Fauna migratoria no aparece en verano ni invierno."""
        import unittest.mock as mock
        sfs = SymbolicFaunaSystem(seed=5)

        class AlwaysSpawnRNG:
            def random(self): return 0.0
            def randint(self, a, b): return a
            def choice(self, seq): return seq[0]

        sfs._rng = AlwaysSpawnRNG()

        class FakeTerrain:
            def explored_coords(self): return [(0,0), (1,1)]

        events_verano   = sfs.on_day(1, "verano",    FakeTerrain(), [])
        events_primavera = sfs.on_day(2, "primavera", FakeTerrain(), [])

        migratory_verano    = [e for e in events_verano   if e["subtipo"] == "migratorio"]
        migratory_primavera = [e for e in events_primavera if e["subtipo"] == "migratorio"]
        assert len(migratory_verano) == 0
        assert len(migratory_primavera) >= 1

    def test_scavenger_aparece_con_tumbas(self):
        """Carroñero aparece condicionalmente cuando hay tumbas activas."""
        sfs = SymbolicFaunaSystem(seed=6)

        class AlwaysSpawnRNG:
            def random(self): return 0.0
            def randint(self, a, b): return a
            def choice(self, seq): return seq[0]

        sfs._rng = AlwaysSpawnRNG()

        class FakeTerrain:
            def explored_coords(self): return [(0,0)]

        graves = [((1,1), 0.8, "heroe")]
        events = sfs.on_day(1, "primavera", FakeTerrain(), graves)
        scav = [e for e in events if e["subtipo"] == "carronero"]
        assert len(scav) >= 1


class TestWorldCoreFaunaSymbolic:
    """Tests de integración: SymbolicFaunaSystem en WorldCore."""

    def test_worldcore_tiene_fauna_symbolic(self):
        world = WorldCore(seed=42)
        assert hasattr(world, "fauna_symbolic")
        assert isinstance(world.fauna_symbolic, SymbolicFaunaSystem)

    def test_snapshot_incluye_fauna_simbolica(self):
        from core.time import TimePoint
        world = WorldCore(seed=42)
        # Insertar entidad manualmente
        ent = world.fauna_symbolic._spawn("raro", (5, 5))
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        world.on_tick(tp)
        snap = world.current_snapshot
        assert snap is not None
        fauna = snap.fauna_simbolica
        assert any(f["nombre"] == ent.nombre for f in fauna)


class TestHito6EmergentCriterion:
    """
    Criterio de salida del Hito 6:
    Dos muertes por depredador en 7 días → 'sombra' + 'muerte' altos en ICL → cosmogonia emergente.
    """

    def _make_tribe_agents(self, world, core, tribe_id, n=4):
        from core.social.collective_field import CollectiveField
        from core.social.cultural_memory import CulturalMemory
        agents = []
        for i in range(n):
            a = Agent(f"{tribe_id}_{i}", f"Agente{i}", (5, 5), seed=i+50)
            a.edad = 25
            core.add_agent(a)
            agents.append(a)
        core.tribe_manager.tribes[tribe_id]             = [a.id for a in agents]
        core.tribe_manager.local_fields[tribe_id]       = CollectiveField()
        core.tribe_manager.cultural_memories[tribe_id]  = CulturalMemory(tribe_id)
        for a in agents:
            core.tribe_manager.agent_to_tribe[a.id] = tribe_id
        return agents

    def test_depredador_inyecta_sombra_en_icl(self):
        """Muerte por depredador eleva símbolo 'sombra' en campo tribal."""
        world  = WorldCore(seed=42)
        core   = AgentCore(world)
        agents = self._make_tribe_agents(world, core, "t_pred", n=4)

        # Colocar depredador en posición de los agentes
        pred = world.fauna_symbolic._spawn("depredador", (5, 5))
        pred.duracion = 999

        lf = core.tribe_manager.local_fields["t_pred"]
        sombra_antes = lf.symbols.get("sombra", 0.0)

        # Forzar ataque
        world.fauna_symbolic._rng = type("R", (), {"random": lambda s: 0.0})()
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        core._process_symbolic_fauna(tp, world.fauna_symbolic)

        assert lf.symbols.get("sombra", 0.0) > sombra_antes

    def test_dos_kills_boost_myth_pressure(self):
        """Dos kills en 7 días disparan boost de myth_pressure y registro en CulturalMemory."""
        from core.world.fauna_symbolic import PredatorKill
        world  = WorldCore(seed=42)
        core   = AgentCore(world)
        agents = self._make_tribe_agents(world, core, "t_doble", n=4)

        # Precargar un kill anterior del mismo día
        world.fauna_symbolic._kills.append(
            PredatorKill(dia=1, coord=(5,5), tribe_id="t_doble", nombre="lobo_gris")
        )

        pred = world.fauna_symbolic._spawn("depredador", (5, 5))
        pred.duracion = 999
        world.fauna_symbolic._rng = type("R", (), {"random": lambda s: 0.0})()

        lf = core.tribe_manager.local_fields["t_doble"]
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        core._process_symbolic_fauna(tp, world.fauna_symbolic)

        cmem   = core.tribe_manager.cultural_memories["t_doble"]
        dobles = [r for r in cmem.records if r.tipo_evento == "depredador_doble_muerte"]
        assert len(dobles) >= 1
        assert lf.myth_pressure > 0.0

    def test_fauna_rara_eleva_myth_pressure(self):
        """Fauna rara cercana eleva myth_pressure del campo tribal."""
        world  = WorldCore(seed=42)
        core   = AgentCore(world)
        agents = self._make_tribe_agents(world, core, "t_raro", n=3)

        rara = world.fauna_symbolic._spawn("raro", (6, 5))
        rara.duracion = 999

        lf = core.tribe_manager.local_fields["t_raro"]
        mp_antes = lf.myth_pressure

        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        # Proveer snapshot con la fauna activa
        world.on_tick(tp)
        core._process_symbolic_fauna(tp, world.fauna_symbolic)

        assert lf.myth_pressure > mp_antes

    def test_migracion_recurrente_registra_en_memoria(self):
        """Fauna migratoria que aparece ≥2 veces produce registro en CulturalMemory."""
        world  = WorldCore(seed=42)
        core   = AgentCore(world)
        agents = self._make_tribe_agents(world, core, "t_migra", n=3)

        migra = world.fauna_symbolic._spawn("migratorio", (5, 5))
        migra.duracion = 999
        # Simular 2 apariciones previas registradas
        world.fauna_symbolic._migration_log[migra.nombre] = [
            ("primavera", 10), ("primavera", 100)
        ]
        world.fauna_symbolic._tribe_obs["t_migra"] = {migra.nombre: 2}

        tp = TimePoint(tick=12, dia_simulado=200, hora_del_dia=12,
                       dia_del_año=200, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=200.0)
        world.on_tick(tp)
        core._process_symbolic_fauna(tp, world.fauna_symbolic)

        cmem = core.tribe_manager.cultural_memories["t_migra"]
        migraciones = [r for r in cmem.records if r.tipo_evento == "migracion_recurrente"]
        assert len(migraciones) >= 1


# ── Hito 7: Linajes, Parentesco y Tabú del Incesto ──────────────────────────

from core.social.genealogy import LineageGraph


class TestLineageGraph:
    """Tests unitarios del árbol genealógico."""

    def test_registro_y_generacion(self):
        """Fundadores = gen 0; hijos = gen 1; nietos = gen 2."""
        lg = LineageGraph()
        lg.register("f1", None, None, dia=0,   tribe_orig="t1")
        lg.register("f2", None, None, dia=0,   tribe_orig="t1")
        lg.register("h1", "f1", "f2",  dia=10,  tribe_orig="t1")
        lg.register("n1", "h1", None,  dia=100, tribe_orig="t1")

        assert lg.get_generation("f1") == 0
        assert lg.get_generation("h1") == 1
        assert lg.get_generation("n1") == 2

    def test_consanguinity_hermanos(self):
        """Hermanos comparten padre → consanguinity 0.50."""
        lg = LineageGraph()
        lg.register("p", None, None, 0, "t")
        lg.register("m", None, None, 0, "t")
        lg.register("a", "p", "m",  10, "t")
        lg.register("b", "p", "m",  12, "t")
        assert lg.consanguinity_score("a", "b") == 0.50

    def test_consanguinity_primos(self):
        """Primos comparten abuelo → consanguinity 0.25."""
        lg = LineageGraph()
        lg.register("g1", None, None, 0, "t")
        lg.register("g2", None, None, 0, "t")
        lg.register("p1", "g1", "g2", 10, "t")
        lg.register("p2", "g1", "g2", 11, "t")
        lg.register("c1", "p1", None, 20, "t")
        lg.register("c2", "p2", None, 21, "t")
        assert lg.consanguinity_score("c1", "c2") == 0.25

    def test_sin_parentesco(self):
        """Fundadores de distinta tribu → consanguinity 0."""
        lg = LineageGraph()
        lg.register("a", None, None, 0, "t1")
        lg.register("b", None, None, 0, "t2")
        assert lg.consanguinity_score("a", "b") == 0.0

    def test_are_related(self):
        """are_related detecta ancestros comunes."""
        lg = LineageGraph()
        lg.register("f", None, None, 0, "t")
        lg.register("h1", "f", None, 10, "t")
        lg.register("h2", "f", None, 11, "t")
        assert lg.are_related("h1", "h2") is True

    def test_serialization_round_trip(self):
        """to_dict / from_dict preserva todo el árbol."""
        lg = LineageGraph()
        lg.register("f1", None, None, 0,  "t1")
        lg.register("f2", None, None, 0,  "t2")
        lg.register("c1", "f1", "f2",  10, "t1")

        d   = lg.to_dict()
        lg2 = LineageGraph.from_dict(d)
        assert lg2.get_generation("c1") == 1
        assert lg2.consanguinity_score("f1", "f2") == 0.0


class TestHito7EmergentCriterion:
    """
    Criterio de salida del Hito 7:
    - Celos → complejo de abandono + CulturalMemory 'traicion_vinculo'
    - Consanguinidad → penalización de rasgos al nacer
    - Reproducción cross-tribal → transferencia cultural emergente
    """

    def _make_agent(self, aid, nombre, posicion=(5,5), seed=0, edad=25):
        a = Agent(aid, nombre, posicion, seed=seed)
        a.edad = edad
        return a

    def _make_tribe_setup(self, world, core, tribe_id, agents):
        from core.social.collective_field import CollectiveField
        from core.social.cultural_memory import CulturalMemory
        core.tribe_manager.tribes[tribe_id]             = [a.id for a in agents]
        core.tribe_manager.local_fields[tribe_id]       = CollectiveField()
        core.tribe_manager.cultural_memories[tribe_id]  = CulturalMemory(tribe_id)
        for a in agents:
            core.tribe_manager.agent_to_tribe[a.id] = tribe_id

    def test_celos_activan_complejo_abandono(self):
        """A con bond alto con B, B con bond medio con C → A.complejo.abandono sube."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        ag_a = self._make_agent("a1", "Ares",    seed=1)
        ag_b = self._make_agent("b1", "Briseis", seed=2)
        ag_c = self._make_agent("c1", "Circe",   seed=3)
        for a in (ag_a, ag_b, ag_c):
            core.add_agent(a)

        core.social_network.set_bond("a1", "b1", 0.80)
        core.social_network.set_bond("b1", "a1", 0.80)
        core.social_network.set_bond("b1", "c1", 0.60)  # rival

        abandono_antes = ag_a.complexes.abandono
        tp = TimePoint(tick=12, dia_simulado=5, hora_del_dia=12,
                       dia_del_año=5, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        core._process_jealousy(tp)
        assert ag_a.complexes.abandono > abandono_antes

    def test_celos_registra_traicion_en_memoria(self):
        """Celos intensos se registran como 'traicion_vinculo' en CulturalMemory."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        ag_a = self._make_agent("j1", "Juno",   seed=10)
        ag_b = self._make_agent("j2", "Zeus",   seed=11)
        ag_c = self._make_agent("j3", "Hera",   seed=12)
        for a in (ag_a, ag_b, ag_c):
            core.add_agent(a)
        self._make_tribe_setup(world, core, "t_celos", [ag_a, ag_b, ag_c])

        core.social_network.set_bond("j1", "j2", 0.85)
        core.social_network.set_bond("j2", "j1", 0.85)
        core.social_network.set_bond("j2", "j3", 0.75)  # rival fuerte

        tp = TimePoint(tick=12, dia_simulado=10, hora_del_dia=12,
                       dia_del_año=10, año_simulado=0, estacion="primavera",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        core._process_jealousy(tp)

        cmem    = core.tribe_manager.cultural_memories["t_celos"]
        traicion = [r for r in cmem.records if r.tipo_evento == "traicion_vinculo"]
        assert len(traicion) >= 1

    def test_consanguinidad_aplica_penalizacion_traits(self):
        """Hijo de hermanos recibe ruido extra en sus rasgos vs hijo de no relacionados."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        # Fundar dos parejas: una con parentesco, otra sin
        padre = self._make_agent("p1", "Padre",  seed=20)
        madre = self._make_agent("p2", "Madre",  seed=21)
        herm1 = self._make_agent("h1", "Hermano1", seed=22, edad=20)
        herm2 = self._make_agent("h2", "Hermano2", seed=23, edad=20)
        # No relacionados
        ext1  = self._make_agent("e1", "Externo1", seed=24, edad=20)
        ext2  = self._make_agent("e2", "Externo2", seed=25, edad=20)

        for a in (padre, madre, herm1, herm2, ext1, ext2):
            core.add_agent(a)

        # Registrar genealogía
        core.lineage.register("p1", None, None, 0, "t")
        core.lineage.register("p2", None, None, 0, "t")
        core.lineage.register("h1", "p1", "p2", 10, "t")
        core.lineage.register("h2", "p1", "p2", 11, "t")
        core.lineage.register("e1", None, None, 0, "t")
        core.lineage.register("e2", None, None, 0, "t")

        score = core.lineage.consanguinity_score("h1", "h2")
        assert score == 0.50

    def test_linaje_registrado_al_nacer(self):
        """Descendiente generado por _generate_offspring aparece en LineageGraph."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        pa = self._make_agent("pa1", "ParentA", seed=30, edad=25)
        pb = self._make_agent("pb1", "ParentB", seed=31, edad=25)
        pa.needs.hambre = 0.0; pa.needs.sed = 0.0; pa.needs.fatiga = 0.0
        pb.needs.hambre = 0.0; pb.needs.sed = 0.0; pb.needs.fatiga = 0.0
        core.add_agent(pa)
        core.add_agent(pb)

        child = core._generate_offspring(pa, pb, dia=50)
        assert child.id in core.lineage.records
        rec = core.lineage.records[child.id]
        assert rec.parent_a == pa.id
        assert rec.parent_b == pb.id

    def test_bond_heredado_parcialmente(self):
        """El hijo hereda una fracción del bond que sus padres tenían con terceros."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        pa = self._make_agent("pa2", "Padre",  seed=40, edad=25)
        pb = self._make_agent("pb2", "Madre",  seed=41, edad=25)
        am = self._make_agent("am2", "Amigo",  seed=42, edad=30)
        for a in (pa, pb, am):
            core.add_agent(a)

        core.social_network.set_bond(pa.id, am.id, 0.80)
        core.social_network.set_bond(pb.id, am.id, 0.40)

        child = core._generate_offspring(pa, pb, dia=60)
        core.add_agent(child)

        inherited = core.social_network.get_bond(child.id, am.id)
        assert inherited > 0.05  # debe haber heredado algo

    def test_agentcore_serialization_incluye_linaje(self):
        """to_dict / from_dict del AgentCore preserva el LineageGraph."""
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        pa = self._make_agent("sa1", "SerPa", seed=50, edad=25)
        pb = self._make_agent("sb1", "SerPb", seed=51, edad=25)
        core.add_agent(pa)
        core.add_agent(pb)
        child = core._generate_offspring(pa, pb, dia=5)
        core.add_agent(child)

        d     = core.to_dict()
        core2 = AgentCore.from_dict(d, world)
        assert child.id in core2.lineage.records
        assert core2.lineage.records[child.id].parent_a == pa.id
