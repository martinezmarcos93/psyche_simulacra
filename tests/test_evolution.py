"""
Tests para la arquitectura evolution:
  Fase 0 — EventBus, RuntimeState, ServiceManager (estructura base)
  Fase 1 — Bridge clock → EventBus (WorldTickEvent, WorldDayEvent)
"""
from __future__ import annotations

import time
import threading
from typing import Any

import pytest

from core.runtime.event_bus import EventBus, AsyncQueueHandler
from core.runtime.event_types import (
    WorldTickEvent,
    WorldDayEvent,
    WorldSeasonChangeEvent,
    AgentDiedEvent,
    ServiceHealthEvent,
)
from core.runtime.runtime_state import RuntimeState
from core.runtime.psyche_runtime import PsycheRuntime

from core.time.simulation_clock import SimulationClock, TimePoint
from core.world.world_core import WorldCore
from core.agents.agent_core import AgentCore
from core.agents.agent import Agent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_tp(tick: int = 0, dia: int = 0, hora: int = 0) -> TimePoint:
    from core.time.simulation_clock import SimulationClock
    c = SimulationClock(start_dia=dia, start_hora=hora)
    return c._make_timepoint()


# ══════════════════════════════════════════════════════════════════════════════
# Fase 0 — EventBus
# ══════════════════════════════════════════════════════════════════════════════

class TestEventBus:

    def test_sync_subscribe_and_emit(self):
        bus = EventBus()
        received = []
        bus.subscribe(WorldTickEvent, received.append, priority=10)

        tp = _make_tp()
        bus.emit(WorldTickEvent(tick=1, timepoint=tp))
        assert len(received) == 1
        assert received[0].tick == 1

    def test_multiple_sync_handlers_ordered_by_priority(self):
        bus = EventBus()
        order = []
        bus.subscribe(WorldDayEvent, lambda e: order.append("b"), priority=20)
        bus.subscribe(WorldDayEvent, lambda e: order.append("a"), priority=10)

        bus.emit(WorldDayEvent(dia=1, season="verano"))
        assert order == ["a", "b"]

    def test_unsubscribe_sync(self):
        bus = EventBus()
        received = []
        handler = received.append
        bus.subscribe(WorldDayEvent, handler, priority=10)
        bus.unsubscribe(WorldDayEvent, handler)
        bus.emit(WorldDayEvent(dia=1, season="verano"))
        assert received == []

    def test_async_handler_receives_event(self):
        bus = EventBus()
        received = []
        event = threading.Event()

        def slow_handler(e):
            received.append(e)
            event.set()

        bus.subscribe(ServiceHealthEvent, slow_handler, priority=50)
        bus.emit(ServiceHealthEvent(service="test", state="running", detail="ok"))

        assert event.wait(timeout=2), "Async handler did not fire in time"
        assert received[0].service == "test"
        bus.shutdown()

    def test_no_handler_for_type_does_not_crash(self):
        bus = EventBus()
        bus.emit(WorldSeasonChangeEvent(old_season="invierno", new_season="primavera", dia=90))

    def test_emit_does_not_block_when_async_queue_full(self):
        """Queue llena → evento descartado silenciosamente, no se bloquea el caller."""
        bus = EventBus()
        blocker = threading.Event()

        def blocking_handler(e):
            blocker.wait(timeout=30)

        bus.subscribe(ServiceHealthEvent, blocking_handler, priority=50)

        start = time.monotonic()
        for _ in range(600):
            bus.emit(ServiceHealthEvent(service="x", state="running", detail=""))
        elapsed = time.monotonic() - start
        blocker.set()
        bus.shutdown()

        assert elapsed < 1.0, f"emit blocked for {elapsed:.2f}s — queue did not drop events"


# ══════════════════════════════════════════════════════════════════════════════
# Fase 0 — RuntimeState
# ══════════════════════════════════════════════════════════════════════════════

class TestRuntimeState:

    def test_default_state(self):
        s = RuntimeState()
        assert s.simulation == "stopped"
        assert s.ollama == "stopped"
        assert s.dia_simulado == 0

    def test_to_dict(self):
        s = RuntimeState(simulation="running", dia_simulado=42)
        d = s.to_dict()
        assert d["simulation"] == "running"
        assert d["dia_simulado"] == 42
        assert "timestamp_real" in d


# ══════════════════════════════════════════════════════════════════════════════
# Fase 0 — PsycheRuntime estructura base
# ══════════════════════════════════════════════════════════════════════════════

