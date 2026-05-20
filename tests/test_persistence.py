"""
Tests de Persistencia — Fase 4.
Cubre DatabaseManager, WriteBuffer, CheckpointManager y SessionLog.
Criterio de fase: cerrar y reanudar es transparente para la simulación.
"""
import json
import time
import tempfile
from pathlib import Path

import pytest

from core.time import SimulationClock, TimePoint
from core.world import WorldCore
from core.agents import Agent, AgentCore
from persistence import DatabaseManager, WriteBuffer, CheckpointManager, SessionLog


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    db = DatabaseManager(db_path=str(tmp_path / "test.db"))
    yield db
    db.close()


@pytest.fixture
def tmp_checkpoint_dir(tmp_path):
    return tmp_path / "checkpoints"


@pytest.fixture
def world_and_agents():
    world = WorldCore(seed=42)
    core  = AgentCore(world)
    cx, cy = world.terrain.center
    for i in range(5):
        core.add_agent(Agent(
            agent_id=f"a{i}", nombre=f"Agente {i}",
            posicion=(cx, cy), seed=i,
        ))
    return world, core


def _run_ticks(world: WorldCore, agents: AgentCore, n_ticks: int) -> dict:
    clock = SimulationClock(start_dia=0, start_hora=0)
    clock.on_tick(world.on_tick,  priority=10)
    clock.on_day(world.on_day,    priority=10)
    clock.on_tick(agents.on_tick, priority=20)
    clock.on_day(agents.on_day,   priority=20)

    count = [0]
    clock_state = [{}]

    def stopper(tp: TimePoint) -> None:
        count[0] += 1
        clock_state[0] = clock.to_dict()
        if count[0] >= n_ticks:
            clock.shutdown()

    clock.on_tick(stopper, priority=99)
    clock.start()
    return clock_state[0]


# ── DatabaseManager ───────────────────────────────────────────────────────────

class TestDatabaseManager:

    def test_crea_archivo_db(self, tmp_db, tmp_path):
        assert (tmp_path / "test.db").exists()

    def test_insert_agent_snapshots(self, tmp_db):
        agents_data = [
            {"id": "a1", "nombre": "Ana", "posicion": [40, 30],
             "rol": "generico", "is_alive": True,
             "needs": {"hambre": 0.2, "fatiga": 0.1, "sed": 0.3},
             "humor": 0.7, "energia": 0.8, "ansiedad": 0.1},
        ]
        tmp_db.insert_agent_snapshots(dia=5, agents_data=agents_data)
        result = tmp_db.get_agent_snapshot("a1", dia=5)
        assert result is not None
        assert result["nombre"] == "Ana"

    def test_insert_death(self, tmp_db):
        tmp_db.insert_death({
            "tick": 72, "dia": 3,
            "agent_id": "a2", "nombre": "Luis", "causa": "deshidratacion",
        })
        deaths = tmp_db.get_deaths(desde_dia=0)
        assert len(deaths) == 1
        assert deaths[0]["causa"] == "deshidratacion"

    def test_insert_deaths_batch(self, tmp_db):
        deaths = [
            {"tick": i*24, "dia": i, "agent_id": f"a{i}", "nombre": f"N{i}", "causa": "inanicion"}
            for i in range(3)
        ]
        tmp_db.insert_deaths_batch(deaths)
        result = tmp_db.get_deaths()
        assert len(result) == 3

    def test_insert_climate_batch(self, tmp_db):
        rows = [
            {"dia": 1, "hora": h, "temperatura": 18.0 + h,
             "precipitacion": 0.3, "luminosidad": 0.8,
             "estacion": "primavera", "evento": None,
             "survival_risk": 0.0, "mood_modifier": 0.1}
            for h in range(24)
        ]
        tmp_db.insert_climate_batch(rows)
        # No error = pass; verificar via consulta directa
        cur = tmp_db._conn.execute("SELECT COUNT(*) FROM climate_log")
        assert cur.fetchone()[0] == 24

    def test_upsert_session(self, tmp_db):
        tmp_db.upsert_session({
            "session_id":          "sess-001",
            "timestamp_inicio":    "2026-01-01T00:00:00+00:00",
            "dia_inicio_simulado": 0,
            "version_motor":       "0.1.0",
        })
        cur = tmp_db._conn.execute("SELECT * FROM session_log WHERE session_id=?", ("sess-001",))
        row = cur.fetchone()
        assert row is not None
        assert row["version_motor"] == "0.1.0"

    def test_insert_checkpoint_meta(self, tmp_db):
        tmp_db.insert_checkpoint_meta({
            "checkpoint_id":  "cp-001",
            "dia_simulado":   10,
            "hora_simulada":  0,
            "timestamp_real": "2026-01-01T00:00:00+00:00",
            "session_id":     "sess-001",
            "razon":          "auto",
            "archivo_json":   "/tmp/checkpoint_00010.json",
        })
        cur = tmp_db._conn.execute(
            "SELECT * FROM simulation_checkpoints WHERE checkpoint_id=?", ("cp-001",)
        )
        assert cur.fetchone() is not None


