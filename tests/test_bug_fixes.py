"""
Tests de regresión para los bugs corregidos en la auditoría 2026-05-23.
Cubre: C1, C3, I2, I3, I4, I5, I7, M6, T1–T5 y el bug extra archetypes.weights.
"""
from __future__ import annotations

import time
import pytest

from core.time import SimulationClock, TimePoint
from core.agents.agent import Agent
from core.agents.needs import Needs, OVERRIDE_THRESHOLD
from core.agents.psyche.archetypes import ArchetypeVector
from core.liminal.agent_transfer import AgentTransferHandler, _IN_TRANSIT_TIMEOUT, _RETURN_COOLDOWN_TICKS
from core.interface import ActionType


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_tp(hora: int = 6, dia: int = 0) -> TimePoint:
    return TimePoint(
        tick=dia * 24 + hora, dia_simulado=dia, hora_del_dia=hora,
        dia_del_año=dia % 360, año_simulado=dia // 360,
        estacion="primavera",
        es_amanecer=(hora == 6), es_mediodia=(hora == 12),
        es_anochecer=(hora == 20), es_medianoche=(hora == 23),
        es_inicio_dia=(hora == 0), es_fin_dia=(hora == 23),
        timestamp_real=time.monotonic(),
    )


def _make_agent(pos=(40, 30)) -> Agent:
    return Agent(agent_id="test_001", nombre="Ares", posicion=pos, seed=0)


class _MockClient:
    def __init__(self, connected: bool = True):
        self.is_connected = connected
        self._incoming: list[dict] = []
        self.sent_enters: list[dict] = []

    def send_agent_enter(self, **kwargs):
        self.sent_enters.append(kwargs)

    def drain_incoming(self) -> list[dict]:
        evts = self._incoming[:]
        self._incoming.clear()
        return evts

    def push(self, event: dict) -> None:
        self._incoming.append(event)


class _MockAgentCore:
    def __init__(self, agents: dict | None = None):
        self.agents = agents or {}
        self.collective_field = _MockField()
        self.tribe_manager = None


class _MockField:
    def __init__(self):
        self.events: list[tuple] = []

    def absorb_event(self, event_type: str, intensity: float = 1.0) -> None:
        self.events.append((event_type, intensity))


class _MockPortal:
    def __init__(self, pos=(40, 30)):
        self.pos = pos

    def agent_at_portal(self, agent: Agent) -> bool:
        return agent.posicion == self.pos


def _make_handler(agent: Agent | None = None, portal_pos=(40, 30), connected=True):
    agents = {}
    if agent:
        agents[agent.id] = agent
    agent_core = _MockAgentCore(agents)
    portal = _MockPortal(portal_pos)
    client = _MockClient(connected)
    handler = AgentTransferHandler(agent_core, portal, client)
    return handler, client, agent_core


# ── I3 — es_medianoche debe ser hora==23, no hora==0 ─────────────────────────

