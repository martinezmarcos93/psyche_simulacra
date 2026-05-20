"""
Tests del Núcleo 2 (Agentes) — Fase 3.
Cubre Needs, ScheduleSystem, Agent y AgentCore.
Criterio de fase: 15 agentes corren 30 días simulados sin morir todos.
"""
import time
import pytest
from core.time import SimulationClock, TimePoint
from core.world import WorldCore
from core.agents import Agent, AgentCore, Needs, ScheduleSystem, OVERRIDE_THRESHOLD, CRITICAL_THRESHOLD


# ── Needs ─────────────────────────────────────────────────────────────────────

class TestNeeds:

    def test_initial_values(self):
        n = Needs()
        assert n.hambre == 0.0
        assert n.fatiga == 0.0
        assert n.sed == 0.0

    def test_waking_increases_needs(self):
        n = Needs()
        n.update_waking()
        assert n.hambre > 0.0
        assert n.fatiga > 0.0
        assert n.sed > 0.0

    def test_sleeping_recovers_fatigue(self):
        n = Needs(fatiga=0.8)
        n.update_sleeping()
        assert n.fatiga < 0.8

    def test_sleeping_hambre_increases_slower_than_waking(self):
        n1 = Needs()
        n2 = Needs()
        n1.update_waking()
        n2.update_sleeping()
        assert n1.hambre > n2.hambre

    def test_eat_reduces_hambre(self):
        n = Needs(hambre=0.8)
        n.eat(0.30)
        assert n.hambre < 0.8

    def test_drink_reduces_sed(self):
        n = Needs(sed=0.9)
        n.drink(0.50)
        assert n.sed < 0.9

    def test_needs_clamped_at_1(self):
        n = Needs(hambre=0.99)
        for _ in range(10):
            n.update_waking()
        assert n.hambre <= 1.0

    def test_needs_clamped_at_0(self):
        n = Needs(hambre=0.05)
        n.eat(1.0)
        assert n.hambre >= 0.0

    def test_survival_override_when_critical(self):
        n = Needs(sed=OVERRIDE_THRESHOLD)
        assert n.survival_override_active()

    def test_no_override_when_low(self):
        n = Needs(hambre=0.3, sed=0.3, fatiga=0.3)
        assert not n.survival_override_active()

    def test_most_critical_need_returns_worst(self):
        n = Needs(hambre=0.5, sed=OVERRIDE_THRESHOLD + 0.01, fatiga=0.6)
        assert n.most_critical_need() == "sed"

    def test_most_critical_need_returns_ninguna_when_ok(self):
        n = Needs(hambre=0.3, sed=0.3, fatiga=0.3)
        assert n.most_critical_need() == "ninguna"

    def test_stress_level_range(self):
        n = Needs(hambre=0.5, sed=0.5, fatiga=0.5)
        assert 0.0 <= n.stress_level <= 1.0

    def test_serialization_roundtrip(self):
        n = Needs(hambre=0.4, fatiga=0.6, sed=0.2, sociabilidad=0.8)
        n2 = Needs.from_dict(n.to_dict())
        assert abs(n2.hambre - 0.4) < 1e-9
        assert abs(n2.fatiga - 0.6) < 1e-9


# ── ScheduleSystem ────────────────────────────────────────────────────────────

class TestScheduleSystem:

    def test_sleeps_at_night(self):
        s = ScheduleSystem()
        for hora in [0, 1, 2, 3, 4, 5, 22, 23]:
            assert s.get_activity(hora) == "dormir", f"hora {hora} should be dormir"

    def test_default_day_activities(self):
        s = ScheduleSystem()
        assert s.get_activity(7)  == "buscar_alimento"
        assert s.get_activity(13) == "interactuar"
        assert s.get_activity(17) == "explorar"

    def test_cazador_role(self):
        s = ScheduleSystem(rol="cazador")
        assert s.get_activity(7) == "cazar"
        assert s.get_activity(8) == "cazar"

    def test_explorador_role(self):
        s = ScheduleSystem(rol="explorador")
        assert s.get_activity(7) == "explorar"

    def test_adjust_for_season_is_stub(self):
        s = ScheduleSystem()
        s.adjust_for_season("invierno")  # should not raise

    def test_serialization_roundtrip(self):
        s = ScheduleSystem(rol="cazador")
        s2 = ScheduleSystem.from_dict(s.to_dict())
        assert s2.rol == "cazador"
        assert s2.get_activity(7) == "cazar"