# ── WriteBuffer ───────────────────────────────────────────────────────────────

class TestWriteBuffer:

    def test_buffer_vacio_al_crear(self, tmp_db):
        buf = WriteBuffer(tmp_db)
        assert len(buf) == 0

    def test_record_deaths_inmediato(self, tmp_db):
        buf = WriteBuffer(tmp_db)
        buf.record_deaths([{
            "tick": 10, "dia": 1,
            "agent_id": "a1", "nombre": "Test", "causa": "inanicion",
        }])
        # Debe estar en BD sin hacer flush
        deaths = tmp_db.get_deaths()
        assert len(deaths) == 1

    def test_climate_se_acumula_y_flush(self, tmp_db):
        buf = WriteBuffer(tmp_db)
        for h in range(5):
            buf.add_climate({
                "dia": 0, "hora": h, "temperatura": 20.0,
                "precipitacion": 0.3, "luminosidad": 0.8,
                "estacion": "primavera", "evento": None,
                "survival_risk": 0.0, "mood_modifier": 0.1,
            })
        assert len(buf) == 5
        written = buf.flush()
        assert written == 5
        assert len(buf) == 0

    def test_agent_snapshots_buffered(self, tmp_db):
        buf = WriteBuffer(tmp_db)
        agents_data = [
            {"id": "a1", "nombre": "X", "posicion": [40, 30], "rol": "generico",
             "is_alive": True, "needs": {"hambre": 0.1, "fatiga": 0.1, "sed": 0.1},
             "humor": 0.5, "energia": 0.5, "ansiedad": 0.2},
        ]
        buf.add_agent_snapshots(dia=1, agents_data=agents_data)
        assert len(buf) == 1
        buf.flush()
        result = tmp_db.get_agent_snapshot("a1", dia=1)
        assert result is not None

    def test_auto_flush_al_superar_max_size(self, tmp_db):
        buf = WriteBuffer(tmp_db, max_size=3)
        for h in range(4):  # supera max_size en el ítem 3
            buf.add_climate({
                "dia": 0, "hora": h, "temperatura": 20.0,
                "precipitacion": 0.3, "luminosidad": 0.8,
                "estacion": "primavera", "evento": None,
                "survival_risk": 0.0, "mood_modifier": 0.1,
            })
        # Los primeros 3 ítems se flushearon solos; queda 1 en buffer
        assert len(buf) == 1
        # La BD ya tiene filas escritas sin haber llamado flush() explícitamente
        cur = tmp_db._conn.execute("SELECT COUNT(*) FROM climate_log")
        assert cur.fetchone()[0] >= 3


# ── CheckpointManager ─────────────────────────────────────────────────────────