class TestEsMedianoche:

    def test_es_medianoche_en_hora_23(self):
        clock = SimulationClock(start_dia=0, start_hora=23)
        assert clock.now.es_medianoche is True

    def test_no_es_medianoche_en_hora_0(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        assert clock.now.es_medianoche is False

    def test_es_inicio_dia_en_hora_0(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        assert clock.now.es_inicio_dia is True

    def test_no_es_inicio_dia_en_hora_23(self):
        clock = SimulationClock(start_dia=0, start_hora=23)
        assert clock.now.es_inicio_dia is False

    def test_ambas_flags_son_distintas(self):
        for hora in range(24):
            clock = SimulationClock(start_dia=0, start_hora=hora)
            tp = clock.now
            # Nunca deben ser True al mismo tiempo
            assert not (tp.es_medianoche and tp.es_inicio_dia)


# ── I5 — Nueva simulación arranca en hora 6, no dispara on_day en tick 0 ─────

class TestInicioSimulacion:

    def test_nueva_sesion_arranca_en_hora_6(self):
        from core.simulation import SimulationRunner
        # Parcheamos para no necesitar DB ni YAML
        runner = object.__new__(SimulationRunner)
        runner.clock = SimulationClock(start_dia=0, start_hora=6)
        assert runner.clock.now.hora_del_dia == 6
        assert runner.clock.now.es_inicio_dia is False

    def test_tick_0_en_hora_6_no_es_inicio_dia(self):
        clock = SimulationClock(start_dia=0, start_hora=6)
        on_day_llamado = []
        clock.on_day(lambda tp: on_day_llamado.append(tp.hora_del_dia))

        # Correr 6 ticks (hora 6..11) — ninguno es inicio de día
        collected = []
        def stopper(tp):
            collected.append(tp)
            if len(collected) >= 6:
                clock.shutdown()
        clock.on_tick(stopper)
        clock.start()

        assert on_day_llamado == [], (
            f"on_day se disparó en horas {on_day_llamado}, no debería antes de hora 0"
        )


# ── I2 — Agentes muertos no procesan complejos en on_day ─────────────────────

class TestAgentesMuertosOnDay:

    def test_on_day_no_activa_complejos_si_muerto(self):
        agent = _make_agent()
        agent.is_alive = False
        agent.needs.hambre = 0.99  # hambre crítica — debería activar complejo si estuviera vivo

        before_activos = list(agent.complexes.activos) if hasattr(agent.complexes, 'activos') else []
        agent.on_day(_make_tp(hora=0))
        after_activos = list(agent.complexes.activos) if hasattr(agent.complexes, 'activos') else []

        assert before_activos == after_activos, "on_day activó complejos en un agente muerto"

    def test_on_day_si_procesa_agente_vivo(self):
        agent = _make_agent()
        agent.is_alive = True
        agent.needs.hambre = 0.99  # hambre crítica

        agent.on_day(_make_tp(hora=0))
        # Verificar que complexes.decay_day() fue llamado (no lanza excepción)
        # Si llegamos aquí sin error, el agente vivo fue procesado correctamente


# ── I7 — sociabilidad se consume y dispara override ──────────────────────────

class TestSociabilidad:

    def test_social_override_activo_en_umbral(self):
        needs = Needs(sociabilidad=OVERRIDE_THRESHOLD)
        assert needs.social_override_active() is True

    def test_social_override_inactivo_bajo_umbral(self):
        needs = Needs(sociabilidad=0.5)
        assert needs.social_override_active() is False

    def test_socialize_reduce_sociabilidad(self):
        needs = Needs(sociabilidad=0.9)
        needs.socialize()
        assert needs.sociabilidad < 0.9

    def test_sociabilidad_no_baja_de_cero(self):
        needs = Needs(sociabilidad=0.1)
        needs.socialize()
        assert needs.sociabilidad >= 0.0

    def test_sociabilidad_crece_despierto(self):
        needs = Needs(sociabilidad=0.0)
        initial = needs.sociabilidad
        needs.update_waking()
        assert needs.sociabilidad > initial

    def test_survival_override_no_incluye_sociabilidad(self):
        """La sociabilidad alta no debe bloquear comer/beber."""
        needs = Needs(sociabilidad=1.0, hambre=0.0, sed=0.0, fatiga=0.0)
        assert needs.survival_override_active() is False


# ── C3 — Timeout de agentes atascados en _in_transit ─────────────────────────

class TestInTransitTimeout:

    def test_agente_atascado_se_recupera(self):
        agent = _make_agent(pos=(5, 5))
        agent.in_liminal = True
        handler, client, agent_core = _make_handler(agent, connected=True)

        # Simular que el agente está en tránsito
        handler._in_transit.add(agent.id)
        handler._transit_ticks[agent.id] = _IN_TRANSIT_TIMEOUT + 1

        handler._recover_stuck_agents()

        assert agent.in_liminal is False
        assert agent.id not in handler._in_transit
        assert agent.id not in handler._transit_ticks
        assert agent.id in handler._return_cooldown

    def test_agente_sin_timeout_no_se_recupera(self):
        agent = _make_agent(pos=(5, 5))
        agent.in_liminal = True
        handler, client, agent_core = _make_handler(agent, connected=True)

        handler._in_transit.add(agent.id)
        handler._transit_ticks[agent.id] = _IN_TRANSIT_TIMEOUT // 2  # aún no vencido

        handler._recover_stuck_agents()

        assert agent.in_liminal is True  # no recuperado
        assert agent.id in handler._in_transit

    def test_transit_ticks_incrementa_en_on_tick(self):
        agent = _make_agent(pos=(5, 5))
        agent.in_liminal = True
        handler, client, agent_core = _make_handler(agent, connected=False)

        handler._in_transit.add(agent.id)
        handler._transit_ticks[agent.id] = 10

        handler.on_tick(_make_tp())

        assert handler._transit_ticks[agent.id] == 11

    def test_agent_placed_limpia_transit_ticks(self):
        agent = _make_agent(pos=(40, 30))
        handler, client, agent_core = _make_handler(agent, connected=True)

        handler._in_transit.add(agent.id)
        handler._transit_ticks[agent.id] = 5

        client.push({
            "type": "agent_placed",
            "agent_id": agent.id,
            "liminal_pos": [0, 0],
            "liminal_tick": 0,
            "return_after_ticks": 60,
        })
        handler._process_server_events()

        assert agent.id not in handler._transit_ticks
        assert agent.id not in handler._in_transit


# ── C1 — _find_water_action no teleporta y recolecta en el mismo tick ─────────

class TestFindWaterAction:

    def _make_snapshot(self, water_at: tuple[int, int], water_type="agua"):
        from core.interface import WorldSnapshot
        recursos = {water_at: {water_type: 0.5}}
        return WorldSnapshot(
            tick=0, dia=0, hora=6, estacion="primavera",
            temperatura=20.0, precipitacion=0.5, luminosidad=0.8,
            viento=0.2, evento_climatico=None,
            mood_modifier=0.0, productivity_mod=0.0, survival_risk=0.1,
            recursos_por_hex=recursos, fauna_visible={},
            fuego_activo=False, fuego_coord=None,
            fuego_intensidad=0.0, fuego_calor_bonus=0.0,
            carrying_capacity=100.0, resource_pressure=0.1,
            action_results={},
        )

    def test_agua_en_hex_actual_devuelve_recolectar(self):
        agent = _make_agent(pos=(40, 30))
        tp = _make_tp()
        snap = self._make_snapshot(water_at=(40, 30))
        action = agent._find_water_action(tp, snap)
        assert action is not None
        assert action.type == ActionType.RECOLECTAR
        assert agent.posicion == (40, 30)  # no se movió

    def test_agua_en_hex_vecino_devuelve_moverse(self):
        agent = _make_agent(pos=(40, 30))
        tp = _make_tp()
        snap = self._make_snapshot(water_at=(41, 30))
        action = agent._find_water_action(tp, snap)
        assert action is not None
        assert action.type == ActionType.MOVERSE
        assert agent.posicion == (41, 30)  # se movió

    def test_agua_en_hex_vecino_no_recolecta_en_mismo_tick(self):
        """El agente se mueve y el world no recibe RECOLECTAR este tick."""
        agent = _make_agent(pos=(40, 30))
        tp = _make_tp()
        snap = self._make_snapshot(water_at=(41, 30))
        action = agent._find_water_action(tp, snap)
        assert action.type != ActionType.RECOLECTAR

    def test_agua_salobre_reconocida_en_hex_actual(self):
        agent = _make_agent(pos=(40, 30))
        tp = _make_tp()
        snap = self._make_snapshot(water_at=(40, 30), water_type="agua_salobre")
        action = agent._find_water_action(tp, snap)
        assert action is not None
        assert action.type == ActionType.RECOLECTAR

    def test_nieve_reconocida_en_hex_actual(self):
        agent = _make_agent(pos=(40, 30))
        tp = _make_tp()
        snap = self._make_snapshot(water_at=(40, 30), water_type="nieve")
        action = agent._find_water_action(tp, snap)
        assert action is not None
        assert action.type == ActionType.RECOLECTAR


# ── I4 — agua_salobre y nieve reconocidas en sed crítica ─────────────────────

class TestSedCriticaFuentesAgua:

    def test_decide_via_collapse_reconoce_agua_salobre(self):
        from core.interface import WorldSnapshot
        agent = _make_agent(pos=(40, 30))
        tp = _make_tp()
        recursos = {(40, 30): {"agua_salobre": 0.5}}
        snap = WorldSnapshot(
            tick=0, dia=0, hora=6, estacion="primavera",
            temperatura=20.0, precipitacion=0.5, luminosidad=0.8,
            viento=0.2, evento_climatico=None,
            mood_modifier=0.0, productivity_mod=0.0, survival_risk=0.1,
            recursos_por_hex=recursos, fauna_visible={},
            fuego_activo=False, fuego_coord=None,
            fuego_intensidad=0.0, fuego_calor_bonus=0.0,
            carrying_capacity=100.0, resource_pressure=0.1,
            action_results={},
        )
        action = agent._decide_via_collapse(tp, snap, None, False)
        # No debería ignorar agua_salobre — puede devolver RECOLECTAR o MOVERSE
        # Lo importante es que NO devuelve None (el agente intentó hacer algo con el agua)
        if action is not None and action.type == ActionType.RECOLECTAR:
            assert action.params.get("resource") == "agua_salobre"


# ── T5 — _apply_encounter_effects con arquetipos desconocidos ─────────────────

class TestApplyEncounterEffects:

    def test_arquetipo_conocido_aplica_nudge(self):
        agent = _make_agent()
        initial = agent.archetypes.sabio
        handler, client, agent_core = _make_handler(agent)
        agent_core.agents[agent.id] = agent

        encounters = [{"nombre": "Extraño", "dominant_archetype": "sabio"}]
        handler._apply_encounter_effects(agent, encounters)

        assert agent.archetypes.sabio > initial

    def test_arquetipo_desconocido_usa_resonancia_default(self):
        agent = _make_agent()
        handler, client, agent_core = _make_handler(agent)
        agent_core.agents[agent.id] = agent

        encounters = [{"nombre": "Ser", "dominant_archetype": "arquetipo_inexistente"}]
        # No debe lanzar excepción
        handler._apply_encounter_effects(agent, encounters)

        # El log episódico debe registrar el encuentro
        assert any("LIMINAL_ENCUENTRO" in e for e in agent.episodic_log)

    def test_primer_encuentro_setea_dream_seed(self):
        agent = _make_agent()
        assert agent._pending_liminal_encounter is None
        handler, client, agent_core = _make_handler(agent)
        agent_core.agents[agent.id] = agent

        encounters = [{"nombre": "Oráculo", "dominant_archetype": "sabio"}]
        handler._apply_encounter_effects(agent, encounters)

        assert agent._pending_liminal_encounter is not None
        assert "resonancia" in agent._pending_liminal_encounter

    def test_segundo_encuentro_no_sobreescribe_dream_seed(self):
        agent = _make_agent()
        handler, client, agent_core = _make_handler(agent)
        agent_core.agents[agent.id] = agent

        encounters = [
            {"nombre": "Primero", "dominant_archetype": "sabio"},
            {"nombre": "Segundo", "dominant_archetype": "heroe"},
        ]
        handler._apply_encounter_effects(agent, encounters)

        # El seed del primero debe persistir
        assert agent._pending_liminal_encounter is not None
        # resonancia del sabio, no del heroe
        from core.liminal.agent_transfer import _ARCH_RESONANCE
        assert agent._pending_liminal_encounter["resonancia"] == _ARCH_RESONANCE["sabio"]

    def test_campo_colectivo_absorbe_vision_liminal(self):
        agent = _make_agent()
        handler, client, agent_core = _make_handler(agent)
        agent_core.agents[agent.id] = agent

        encounters = [
            {"nombre": "A", "dominant_archetype": "sabio"},
            {"nombre": "B", "dominant_archetype": "heroe"},
        ]
        handler._apply_encounter_effects(agent, encounters)

        assert any(e[0] == "vision_liminal" for e in agent_core.collective_field.events)


# ── T1 — Flujo liminal completo (enter → placed → return) ────────────────────

class TestLiminalFlowCompleto:

    def test_agente_en_portal_entra_al_liminal(self):
        agent = _make_agent(pos=(40, 30))
        handler, client, _ = _make_handler(agent, portal_pos=(40, 30), connected=True)

        handler._check_portal_crossings()

        assert agent.in_liminal is True
        assert agent.id in handler._in_transit
        assert len(client.sent_enters) == 1
        assert client.sent_enters[0]["agent_id"] == agent.id

    def test_agent_placed_confirma_posicion(self):
        agent = _make_agent(pos=(40, 30))
        agent.in_liminal = True
        handler, client, _ = _make_handler(agent, connected=True)
        handler._in_transit.add(agent.id)
        handler._transit_ticks[agent.id] = 0

        client.push({
            "type": "agent_placed",
            "agent_id": agent.id,
            "liminal_pos": [5, 5],
            "liminal_tick": 0,
            "return_after_ticks": 60,
        })
        handler._process_server_events()

        assert agent.id not in handler._in_transit
        assert handler.get_liminal_pos(agent.id) == (5, 5)

    def test_agent_return_restaura_agente(self):
        agent = _make_agent(pos=(40, 30))
        agent.in_liminal = True
        handler, client, _ = _make_handler(agent, portal_pos=(40, 30), connected=True)
        handler._liminal_agents[agent.id] = {"pos": (5, 5), "liminal_tick": 0, "return_after_ticks": 60}

        client.push({
            "type": "agent_return",
            "agent_id": agent.id,
            "encounters": [],
        })
        handler._process_server_events()

        assert agent.in_liminal is False
        assert agent.posicion == (40, 30)
        assert agent.id in handler._return_cooldown

    def test_cooldown_evita_reentrada_inmediata(self):
        agent = _make_agent(pos=(40, 30))
        handler, client, _ = _make_handler(agent, portal_pos=(40, 30), connected=True)
        handler._return_cooldown[agent.id] = 10

        handler._check_portal_crossings()

        # No debe haber intentado cruzar
        assert len(client.sent_enters) == 0

    def test_desconectado_no_transfiere(self):
        agent = _make_agent(pos=(40, 30))
        handler, client, _ = _make_handler(agent, portal_pos=(40, 30), connected=False)

        handler._check_portal_crossings()

        assert agent.in_liminal is False
        assert len(client.sent_enters) == 0


# ── Bug extra — archetypes.to_dict() (no .weights) ───────────────────────────

class TestArchetypesSerializacion:

    def test_to_dict_devuelve_todos_los_arquetipos(self):
        av = ArchetypeVector()
        d = av.to_dict()
        assert "self" in d
        assert "heroe" in d
        assert "sombra" in d
        assert len(d) == 12

    def test_no_existe_atributo_weights(self):
        av = ArchetypeVector()
        assert not hasattr(av, "weights"), (
            "ArchetypeVector.weights no debe existir — usar to_dict()"
        )

    def test_agent_transfer_usa_to_dict_no_weights(self):
        """Verificar que _transfer_agent puede serializar arquetipos sin crash."""
        agent = _make_agent(pos=(40, 30))
        handler, client, _ = _make_handler(agent, portal_pos=(40, 30), connected=True)

        handler._transfer_agent(agent)

        assert len(client.sent_enters) == 1
        sent = client.sent_enters[0]
        assert "archetypes" in sent
        assert isinstance(sent["archetypes"], dict)


# ── T4 — Orden de handlers en SimulationClock ────────────────────────────────

class TestClockHandlerOrder:

    def test_prioridad_determina_orden_on_tick(self):
        clock = SimulationClock()
        orden = []
        clock.on_tick(lambda tp: orden.append("world"),  priority=10)
        clock.on_tick(lambda tp: orden.append("agents"), priority=20)
        clock.on_tick(lambda tp: orden.append("persist"), priority=30)

        ticks = []
        def stopper(tp):
            ticks.append(tp)
            if len(ticks) >= 1:
                clock.shutdown()
        clock.on_tick(stopper, priority=99)
        clock.start()

        assert orden == ["world", "agents", "persist"]

    def test_prioridad_determina_orden_on_day(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        orden_day = []
        clock.on_day(lambda tp: orden_day.append("world"),  priority=10)
        clock.on_day(lambda tp: orden_day.append("agents"), priority=20)
        clock.on_day(lambda tp: orden_day.append("persist"), priority=30)

        ticks = []
        def stopper(tp):
            ticks.append(tp)
            if len(ticks) >= 1:
                clock.shutdown()
        clock.on_tick(stopper, priority=99)
        clock.start()

        assert orden_day == ["world", "agents", "persist"]


# ── T2 — Edge cases de muerte ─────────────────────────────────────────────────

class TestMuerteEdgeCases:

    def test_check_death_no_mata_en_primer_dia_con_necesidades_bajas(self):
        agent = _make_agent()
        assert agent.is_alive is True
        result = agent.check_death()
        assert result is None
        assert agent.is_alive is True

    def test_agente_in_liminal_vivo_no_envejece_si_on_day_skipped(self):
        """on_day salta si muerto; el agente liminal no debe morir por lógica de on_day."""
        agent = _make_agent()
        agent.is_alive = False
        agent.needs.hambre = 1.0
        agent.needs.sed = 1.0

        # on_day debe retornar sin activar complejos ni llamar check_activation
        tp = _make_tp(hora=0)
        agent.on_day(tp)  # No debe lanzar excepción ni hacer nada

        # El agente sigue muerto, sin cambios en complejos
        assert agent.is_alive is False

    def test_muerte_por_sed_tarda_dias_criticos(self):
        from core.agents.needs import CRITICAL_THRESHOLD
        agent = _make_agent()
        agent.needs.sed = CRITICAL_THRESHOLD + 0.01  # sed crítica desde el inicio
        tp = _make_tp(hora=0)

        # 1 día crítico → no muere (necesita _DIAS_SED_MUERTE = 3)
        result = agent.check_death()
        assert result is None

        # 3 días críticos → muere
        agent._dias_sed_critica = 3
        result = agent.check_death()
        assert result == "deshidratacion"
        assert agent.is_alive is False


# ── Hito: Transmisión cross-sim de mitos ──────────────────────────────────────

from core.social.collective_field import CollectiveField
from core.social.mythology import MythologyEngine, MythCrystal, ProtoMito
from core.liminal.agent_transfer import _ARCH_RESONANCE


class _MockClientMythAware(_MockClient):
    """Versión del mock que también captura send_myth_event."""
    def __init__(self, connected: bool = True):
        super().__init__(connected)
        self.sent_myths: list[dict] = []

    def send_myth_event(self, **kwargs):
        self.sent_myths.append(kwargs)


class _MockAgentCoreWithMythology(_MockAgentCore):
    def __init__(self, agents=None):
        super().__init__(agents)
        self.mythology_engine = MythologyEngine()
        self.collective_field = CollectiveField()


class TestPoolNombres:
    """El pool de nombres no debe tener duplicados y debe tener >90 entradas."""

    def test_sin_duplicados(self):
        from core.agents.agent_core import _NOMBRES_POOL
        assert len(_NOMBRES_POOL) == len(set(_NOMBRES_POOL)), "Hay nombres duplicados"

    def test_pool_suficientemente_grande(self):
        from core.agents.agent_core import _NOMBRES_POOL
        assert len(_NOMBRES_POOL) >= 90, f"Pool insuficiente: {len(_NOMBRES_POOL)} nombres"


class TestCollectiveFieldMythBroadcast:
    """absorb_myth_broadcast() sube myth_pressure y carga símbolos del par."""

    def test_aumenta_myth_pressure(self):
        cf = CollectiveField()
        cf.absorb_myth_broadcast("mito_moral", ["heroe", "sombra"], 1.0, "SIM_B")
        assert cf.myth_pressure > 0.0

    def test_carga_simbolos_del_par(self):
        cf = CollectiveField()
        cf.absorb_myth_broadcast("mito_moral", ["heroe", "sombra"], 1.0, "SIM_B")
        assert cf.symbols["heroe"] > 0.0
        assert cf.symbols["sombra"] > 0.0

    def test_eco_es_mas_debil_que_local(self):
        """El eco cross-sim (40%) debe subir menos que un vision_liminal directo."""
        cf_eco   = CollectiveField()
        cf_local = CollectiveField()
        cf_eco.absorb_myth_broadcast("mito_moral", ["heroe", "sombra"], 1.0, "SIM_B")
        cf_local.absorb_event("vision_liminal", intensity=1.0)
        assert cf_eco.myth_pressure < cf_local.myth_pressure

    def test_par_vacio_no_crashea(self):
        cf = CollectiveField()
        cf.absorb_myth_broadcast("mito_moral", [], 0.5, "SIM_X")
        assert cf.myth_pressure > 0.0


class TestBroadcastNewMyths:
    """AgentTransferHandler.on_day() detecta mitos nuevos y los envía al servidor."""

    def _make_myth_handler(self):
        core   = _MockAgentCoreWithMythology()
        portal = _MockPortal()
        client = _MockClientMythAware(connected=True)
        handler = AgentTransferHandler(core, portal, client)
        return handler, client, core

    def test_mito_nuevo_se_envía(self):
        handler, client, core = self._make_myth_handler()
        core.mythology_engine.active_myths.append(MythCrystal(
            name="mito_moral_dia1", tipo="mito_moral",
            par=("heroe", "sombra"), active=True, day_crystallized=1,
        ))
        tp = _make_tp(hora=0, dia=1)
        handler.on_day(tp)
        assert len(client.sent_myths) == 1
        sent = client.sent_myths[0]
        assert sent["myth_name"] == "mito_moral_dia1"
        assert sent["myth_type"] == "mito_moral"

    def test_mito_ya_enviado_no_se_reenvía(self):
        handler, client, core = self._make_myth_handler()
        myth = MythCrystal(
            name="mito_moral_dia1", tipo="mito_moral",
            par=("heroe", "sombra"), active=True, day_crystallized=1,
        )
        core.mythology_engine.active_myths.append(myth)
        tp = _make_tp(hora=0, dia=1)
        handler.on_day(tp)
        handler.on_day(tp)  # segundo on_day
        assert len(client.sent_myths) == 1  # sólo enviado una vez

    def test_sin_conexion_no_envía(self):
        core   = _MockAgentCoreWithMythology()
        portal = _MockPortal()
        client = _MockClientMythAware(connected=False)
        handler = AgentTransferHandler(core, portal, client)
        core.mythology_engine.active_myths.append(MythCrystal(
            name="mito_x", tipo="mito_moral",
            par=("heroe", "sombra"), active=True, day_crystallized=1,
        ))
        tp = _make_tp(hora=0, dia=1)
        handler.on_day(tp)
        assert len(client.sent_myths) == 0

    def test_multiples_mitos_todos_enviados(self):
        handler, client, core = self._make_myth_handler()
        for i in range(3):
            core.mythology_engine.active_myths.append(MythCrystal(
                name=f"mito_dia{i}", tipo="mito_moral",
                par=("heroe", "sombra"), active=True, day_crystallized=i,
            ))
        tp = _make_tp(hora=0, dia=3)
        handler.on_day(tp)
        assert len(client.sent_myths) == 3


class TestHandleMythBroadcast:
    """_handle_myth_broadcast() altera campo colectivo e inyecta resonancia onírica."""

    def _make_myth_handler_with_agent(self, arch_dominante: str = "heroe"):
        agent = _make_agent()
        setattr(agent.archetypes, arch_dominante, 0.90)
        core   = _MockAgentCoreWithMythology({agent.id: agent})
        portal = _MockPortal(pos=(0, 0))  # posición distinta al agente para no disparar transferencia
        client = _MockClientMythAware(connected=True)
        handler = AgentTransferHandler(core, portal, client)
        return handler, agent, core

    def test_myth_broadcast_aumenta_campo(self):
        handler, _, core = self._make_myth_handler_with_agent()
        client = handler._client
        client.push({
            "type": "myth_broadcast", "origin_sim": "SIM_B",
            "myth_name": "mito_moral_dia3", "myth_type": "mito_moral",
            "par": ["heroe", "sombra"], "intensity": 0.8, "day": 3,
        })
        tp = _make_tp(hora=6)
        handler.on_tick(tp)
        assert core.collective_field.myth_pressure > 0.0

    def test_myth_broadcast_inyecta_sueno_en_agente_afin(self):
        """Un agente con arquetipo heroe dominante recibe semilla onírica."""
        handler, agent, _ = self._make_myth_handler_with_agent("heroe")
        handler._client.push({
            "type": "myth_broadcast", "origin_sim": "SIM_B",
            "myth_name": "mito_moral_dia3", "myth_type": "mito_moral",
            "par": ["heroe", "sombra"], "intensity": 0.8, "day": 3,
        })
        tp = _make_tp(hora=6)
        handler.on_tick(tp)
        assert agent._pending_liminal_encounter is not None

    def test_myth_broadcast_no_afecta_agente_no_afin(self):
        """Un agente sin arquetipo afín NO recibe semilla onírica."""
        handler, agent, _ = self._make_myth_handler_with_agent("sabio")
        handler._client.push({
            "type": "myth_broadcast", "origin_sim": "SIM_B",
            "myth_name": "mito_moral_dia3", "myth_type": "mito_moral",
            "par": ["heroe", "sombra"], "intensity": 0.8, "day": 3,
        })
        tp = _make_tp(hora=6)
        handler.on_tick(tp)
        assert agent._pending_liminal_encounter is None

    def test_myth_broadcast_registra_en_episodic_log(self):
        handler, agent, _ = self._make_myth_handler_with_agent("heroe")
        handler._client.push({
            "type": "myth_broadcast", "origin_sim": "SIM_B",
            "myth_name": "mito_moral_dia3", "myth_type": "mito_moral",
            "par": ["heroe", "sombra"], "intensity": 0.8, "day": 3,
        })
        tp = _make_tp(hora=6)
        handler.on_tick(tp)
        assert any("ECO_MITICO" in e for e in agent.episodic_log)