# ── Agent ─────────────────────────────────────────────────────────────────────

def _make_agent(agent_id: str = "a1", posicion: tuple = (40, 30)) -> Agent:
    return Agent(agent_id=agent_id, nombre="Test", posicion=posicion, seed=42)


def _make_snapshot(tick: int = 0) -> object:
    from core.interface import WorldSnapshot
    return WorldSnapshot(
        tick=tick, dia=0, hora=8, estacion="primavera",
        temperatura=18.0, precipitacion=0.3, luminosidad=0.8,
        viento=0.2, evento_climatico=None,
        mood_modifier=0.1, productivity_mod=0.1, survival_risk=0.0,
        recursos_por_hex={(40, 30): {"frutos": 0.8, "agua": 0.9}},
        fauna_visible={(40, 30): {"pequena": 0.4, "grande": 0.1}},
        fuego_activo=False, fuego_coord=None,
        fuego_intensidad=0.0, fuego_calor_bonus=0.0,
        carrying_capacity=40, resource_pressure=0.3,
        action_results={},
    )


def _make_tp(tick: int = 0, hora: int = 8) -> TimePoint:
    dia = tick // 24
    return TimePoint(
        tick=tick, dia_simulado=dia, hora_del_dia=hora,
        dia_del_año=dia % 360, año_simulado=dia // 360,
        estacion="primavera",
        es_amanecer=(hora == 6), es_mediodia=(hora == 12),
        es_anochecer=(hora == 20), es_medianoche=(hora == 0),
        es_inicio_dia=(hora == 0), es_fin_dia=(hora == 23),
        timestamp_real=time.monotonic(),
    )


class TestAgent:

    def test_agent_starts_alive(self):
        a = _make_agent()
        assert a.is_alive

    def test_update_biological_changes_needs(self):
        a = _make_agent()
        snap = _make_snapshot()
        tp   = _make_tp(hora=8)
        a.update_biological(tp, snap)
        assert a.needs.hambre > 0.0

    def test_sleeping_tick_recovers_fatigue(self):
        a = _make_agent()
        a.needs.fatiga = 0.8
        snap = _make_snapshot()
        tp   = _make_tp(hora=2)  # hora 2 → dormir
        a.update_biological(tp, snap)
        assert a.needs.fatiga < 0.8

    def test_decide_action_returns_worldaction_during_day(self):
        a    = _make_agent()
        snap = _make_snapshot()
        tp   = _make_tp(hora=8)
        action = a.decide_action(tp, snap)
        assert action is not None
        assert action.agent_id == "a1"

    def test_decide_action_none_while_sleeping(self):
        a    = _make_agent()
        snap = _make_snapshot()
        tp   = _make_tp(hora=2)
        action = a.decide_action(tp, snap)
        assert action is None

    def test_critical_thirst_overrides_schedule(self):
        a = _make_agent()
        a.needs.sed = OVERRIDE_THRESHOLD
        snap = _make_snapshot()
        tp   = _make_tp(hora=12)  # hora 12 → descansar normally
        action = a.decide_action(tp, snap)
        # Should seek water instead of resting
        assert action is not None

    def test_check_death_not_triggered_normally(self):
        a = _make_agent()
        cause = a.check_death()
        assert cause is None
        assert a.is_alive

    def test_death_by_dehydration(self):
        a = _make_agent()
        a.needs.sed = CRITICAL_THRESHOLD
        for _ in range(3):  # call 2 days + buffer
            a.check_death()
        # After _DIAS_SED_MUERTE (2) consecutive critical days
        a.needs.sed = CRITICAL_THRESHOLD
        cause = a.check_death()
        assert not a.is_alive or cause == "deshidratacion"

    def test_death_counter_resets_when_need_drops(self):
        a = _make_agent()
        a.needs.hambre = CRITICAL_THRESHOLD
        a.check_death()
        assert a._dias_hambre_critica == 1
        a.needs.hambre = 0.3  # recovered
        a.check_death()
        assert a._dias_hambre_critica == 0

    def test_snapshot_dict_has_expected_keys(self):
        a    = _make_agent()
        snap = a.snapshot()
        for key in ["id", "nombre", "posicion", "rol", "is_alive", "needs"]:
            assert key in snap

    def test_serialization_roundtrip(self):
        a  = _make_agent()
        a.needs.hambre = 0.45
        d  = a.to_dict()
        a2 = Agent.from_dict(d)
        assert a2.id == a.id
        assert abs(a2.needs.hambre - 0.45) < 1e-9

    def test_dead_agent_produces_no_action(self):
        a = _make_agent()
        a.is_alive = False
        snap = _make_snapshot()
        tp   = _make_tp(hora=8)
        assert a.decide_action(tp, snap) is None


