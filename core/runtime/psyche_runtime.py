"""
PsycheRuntime — orquestador central de PSYCHE SIMULACRA.

Única fuente de verdad sobre qué está corriendo. La UI y cualquier
observer se conectan aquí; nunca tocan SimulationRunner directamente.

Fase 0: estructura base + EventBus instanciado.
Fase 1: bridge clock → EventBus activo (WorldTickEvent, WorldDayEvent).
Fase 4: ServiceManager operativo.
Fase 5: NiceGUI UI conectada.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, TYPE_CHECKING

from .event_bus import EventBus
from .event_types import (
    WorldTickEvent,
    WorldDayEvent,
    WorldSeasonChangeEvent,
    AgentBornEvent,
    AgentDiedEvent,
    NarrativeRequestEvent,
)
from .runtime_state import RuntimeState
from .service_manager import ServiceManager
from .snapshot_pipeline import SnapshotPipeline

if TYPE_CHECKING:
    from core.time.simulation_clock import TimePoint
    from core.simulation import SimulationRunner


class PsycheRuntime:
    """
    Punto de entrada único. La UI y los observers se conectan aquí.

    Doctrina A: el runtime es la realidad canónica.
    Doctrina B: la simulación existe sin observers.
    Doctrina C: el usuario observa, no controla.
    """

    def __init__(self) -> None:
        self.bus:               EventBus         = EventBus()
        self.state:             RuntimeState     = RuntimeState()
        self.services:          ServiceManager   = ServiceManager(self.bus)
        self.snapshot_pipeline: SnapshotPipeline = SnapshotPipeline(self.bus)

        self._runner:  SimulationRunner | None = None
        self._lock     = threading.Lock()

    # ── Ciclo de vida de la simulación ────────────────────────────────────────

    def attach_runner(self, runner: "SimulationRunner") -> None:
        """
        Conecta un SimulationRunner ya construido al runtime.
        Registra el bridge clock→EventBus (Fase 1).
        """
        with self._lock:
            self._runner = runner

        self._wire_event_bridge(runner)
        self._wire_narrator_bridge(runner)
        runner.attach_bus(self.bus)
        self.state.simulation = "stopped"

    def detach_runner(self) -> None:
        with self._lock:
            self._runner = None
        self.state.simulation = "stopped"

    # ── EventBus API pública ──────────────────────────────────────────────────

    def subscribe(
        self,
        event_type: type,
        handler: Callable[[Any], None],
        priority: int = 50,
    ) -> None:
        self.bus.subscribe(event_type, handler, priority)

    def unsubscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        self.bus.unsubscribe(event_type, handler)

    # ── Estado observable ─────────────────────────────────────────────────────

    def get_state(self) -> RuntimeState:
        runner = self._get_runner()
        if runner is not None:
            self._sync_state_from_runner(runner)
        return self.state

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def get_current_snapshot(self) -> dict | None:
        """Retorna el WorldSnapshot actual serializado, o None si no hay runner."""
        runner = self._get_runner()
        if runner is None:
            return None
        snap = runner.world.current_snapshot
        if snap is None:
            return None
        return snap.to_dict() if hasattr(snap, "to_dict") else None

    # ── Ciclo de vida del runtime ─────────────────────────────────────────────

    def shutdown(self) -> None:
        self.services.shutdown_all()
        self.bus.shutdown()
        self.state.simulation = "stopped"

    # ── SnapshotPipeline API (Fase 3) ─────────────────────────────────────────

    def subscribe_snapshots(self, handler) -> None:
        self.snapshot_pipeline.subscribe(handler)

    def unsubscribe_snapshots(self, handler) -> None:
        self.snapshot_pipeline.unsubscribe(handler)

    # ── Bridge clock→EventBus (Fase 1) ────────────────────────────────────────

    def _wire_event_bridge(self, runner: "SimulationRunner") -> None:
        """
        Registra handlers en el clock que emiten eventos al bus.
        Priority=15: después del mundo (10), antes de los agentes (20).
        No modifica los handlers existentes — canal paralelo puro.
        """
        bus = self.bus

        def _tick_bridge(tp: "TimePoint") -> None:
            bus.emit(WorldTickEvent(tick=tp.tick, timepoint=tp))

        def _day_bridge(tp: "TimePoint") -> None:
            snap  = runner.world.current_snapshot
            clima = None
            if snap is not None and hasattr(snap, "clima"):
                clima = snap.clima.__dict__ if hasattr(snap.clima, "__dict__") else {"raw": str(snap.clima)}
            bus.emit(WorldDayEvent(
                dia    = tp.dia_simulado,
                season = tp.estacion,
                climate= clima,
            ))
            # Fase 3: broadcast snapshot a todos los observers suscritos
            if snap is not None:
                snap_dict = snap.to_dict() if hasattr(snap, "to_dict") else {}
                self.snapshot_pipeline.broadcast(snap_dict, tp.tick)
            self._sync_state_from_runner(runner)

        _prev_season: list[str] = [runner.clock.now.estacion]

        def _season_bridge(tp: "TimePoint") -> None:
            bus.emit(WorldSeasonChangeEvent(
                old_season = _prev_season[0],
                new_season = tp.estacion,
                dia        = tp.dia_simulado,
            ))
            _prev_season[0] = tp.estacion

        runner.clock.on_tick(          _tick_bridge,   priority=15)
        runner.clock.on_day(           _day_bridge,    priority=15)
        runner.clock.on_season_change( _season_bridge, priority=15)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_runner(self) -> "SimulationRunner | None":
        with self._lock:
            return self._runner

    # ── NarratorEngine → EventBus (Fase 2) ───────────────────────────────────

    def _wire_narrator_bridge(self, runner: "SimulationRunner") -> None:
        """Suscribe el NarratorEngine al bus para recibir NarrativeRequestEvents."""
        narrator = getattr(runner, "narrator", None)
        if narrator is None:
            return
        self.bus.subscribe(NarrativeRequestEvent, narrator.handle_bus_event, priority=60)

    def _sync_state_from_runner(self, runner: "SimulationRunner") -> None:
        try:
            cd = runner.clock.to_dict()
            self.state.dia_simulado  = cd.get("dia_simulado", 0)
            self.state.agentes_vivos = runner.alive_count
            tribes = runner.agents.tribe_manager.tribes
            self.state.tribus_activas = sum(1 for t in tribes.values() if getattr(t, "is_active", True))
        except Exception:
            pass