class TestPsycheRuntime:

    def test_instantiation(self):
        rt = PsycheRuntime()
        assert rt.bus is not None
        assert rt.state.simulation == "stopped"

    def test_subscribe_and_get_state(self):
        rt = PsycheRuntime()
        received = []
        rt.subscribe(WorldDayEvent, received.append, priority=10)
        rt.bus.emit(WorldDayEvent(dia=5, season="otoño"))
        assert len(received) == 1
        assert received[0].dia == 5

    def test_get_state_without_runner(self):
        rt = PsycheRuntime()
        s = rt.get_state()
        assert s.simulation == "stopped"
        assert s.agentes_vivos == 0


# ══════════════════════════════════════════════════════════════════════════════
# Fase 1 — Bridge clock → EventBus
# ══════════════════════════════════════════════════════════════════════════════

class TestClockEventBridge:

    def _build_runner_stub(self):
        """Construye un SimulationRunner mínimo (sin BD, sin vault)."""
        from core.simulation import SimulationRunner
        runner = SimulationRunner.__new__(SimulationRunner)
        runner.clock  = SimulationClock(start_dia=0, start_hora=0)
        runner.world  = WorldCore(seed=42)
        runner.agents = AgentCore(runner.world)
        runner._last_cp_dia    = -1
        runner._death_cursor   = 0
        runner._prev_tribe_ids = set()
        runner._last_cronica_dia = {}
        runner._prev_myth_keys = set()
        runner.clock.on_tick(runner.world.on_tick,  priority=10)
        runner.clock.on_day(runner.world.on_day,    priority=10)
        runner.clock.on_tick(runner.agents.on_tick, priority=20)
        runner.clock.on_day(runner.agents.on_day,   priority=20)
        runner.clock.on_season_change(runner.world.on_season_change,  priority=10)
        runner.clock.on_season_change(runner.agents.on_season_change, priority=20)
        return runner

    def test_world_tick_events_emitted(self):
        rt     = PsycheRuntime()
        runner = self._build_runner_stub()
        rt.attach_runner(runner)

        ticks_received: list[WorldTickEvent] = []
        rt.subscribe(WorldTickEvent, ticks_received.append, priority=10)

        n_ticks   = 5
        stopper   = [0]

        def _stop(tp: TimePoint) -> None:
            stopper[0] += 1
            if stopper[0] >= n_ticks:
                runner.clock.shutdown()

        runner.clock.on_tick(_stop, priority=99)
        runner.clock.start()

        assert len(ticks_received) == n_ticks

    def test_world_day_events_emitted(self):
        rt     = PsycheRuntime()
        runner = self._build_runner_stub()
        rt.attach_runner(runner)

        days_received: list[WorldDayEvent] = []
        rt.subscribe(WorldDayEvent, days_received.append, priority=10)

        ticks = [0]

        def _stop(tp: TimePoint) -> None:
            ticks[0] += 1
            if ticks[0] >= 49:  # 2 días completos + 1 tick
                runner.clock.shutdown()

        runner.clock.on_tick(_stop, priority=99)
        runner.clock.start()

        # on_day fires at tick 0 (hora=0) and tick 24 (hora=0)
        assert len(days_received) >= 2
        assert days_received[0].dia == 0
        assert days_received[1].dia == 1

    def test_runtime_state_updates_after_day(self):
        rt     = PsycheRuntime()
        runner = self._build_runner_stub()

        # Añadir un agente para que alive_count > 0
        cx, cy = runner.world.terrain.center
        runner.agents.add_agent(Agent(agent_id="test1", nombre="Test", posicion=(cx, cy)))
        rt.attach_runner(runner)

        ticks = [0]

        def _stop(tp: TimePoint) -> None:
            ticks[0] += 1
            if ticks[0] >= 25:
                runner.clock.shutdown()

        runner.clock.on_tick(_stop, priority=99)
        runner.clock.start()

        state = rt.get_state()
        assert state.dia_simulado >= 1

    def test_bridge_is_parallel_existing_handlers_still_fire(self):
        """El bridge no reemplaza los handlers existentes: simulación avanza Y EventBus recibe días."""
        rt     = PsycheRuntime()
        runner = self._build_runner_stub()
        cx, cy = runner.world.terrain.center
        runner.agents.add_agent(Agent(agent_id="a1", nombre="Ana", posicion=(cx, cy)))
        rt.attach_runner(runner)

        days_on_bus: list[WorldDayEvent] = []
        rt.subscribe(WorldDayEvent, days_on_bus.append, priority=10)

        ticks = [0]

        def _stop(tp: TimePoint) -> None:
            ticks[0] += 1
            if ticks[0] >= 25:
                runner.clock.shutdown()

        runner.clock.on_tick(_stop, priority=99)
        runner.clock.start()

        # El bus debe haber recibido al menos 1 día
        assert len(days_on_bus) >= 1, "Bridge should emit WorldDayEvent"
        # El snapshot del mundo debe existir (indica que world.on_day corrió también)
        assert runner.world.current_snapshot is not None, "world.on_day must still fire"