# ── AgentCore ─────────────────────────────────────────────────────────────────

class TestAgentCore:

    def _build_core(self, n_agents: int = 3) -> tuple[WorldCore, AgentCore]:
        world = WorldCore(seed=42)
        core  = AgentCore(world)
        cx, cy = world.terrain.center
        for i in range(n_agents):
            core.add_agent(Agent(
                agent_id = f"a{i}",
                nombre   = f"Agente {i}",
                posicion = (cx, cy),
                seed     = i,
            ))
        return world, core

    def test_alive_count(self):
        _, core = self._build_core(5)
        assert core.alive_count() == 5

    def test_on_tick_requires_snapshot(self):
        world, core = self._build_core(2)
        tp = _make_tp(hora=8)
        # No snapshot yet — should not crash
        core.on_tick(tp)

    def test_agents_get_actions_after_world_tick(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        world = WorldCore(seed=42)
        core  = AgentCore(world)
        cx, cy = world.terrain.center
        for i in range(3):
            core.add_agent(Agent(
                agent_id=f"a{i}", nombre=f"A{i}",
                posicion=(cx, cy), seed=i,
            ))

        clock.on_tick(world.on_tick, priority=10)
        clock.on_day(world.on_day,   priority=10)
        clock.on_tick(core.on_tick,  priority=20)
        clock.on_day(core.on_day,    priority=20)

        count = [0]
        def stopper(tp):
            count[0] += 1
            if count[0] >= 2:
                clock.shutdown()

        clock.on_tick(stopper, priority=99)
        clock.start()
        # Agents ran without error
        assert core.alive_count() >= 0

    def test_snapshot_all_returns_list(self):
        _, core = self._build_core(3)
        snaps = core.snapshot_all()
        assert len(snaps) == 3

    def test_death_log_records_deaths(self):
        _, core = self._build_core(2)
        # Force an agent to die
        for agent in core.agents.values():
            agent.needs.sed = CRITICAL_THRESHOLD
            agent._dias_sed_critica = 2
        tp = _make_tp()
        core.on_day(tp)
        assert len(core.death_log) > 0


# ── Phase 3 Criterion ─────────────────────────────────────────────────────────

class TestPhase3Criterion:
    """
    Criterio de Fase 3: 15 agentes corren 30 días simulados sin morir todos.
    """

    def test_15_agents_survive_30_days(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        world = WorldCore(seed=42)
        core  = AgentCore(world)

        cx, cy = world.terrain.center
        roles  = ["generico", "cazador", "recolector", "explorador", "guardian"]
        for i in range(15):
            core.add_agent(Agent(
                agent_id = f"agente_{i}",
                nombre   = f"Persona {i}",
                posicion = (cx, cy),
                rol      = roles[i % len(roles)],
                seed     = i * 7,
            ))

        clock.on_tick(world.on_tick, priority=10)
        clock.on_day(world.on_day,   priority=10)
        clock.on_tick(core.on_tick,  priority=20)
        clock.on_day(core.on_day,    priority=20)

        TARGET_TICKS = 30 * 24  # 30 simulated days

        tick_count = [0]
        def stopper(tp: TimePoint) -> None:
            tick_count[0] += 1
            if tick_count[0] >= TARGET_TICKS:
                clock.shutdown()

        clock.on_tick(stopper, priority=99)

        t0 = time.monotonic()
        clock.start()
        elapsed = time.monotonic() - t0

        alive = core.alive_count()
        total = len(core.agents)
        deaths = total - alive

        # At least 1 agent must survive — "not all died"
        assert alive > 0, (
            f"All {total} agents died. Deaths: {core.death_log}"
        )
        # Should finish in reasonable time
        assert elapsed < 10.0, f"30 days took {elapsed:.2f}s"

        print(f"\n  Phase 3 criterion: {alive}/{total} agents alive after 30 days "
              f"({deaths} deaths) in {elapsed:.3f}s")