class TestCheckpointManager:

    def test_save_crea_archivo(self, world_and_agents, tmp_checkpoint_dir):
        world, agents = world_and_agents
        clock_dict    = {"dia_simulado": 0, "hora_del_dia": 0, "estacion": "primavera"}
        mgr  = CheckpointManager(str(tmp_checkpoint_dir))
        path = mgr.save(world, agents, clock_dict, session_id="s1", reason="test")
        assert path.exists()

    def test_save_archivo_es_json_valido(self, world_and_agents, tmp_checkpoint_dir):
        world, agents = world_and_agents
        mgr  = CheckpointManager(str(tmp_checkpoint_dir))
        path = mgr.save(world, agents, {"dia_simulado": 0, "hora_del_dia": 0})
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "checkpoint_id" in data
        assert "agentes" in data
        assert "world" in data

    def test_verify_ok_en_checkpoint_valido(self, world_and_agents, tmp_checkpoint_dir):
        world, agents = world_and_agents
        mgr  = CheckpointManager(str(tmp_checkpoint_dir))
        path = mgr.save(world, agents, {"dia_simulado": 5, "hora_del_dia": 12})
        ok, msg = mgr.verify(path)
        assert ok, msg

    def test_verify_falla_en_archivo_corrupto(self, tmp_checkpoint_dir):
        tmp_checkpoint_dir.mkdir(parents=True, exist_ok=True)
        bad = tmp_checkpoint_dir / "checkpoint_bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        mgr = CheckpointManager(str(tmp_checkpoint_dir))
        ok, _ = mgr.verify(bad)
        assert not ok

    def test_load_latest_devuelve_datos(self, world_and_agents, tmp_checkpoint_dir):
        world, agents = world_and_agents
        mgr = CheckpointManager(str(tmp_checkpoint_dir))
        mgr.save(world, agents, {"dia_simulado": 10, "hora_del_dia": 0})
        data = mgr.load_latest()
        assert data["dia_simulado"] == 10

    def test_load_latest_falla_sin_checkpoints(self, tmp_checkpoint_dir):
        tmp_checkpoint_dir.mkdir(parents=True, exist_ok=True)
        mgr = CheckpointManager(str(tmp_checkpoint_dir))
        with pytest.raises(FileNotFoundError):
            mgr.load_latest()

    def test_prune_elimina_checkpoints_viejos(self, world_and_agents, tmp_checkpoint_dir):
        world, agents = world_and_agents
        mgr = CheckpointManager(str(tmp_checkpoint_dir))
        for dia in range(7):
            mgr.save(world, agents, {"dia_simulado": dia, "hora_del_dia": 0})
        assert len(mgr.list_checkpoints()) == 7
        mgr.prune(keep_n=3)
        assert len(mgr.list_checkpoints()) == 3

    def test_list_checkpoints_ordenados_recientes_primero(self, world_and_agents, tmp_checkpoint_dir):
        world, agents = world_and_agents
        mgr = CheckpointManager(str(tmp_checkpoint_dir))
        for dia in [1, 5, 10]:
            mgr.save(world, agents, {"dia_simulado": dia, "hora_del_dia": 0})
        cp_list = mgr.list_checkpoints()
        nombres = [p.name for p in cp_list]
        # El más reciente (día 10) debe estar primero
        assert nombres[0] > nombres[-1]


# ── SessionLog ────────────────────────────────────────────────────────────────

class TestSessionLog:

    def test_start_genera_session_id(self, tmp_db):
        sl = SessionLog(tmp_db)
        sid = sl.start(dia_inicio=0)
        assert sid != ""
        assert sl.is_active

    def test_close_desactiva_sesion(self, tmp_db):
        sl = SessionLog(tmp_db)
        sl.start()
        sl.close(dia_actual=5, razon="normal")
        assert not sl.is_active

    def test_record_day_incrementa_contador(self, tmp_db):
        sl = SessionLog(tmp_db)
        sl.start()
        sl.record_day()
        sl.record_day()
        assert sl.dias_procesados == 2

    def test_record_death_incrementa_contador(self, tmp_db):
        sl = SessionLog(tmp_db)
        sl.start()
        sl.record_death()
        sl.record_death()
        assert sl._muertes == 2

    def test_close_persiste_en_db(self, tmp_db):
        sl  = SessionLog(tmp_db)
        sid = sl.start(dia_inicio=0)
        sl.record_day()
        sl.close(dia_actual=1, razon="normal")
        cur = tmp_db._conn.execute(
            "SELECT razon_fin FROM session_log WHERE session_id=?", (sid,)
        )
        row = cur.fetchone()
        assert row is not None
        assert row["razon_fin"] == "normal"

    def test_close_doble_no_falla(self, tmp_db):
        sl = SessionLog(tmp_db)
        sl.start()
        sl.close()
        sl.close()  # segunda vez — no debe explotar


