from __future__ import annotations

import atexit
from pathlib import Path

from core.time import SimulationClock, TimePoint
from core.world import WorldCore
from core.agents import AgentCore
from core.narrative.narrator import NarratorEngine
from core.metrics import EmergenceMetrics, MetricsExporter
from persistence import DatabaseManager, WriteBuffer, CheckpointManager, SessionLog
from obsidian.sync import ObsidianSync

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
        self.obsidian_sync      = ObsidianSync(vault_path="vault")
        self.narrator           = NarratorEngine(vault_path="vault")
        self.emergence_metrics  = EmergenceMetrics()
        self.metrics_exporter   = MetricsExporter()

        self._last_cp_dia:  int = -1
        self._death_cursor: int = 0

        # Estado interno para detección de eventos narrativos
        self._prev_tribe_ids:    set[str]       = set()
        self._last_cronica_dia:  dict[str, int] = {}
        self._prev_myth_keys:    set[str]       = set()

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
                self.agents.collective_field.absorb_event("muerte", intensity=1.0)
            self._death_cursor = len(death_log)

        # Snapshots de agentes y escenario (buffered)
        self.buffer.add_agent_snapshots(dia, self.agents.snapshot_all())
        if self.world.current_snapshot is not None:
            self.buffer.add_scenario(dia, self.world.current_snapshot)

        self.session.record_day()

        # Eventos narrativos (Fase 3)
        self._queue_narrative_events(dia, new_deaths)

        # Métricas de emergencia (Fase 5)
        day_m = self.emergence_metrics.compute_day(
            dia=dia,
            agents=self.agents.agents,
            tribe_manager=self.agents.tribe_manager,
            collective_field=self.agents.collective_field,
            culture_engine=self.agents.culture_engine,
        )
        self.metrics_exporter.record(day_m)
        if dia % 10 == 0:
            self.metrics_exporter.flush()

        # Sincronizar con el vault de Obsidian (Fase 8)
        self.obsidian_sync.sync_day(
            dia=dia,
            agents=self.agents.agents,
            social_network=self.agents.social_network,
            collective_field=self.agents.collective_field,
            mythology_engine=self.agents.mythology_engine,
            death_log=self.agents.death_log,
            tribe_manager=self.agents.tribe_manager,
            culture_engine=self.agents.culture_engine,
        )

        # Checkpoint automático cada N días
        if dia > 0 and dia % _CHECKPOINT_EVERY == 0 and dia != self._last_cp_dia:
            self._last_cp_dia = dia
            self._save_checkpoint(reason=f"auto_dia_{dia}")
        elif len(self.buffer) >= 200:
            self.buffer.flush()

    def _queue_narrative_events(self, dia: int, new_deaths: list[dict]) -> None:
        """Detecta eventos relevantes y los encola en el narrador."""
        tm      = self.agents.tribe_manager
        terrain = self.world.terrain
        agents  = self.agents.agents

        # 1. Nuevas tribus detectadas (mito fundacional)
        current_tribe_ids = set(tm.tribes.keys())
        for tribe_id in current_tribe_ids - self._prev_tribe_ids:
            member_ids = tm.tribes.get(tribe_id, [])
            alive      = [agents[aid] for aid in member_ids if aid in agents and agents[aid].is_alive]
            nombres    = [a.nombre for a in alive]
            arquetipo  = alive[0].archetypes.dominant() if alive else "heroe"
            # Bioma dominante
            bioma_counts: dict[str, int] = {}
            for a in alive:
                hx = terrain.get(*a.posicion)
                if hx:
                    bioma_counts[hx.biome] = bioma_counts.get(hx.biome, 0) + 1
            bioma = max(bioma_counts, key=bioma_counts.__getitem__) if bioma_counts else "tierra desconocida"
            lf = tm.local_fields.get(tribe_id)
            simbolos = lf.symbols if lf else {}
            self.narrator.on_new_tribe(tribe_id, dia, {
                "tribe_name": tm.get_tribe_display_name(tribe_id, agents),
                "nombres":    nombres,
                "bioma":      bioma,
                "arquetipo":  arquetipo,
                "simbolos":   dict(simbolos),
            })
        self._prev_tribe_ids = current_tribe_ids

        # 2. Crónica periódica por tribu (cada 100 días)
        for tribe_id, member_ids in tm.tribes.items():
            last = self._last_cronica_dia.get(tribe_id, -100)
            if dia - last >= 100:
                self._last_cronica_dia[tribe_id] = dia
                alive = [agents[aid] for aid in member_ids if aid in agents and agents[aid].is_alive]
                arquetipo   = alive[0].archetypes.dominant() if alive else "heroe"
                lf          = tm.local_fields.get(tribe_id)
                presion     = lf.emotional_pressure if lf else 0.0
                simbolo_dom = max(lf.symbols, key=lf.symbols.__getitem__) if lf and lf.symbols else "sombra"
                # Eventos recientes: últimas muertes + nacimientos del log
                eventos = [
                    f"Muerte de {d['nombre']} (día {d['dia']}, {d['causa']})"
                    for d in self.agents.death_log[-10:]
                    if d.get("agent_id") in set(member_ids)
                ] + [
                    f"Nacimiento de {b['nombre']} (día {b['dia']})"
                    for b in self.agents.birth_log[-5:]
                    if b.get("padre_a") in set(member_ids) or b.get("padre_b") in set(member_ids)
                ]
                self.narrator.on_cronica_day(tribe_id, dia, {
                    "tribe_name":  tm.get_tribe_display_name(tribe_id, agents),
                    "dia_inicio":  last + 1,
                    "n_miembros":  len(alive),
                    "arquetipo":   arquetipo,
                    "presion":     presion,
                    "simbolo_dom": simbolo_dom,
                    "eventos":     eventos,
                })

        # 3. Elegías para muertes de figuras prominentes (arquetipo dominante > 0.70)
        for death in new_deaths:
            aid  = death.get("agent_id", "")
            dead = agents.get(aid)
            if dead is None:
                continue
            raw  = dead.archetypes.dominant()
            attr = "self_" if raw == "self" else raw
            val  = getattr(dead.archetypes, attr, 0.0)
            if val >= 0.70:
                tribe_id = tm.get_tribe_id(aid)
                self.narrator.on_death(aid, dia, {
                    "nombre":     dead.nombre,
                    "edad":       dead.edad,
                    "causa":      death.get("causa", "causas desconocidas"),
                    "arquetipo":  raw,
                    "tribe_name": tm.get_tribe_display_name(tribe_id, agents) if tribe_id else "sin tribu",
                    "memorias":   dead.episodic_log[-5:],
                    "agent_id":   aid,
                })

        # 4. Profecías por cristalización de mitos (global y locales)
        all_myth_engines = [
            (None, self.agents.mythology_engine)
        ] + [
            (tid, me) for tid, me in tm.local_myths.items()
        ]
        for tribe_id, myth_engine in all_myth_engines:
            for myth in myth_engine.active_myths:
                if not myth.get("active"):
                    continue
                key = f"{tribe_id or 'global'}_{myth.get('day_crystallized', 0)}"
                if key in self._prev_myth_keys:
                    continue
                self._prev_myth_keys.add(key)
                hero_id    = myth.get("hero_id")
                monster_id = myth.get("monster_id")
                hero_name  = agents[hero_id].nombre if hero_id and hero_id in agents else "el Elegido"
                mon_name   = agents[monster_id].nombre if monster_id and monster_id in agents else "la Sombra"
                t_id       = tribe_id or (tm.get_tribe_id(hero_id) if hero_id else None)
                lf         = tm.local_fields.get(t_id) if t_id else self.agents.collective_field
                self.narrator.on_myth_crystallized(t_id or "global", dia, {
                    "tribe_name":    tm.get_tribe_display_name(t_id, agents) if t_id else "el Campo Global",
                    "arquetipo":     "heroe",
                    "heroe_nombre":  hero_name,
                    "antagonista":   mon_name,
                    "presion":       lf.emotional_pressure if lf else 0.0,
                    "simbolos":      dict(lf.symbols) if lf else {},
                })

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

        # Parar si todos mueren
        def _extinction_check(tp: TimePoint) -> None:
            if self.alive_count == 0:
                print(f"\n[💀] EXTINCIÓN TOTAL detectada en el Día {tp.dia_simulado}. Deteniendo simulación.")
                self.clock.shutdown()
        
        self.clock.on_day(_extinction_check, priority=100)

        self.narrator.start()
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
        # Esperar a que el narrador termine los eventos pendientes
        try:
            self.narrator.drain(timeout=60)
            self.narrator.stop()
        except Exception:
            pass
        try:
            self.metrics_exporter.flush()
            self.metrics_exporter.export_summary()
        except Exception:
            pass
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
        # Limpiar base de datos vieja
        db_file = Path(db_path)
        if db_file.exists():
            try:
                db_file.unlink()
                Path(f"{db_path}-wal").unlink(missing_ok=True)
                Path(f"{db_path}-shm").unlink(missing_ok=True)
            except Exception:
                pass

        # Limpiar checkpoints viejos
        cp_path = Path(checkpoint_dir)
        if cp_path.exists():
            for f in cp_path.glob("checkpoint_*.json"):
                try:
                    f.unlink()
                except Exception:
                    pass

        # Limpiar archivos viejos del Obsidian vault
        vault_dir = Path("vault")
        if vault_dir.exists():
            for sub in ["Personas", "Colectivo", "Meta", "Tribus"]:
                sub_dir = vault_dir / sub
                if sub_dir.exists():
                    for f in sub_dir.glob("*.md"):
                        try:
                            f.unlink()
                        except Exception:
                            pass
            # Subcarpeta de leyendas narrativas
            leyendas_dir = vault_dir / "Colectivo" / "Leyendas"
            if leyendas_dir.exists():
                for f in leyendas_dir.glob("*.md"):
                    try:
                        f.unlink()
                    except Exception:
                        pass

        runner = cls(seed=seed, db_path=db_path, checkpoint_dir=checkpoint_dir)
        runner.agents = AgentCore.from_yaml(seed_file, runner.world)
        runner.obsidian_sync.sync_from_vault(runner.agents.agents)
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
        runner.obsidian_sync.sync_from_vault(runner.agents.agents)

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
