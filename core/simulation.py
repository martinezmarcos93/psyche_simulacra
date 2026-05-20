from __future__ import annotations

import atexit
from pathlib import Path

from core.time import SimulationClock, TimePoint
from core.world import WorldCore
from core.agents import AgentCore
from persistence import DatabaseManager, WriteBuffer, CheckpointManager, SessionLog

_DEFAULT_DB          = "data/db/simulation.db"
_DEFAULT_CHECKPOINTS = "data/checkpoints"
_CHECKPOINT_EVERY    = 10   # días simulados


class SimulationRunner:
    """
    Orquestador principal — une SimulationClock, WorldCore, AgentCore y persistencia.

    Siempre usar los constructores de clase:
        SimulationRunner.new_session(seed_file)   ← primera ejecución
        SimulationRunner.resume()                 ← reanudar desde checkpoint
    """

    def __init__(
        self,
        seed:           int = 42,
        db_path:        str = _DEFAULT_DB,
        checkpoint_dir: str = _DEFAULT_CHECKPOINTS,
    ) -> None:
        self.clock  = SimulationClock(start_dia=0, start_hora=0)
        self.world  = WorldCore(seed=seed)
        self.agents = AgentCore(self.world)
        self.db     = DatabaseManager(db_path=db_path)
        self.buffer = WriteBuffer(self.db)
        self.cp_mgr = CheckpointManager(checkpoint_dir=checkpoint_dir, db=self.db)
        self.session = SessionLog(self.db)

        self._last_cp_dia:  int = -1
        self._death_cursor: int = 0

        # NO se llama _wire_handlers() aquí — se llama desde los constructores de clase

    # ── Wiring ───────────────────────────────────────────────────────────────

    def _wire_handlers(self) -> None:
        """Registra todos los handlers en el clock actual."""
        self.clock.on_tick(self.world.on_tick,  priority=10)
        self.clock.on_day(self.world.on_day,    priority=10)

        self.clock.on_tick(self.agents.on_tick, priority=20)
        self.clock.on_day(self.agents.on_day,   priority=20)

        self.clock.on_season_change(self.world.on_season_change,  priority=10)
        self.clock.on_season_change(self.agents.on_season_change, priority=20)

        self.clock.on_tick(self._persist_tick, priority=30)
        self.clock.on_day(self._persist_day,   priority=30)

        atexit.register(self._emergency_save)

    # ── Persistencia per-tick y per-día ──────────────────────────────────────

    def _persist_tick(self, tp: TimePoint) -> None:
        snap = self.world.current_snapshot
        if snap is None:
            return
        self.buffer.add_climate({
            "dia":           tp.dia_simulado,
            "hora":          tp.hora_del_dia,
            "temperatura":   snap.temperatura,
            "precipitacion": snap.precipitacion,
            "luminosidad":   snap.luminosidad,
            "estacion":      snap.estacion,
            "evento":        snap.evento_climatico,
            "survival_risk": snap.survival_risk,
            "mood_modifier": snap.mood_modifier,
        })

    def _persist_day(self, tp: TimePoint) -> None:
        dia = tp.dia_simulado

        # Muertes nuevas — inmediatas a la BD
        death_log  = self.agents.death_log
        new_deaths = death_log[self._death_cursor:]
        if new_deaths:
            self.buffer.record_deaths(new_deaths)
            for _ in new_deaths:
                self.session.record_death()
            self._death_cursor = len(death_log)

        # Snapshots de agentes y escenario (buffered)
        self.buffer.add_agent_snapshots(dia, self.agents.snapshot_all())
        if self.world.current_snapshot is not None:
            self.buffer.add_scenario(dia, self.world.current_snapshot)

        self.session.record_day()

        # Checkpoint automático cada N días
        if dia > 0 and dia % _CHECKPOINT_EVERY == 0 and dia != self._last_cp_dia:
            self._last_cp_dia = dia
            self._save_checkpoint(reason=f"auto_dia_{dia}")
        elif len(self.buffer) >= 200:
            self.buffer.flush()

    def _save_checkpoint(self, reason: str = "auto") -> Path:
        self.buffer.flush()
        path = self.cp_mgr.save(
            world      = self.world,
            agents     = self.agents,
            clock_dict = self.clock.to_dict(),
            session_id = self.session.session_id,
            reason     = reason,
        )
        self.cp_mgr.prune(keep_n=5)
        return path

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def run(self, n_days: int | None = None) -> None:
        """
        Inicia el reloj y bloquea hasta completar n_days o hasta Ctrl+C.
        Si n_days es None, corre indefinidamente.
        """
        if n_days is not None:
            target_dia = self.clock.to_dict().get("dia_simulado", 0) + n_days
            done = [False]

            def _stopper(tp: TimePoint) -> None:
                if not done[0] and tp.dia_simulado >= target_dia:
                    done[0] = True
                    self.clock.shutdown()

            self.clock.on_day(_stopper, priority=99)

        try:
            self.clock.start()
        except KeyboardInterrupt:
            pass
        finally:
            self._shutdown_gracefully()

    def shutdown(self) -> None:
        self.clock.shutdown()

    # ── Cierre limpio ─────────────────────────────────────────────────────────

    def _shutdown_gracefully(self) -> None:
        try:
            self.buffer.flush()
            self.cp_mgr.save(
                world      = self.world,
                agents     = self.agents,
                clock_dict = self.clock.to_dict(),
                session_id = self.session.session_id,
                reason     = "shutdown",
            )
            self.session.close(
                dia_actual = self.clock.to_dict().get("dia_simulado", 0),
                razon      = "normal",
            )
        except Exception:
            pass

    def _emergency_save(self) -> None:
        try:
            self.buffer.flush()
        except Exception:
            pass

    # ── Constructores de clase ────────────────────────────────────────────────

    @classmethod
    def new_session(
        cls,
        seed_file:      str = "data/seeds/initial_personas.yaml",
        seed:           int = 42,
        db_path:        str = _DEFAULT_DB,
        checkpoint_dir: str = _DEFAULT_CHECKPOINTS,
    ) -> SimulationRunner:
        """Crea una nueva simulación desde el archivo de semillas."""
        runner = cls(seed=seed, db_path=db_path, checkpoint_dir=checkpoint_dir)
        runner.agents = AgentCore.from_yaml(seed_file, runner.world)
        runner._wire_handlers()
        runner.session.start(dia_inicio=0)
        return runner

    @classmethod
    def resume(
        cls,
        checkpoint_path: str | None = None,
        db_path:         str = _DEFAULT_DB,
        checkpoint_dir:  str = _DEFAULT_CHECKPOINTS,
    ) -> SimulationRunner:
        """Reanuda desde el checkpoint más reciente (o uno específico)."""
        tmp_cp = CheckpointManager(checkpoint_dir=checkpoint_dir)
        data   = tmp_cp.load(checkpoint_path) if checkpoint_path else tmp_cp.load_latest()

        # El seed del mundo está guardado en data["world"]["seed"]
        seed = data.get("world", {}).get("seed", 42)

        runner = cls(seed=seed, db_path=db_path, checkpoint_dir=checkpoint_dir)

        # Restaurar clock con el día/hora del checkpoint
        runner.clock = SimulationClock.from_dict(data["reloj"])

        # Restaurar mundo (biomas ya generados con el seed correcto)
        runner.world.restore_from_state_dict(data["world"])

        # Restaurar agentes
        runner.agents = AgentCore.from_dict(data["agentes"], runner.world)

        # Re-wiring con el clock y agents restaurados
        runner._wire_handlers()

        dia_inicio = data.get("dia_simulado", 0)
        runner._last_cp_dia  = dia_inicio
        runner._death_cursor = len(runner.agents.death_log)
        runner.session.start(
            dia_inicio = dia_inicio,
            session_id = data.get("session_id"),
        )
        return runner

    # ── Estado ────────────────────────────────────────────────────────────────

    @property
    def alive_count(self) -> int:
        return self.agents.alive_count()

    @property
    def current_dia(self) -> int:
        return self.clock.to_dict().get("dia_simulado", 0)

    def status_line(self) -> str:
        d = self.clock.to_dict()
        return (
            f"Día {d.get('dia_simulado', 0):>4} | "
            f"Hora {d.get('hora_del_dia', 0):>2} | "
            f"{d.get('estacion', '?'):>10} | "
            f"Vivos: {self.alive_count}/{len(self.agents.agents)}"
        )