# ── Criterio de Fase 4: checkpoint transparente ───────────────────────────────

class TestPhase4Criterion:
    """
    Criterio: cerrar y reanudar es transparente para la simulación.
    Se verifica que el estado restaurado desde checkpoint coincide con el original.
    """

    def test_checkpoint_roundtrip_world_state(self, tmp_path):
        world  = WorldCore(seed=42)
        agents = AgentCore(world)
        cx, cy = world.terrain.center
        for i in range(5):
            agents.add_agent(Agent(
                agent_id=f"a{i}", nombre=f"P{i}",
                posicion=(cx, cy), seed=i,
            ))

        # Correr 3 días para que haya estado no-trivial
        clock_state = _run_ticks(world, agents, n_ticks=3 * 24)

        mgr   = CheckpointManager(str(tmp_path / "cp"))
        path  = mgr.save(world, agents, clock_state, session_id="test", reason="test")

        # ── Restaurar en instancias nuevas ──────────────────────────────────
        data = mgr.load(path)

        world2  = WorldCore(seed=42)
        agents2 = AgentCore(world2)
        world2.restore_from_state_dict(data["world"])
        agents2_dict = data["agentes"]

        # Verificar que el número de agentes coincide
        assert len(agents2_dict["agents"]) == len(agents.agents)

        # Verificar estado del fuego
        assert world2.fire.is_active == world.fire.is_active

        # Verificar hexes explorados
        orig_explored  = set(map(tuple, data["world"]["explored_coords"]))
        rest_explored  = set(world2.terrain.explored_coords())
        assert orig_explored == rest_explored

    def test_checkpoint_incluye_needs_de_agentes(self, tmp_path):
        world  = WorldCore(seed=42)
        agents = AgentCore(world)
        cx, cy = world.terrain.center
        agents.add_agent(Agent(agent_id="a0", nombre="P0", posicion=(cx, cy), seed=0))

        clock_state = _run_ticks(world, agents, n_ticks=24)

        mgr  = CheckpointManager(str(tmp_path / "cp"))
        path = mgr.save(world, agents, clock_state)
        data = mgr.load(path)

        agent_dict = data["agentes"]["agents"][0]
        needs = agent_dict.get("needs", {})
        # Después de 24 ticks las necesidades deben haber aumentado
        assert needs.get("hambre", 0) > 0 or needs.get("sed", 0) > 0

    def test_database_registra_deaths_durante_simulacion(self, tmp_path):
        db    = DatabaseManager(db_path=str(tmp_path / "sim.db"))
        buf   = WriteBuffer(db)
        world = WorldCore(seed=42)
        agents = AgentCore(world)
        cx, cy = world.terrain.center

        # Agente en estado crítico
        moribundo = Agent(agent_id="doom", nombre="Doom", posicion=(cx, cy))
        moribundo.needs.sed = 0.99
        moribundo._dias_sed_critica = 1
        agents.add_agent(moribundo)

        # Correr 2 días para que muera
        _run_ticks(world, agents, n_ticks=2 * 24)

        # Registrar muertes en BD
        buf.record_deaths(agents.death_log)

        deaths = db.get_deaths()
        assert any(d["agent_id"] == "doom" for d in deaths)
        db.close()

    def test_session_log_ciclo_completo(self, tmp_path):
        db  = DatabaseManager(db_path=str(tmp_path / "sim.db"))
        sl  = SessionLog(db)
        sid = sl.start(dia_inicio=0)

        for _ in range(10):
            sl.record_day()

        sl.record_death()
        sl.close(dia_actual=10, razon="normal")

        cur = db._conn.execute(
            "SELECT dias_procesados, muertes_sesion FROM session_log WHERE session_id=?",
            (sid,),
        )
        row = cur.fetchone()
        assert row["dias_procesados"] == 10
        assert row["muertes_sesion"] == 1
        db.close()
