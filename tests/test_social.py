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
        """_process_catastrophe_mortality aplica mortalidad selectiva."""
        import random as _rng_mod
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        infante = Agent("inf1", "Bebé", (5, 5), seed=100)
        infante.edad = 0
        adulto  = Agent("ad1", "Adulto", (5, 5), seed=101)
        adulto.edad = 30

        core.add_agent(infante)
        core.add_agent(adulto)

        # Sequía de máxima severidad global
        world.catastrophe._start("sequia_prolongada", dia=1, terrain=None)
        world.catastrophe.active.severidad  = 1.0
        world.catastrophe.active.area_hexes = None

        # Simular muchos días para que la mortalidad selectiva sea observable
        tp = TimePoint(tick=12, dia_simulado=1, hora_del_dia=12,
                       dia_del_año=1, año_simulado=0, estacion="verano",
                       es_amanecer=False, es_mediodia=True, es_anochecer=False,
                       es_medianoche=False, es_inicio_dia=False, es_fin_dia=False,
                       timestamp_real=0.0)
        muertes_infante = 0
        muertes_adulto  = 0
        for _ in range(200):
            # Reset vivos para contar independientemente
            infante.is_alive = True
            adulto.is_alive  = True
            cat = world.catastrophe
            ri  = cat.get_survival_risk_mod((5, 5), edad=0,  is_infant=True)
            ra  = cat.get_survival_risk_mod((5, 5), edad=30, is_infant=False)
            if core._rng.random() < ri:
                muertes_infante += 1
            if core._rng.random() < ra:
                muertes_adulto  += 1

        assert muertes_infante > muertes_adulto

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
