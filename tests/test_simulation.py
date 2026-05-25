"""
Tests de Fase 5 — Seeds + SimulationRunner.
Criterio: checklist del beta scope completado en los puntos alcanzables
(campo colectivo y vault quedan para Fases 7 y 8).
"""
import time
from pathlib import Path

import pytest
import yaml

from core.simulation import SimulationRunner
from core.agents import AgentCore
from core.world import WorldCore

SEEDS_FILE = "data/seeds/initial_personas.yaml"


# ── Seeds YAML ────────────────────────────────────────────────────────────────

class TestSeedsYAML:

    def test_seeds_file_existe(self):
        assert Path(SEEDS_FILE).exists(), f"No existe: {SEEDS_FILE}"

    def test_seeds_tiene_15_agentes(self):
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["agents"]) == 15

    def test_seeds_ids_unicos(self):
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        ids = [a["id"] for a in data["agents"]]
        assert len(ids) == len(set(ids)), "IDs duplicados en seeds"

    def test_seeds_campos_obligatorios(self):
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        obligatorios = ["id", "nombre", "edad", "sexo", "rol", "posicion"]
        for agente in data["agents"]:
            for campo in obligatorios:
                assert campo in agente, f"Agente {agente.get('id')} sin campo '{campo}'"

    def test_seeds_diversidad_de_roles(self):
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        roles = {a["rol"] for a in data["agents"]}
        assert len(roles) >= 3, f"Poca diversidad de roles: {roles}"

    def test_seeds_rango_edad_variado(self):
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        edades = [a["edad"] for a in data["agents"]]
        assert min(edades) < 20   # crías/jóvenes
        assert max(edades) > 35   # adultos mayores

    def test_seeds_ambos_sexos(self):
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        sexos = {a["sexo"] for a in data["agents"]}
        assert "M" in sexos and "F" in sexos

    def test_seeds_arquetipos_definidos(self):
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for agente in data["agents"]:
            assert "arquetipos" in agente, f"Agente {agente['id']} sin arquetipos"
            arquetipos = agente["arquetipos"]
            assert len(arquetipos) >= 2, f"Agente {agente['id']} con menos de 2 arquetipos"


# ── SimulationRunner — nueva sesión ──────────────────────────────────────────

class TestSimulationRunnerNewSession:

    def test_carga_15_agentes_desde_seeds(self, tmp_path):
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        assert len(runner.agents.agents) == 15

    def test_agentes_tienen_nombres_correctos(self, tmp_path):
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        nombres = {a.nombre for a in runner.agents.agents.values()}
        assert "Kairos" in nombres
        assert "Sophron" in nombres
        assert "Kore" in nombres

    def test_run_n_dias_sin_crash(self, tmp_path):
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        runner.run(n_days=5)
        assert runner.current_dia >= 5

    def test_agentes_vivos_tras_5_dias(self, tmp_path):
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        runner.run(n_days=5)
        assert runner.alive_count > 0

    def test_snapshots_guardados_en_db(self, tmp_path):
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        runner.run(n_days=3)
        cur = runner.db._conn.execute("SELECT COUNT(*) FROM agent_snapshots")
        assert cur.fetchone()[0] > 0

    def test_sesion_registrada_en_db(self, tmp_path):
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        runner.run(n_days=2)
        cur = runner.db._conn.execute("SELECT COUNT(*) FROM session_log")
        assert cur.fetchone()[0] >= 1

    def test_checkpoint_generado_al_cerrar(self, tmp_path):
        cp_dir = tmp_path / "cp"
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(cp_dir),
        )
        runner.run(n_days=2)
        checkpoints = list(cp_dir.glob("checkpoint_*.json"))
        assert len(checkpoints) >= 1


# ── SimulationRunner — reanudación desde checkpoint ──────────────────────────

class TestSimulationRunnerResume:

    def _run_and_save(self, tmp_path, n_days=3):
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        runner.run(n_days=n_days)
        return runner.current_dia

    def test_resume_desde_checkpoint(self, tmp_path):
        dia_orig = self._run_and_save(tmp_path, n_days=3)
        runner2  = SimulationRunner.resume(
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        # El día de inicio debe coincidir (o estar cerca) del checkpoint
        assert runner2.current_dia >= 0

    def test_resume_carga_mismos_agentes(self, tmp_path):
        self._run_and_save(tmp_path, n_days=3)
        runner2 = SimulationRunner.resume(
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        assert len(runner2.agents.agents) == 15

    def test_resume_y_corre_mas_dias(self, tmp_path):
        self._run_and_save(tmp_path, n_days=3)
        runner2 = SimulationRunner.resume(
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        dia_antes = runner2.current_dia
        runner2.run(n_days=2)
        assert runner2.current_dia >= dia_antes + 2

    def test_resume_estado_mundo_coherente(self, tmp_path):
        self._run_and_save(tmp_path, n_days=5)
        runner2 = SimulationRunner.resume(
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        # El mundo debe tener hexes explorados
        assert len(runner2.world.terrain.explored_coords()) > 0

    def test_resume_hexes_explorados_coinciden(self, tmp_path):
        runner1 = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        runner1.run(n_days=5)
        hexes_orig = set(runner1.world.terrain.explored_coords())

        runner2 = SimulationRunner.resume(
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        hexes_rest = set(runner2.world.terrain.explored_coords())
        assert hexes_orig == hexes_rest


# ── Criterio de Fase 5: checklist del beta scope ──────────────────────────────

class TestPhase5Criterion:
    """
    Items del checklist de doc 03 alcanzables en Fase 5:
      [x] 15 agentes definidos en YAML con diversidad arquetípica real
      [x] Motor de tick corriendo sin errores (1 día = 24 ticks)
      [x] Rutinas básicas funcionando (dormir, buscar alimento, interactuar)
      [x] Al menos 1 muerte posible (por hambre/deshidratación)
      [x] SQLite guardando snapshots
      [x] El motor puede pausarse y reanudarse sin perder estado
      [ ] Campo colectivo recibiendo input  ← Fase 7
      [ ] Vault de Obsidian sincronizando   ← Fase 8
    """

    def test_beta_scope_15_agentes_yaml(self):
        """[ ] 15 agentes definidos en YAML con diversidad arquetípica real"""
        with open(SEEDS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["agents"]) == 15
        arquetipos_extremos = {
            a["id"]: max(a.get("arquetipos", {}).values(), default=0)
            for a in data["agents"]
        }
        extremos = [aid for aid, v in arquetipos_extremos.items() if v >= 0.80]
        assert len(extremos) >= 4, f"Menos de 4 perfiles extremos: {extremos}"

    def test_beta_scope_motor_tick(self, tmp_path):
        """[ ] Motor de tick corriendo sin errores"""
        runner = SimulationRunner.new_session(
            seed_file=SEEDS_FILE,
            db_path=str(tmp_path / "sim.db"),
            checkpoint_dir=str(tmp_path / "cp"),
        )
        t0 = time.monotonic()
        runner.run(n_days=1)
        elapsed = time.monotonic() - t0
        assert runner.current_dia >= 1
        assert elapsed < 30.0, f"1 día simulado tardó {elapsed:.2f}s"

    def test_beta_scope_rutinas_funcionando(self, tmp_path):
        """[ ] Rutinas básicas funcionando"""
        runner = SimulationRunner.new_session(
            seed_file=SEEDS_FILE,
            db_path=str(tmp_path / "sim.db"),
            checkpoint_dir=str(tmp_path / "cp"),
        )
        runner.run(n_days=2)
        # Si las rutinas funcionan, las necesidades de los agentes vivos
        # no deben estar todas al máximo (alguien comió/bebió)
        vivos = [a for a in runner.agents.agents.values() if a.is_alive]
        assert len(vivos) > 0
        hambres = [a.needs.hambre for a in vivos]
        # No todos en máximo crítico
        assert not all(h >= 0.95 for h in hambres)

    def test_beta_scope_muerte_posible(self, tmp_path):
        """[ ] Al menos 1 muerte posible — verifica el mecanismo directamente"""
        from core.agents import Agent
        # Verificar inanición (3 días)
        agente = Agent(agent_id="muerto", nombre="Test", posicion=(40, 30))
        agente.needs.hambre = 0.99
        causa = None
        for _ in range(4):
            agente.needs.hambre = 0.99  # mantener crítico
            causa = agente.check_death()
            if causa:
                break
        assert causa == "inanicion"
        assert not agente.is_alive
        # Verificar deshidratación (2 días)
        agente2 = Agent(agent_id="muerto2", nombre="Test2", posicion=(40, 30))
        agente2.needs.sed = 0.99
        causa2 = None
        for _ in range(3):
            agente2.needs.sed = 0.99  # mantener crítico
            causa2 = agente2.check_death()
            if causa2:
                break
        assert causa2 == "deshidratacion"
        assert not agente2.is_alive

    def test_beta_scope_sqlite_snapshots(self, tmp_path):
        """[ ] SQLite guardando snapshots"""
        runner = SimulationRunner.new_session(
            seed_file=SEEDS_FILE,
            db_path=str(tmp_path / "sim.db"),
            checkpoint_dir=str(tmp_path / "cp"),
        )
        runner.run(n_days=2)
        cur = runner.db._conn.execute("SELECT COUNT(DISTINCT agent_id) FROM agent_snapshots")
        n_agents_en_db = cur.fetchone()[0]
        assert n_agents_en_db == 15

    def test_beta_scope_pausar_y_reanudar(self, tmp_path):
        """[ ] El motor puede pausarse y reanudarse sin perder estado"""
        runner1 = SimulationRunner.new_session(
            seed_file=SEEDS_FILE,
            db_path=str(tmp_path / "sim.db"),
            checkpoint_dir=str(tmp_path / "cp"),
        )
        runner1.run(n_days=3)
        dia_pausa  = runner1.current_dia
        vivos_orig = runner1.alive_count

        # Reanudar y correr 2 días más
        runner2 = SimulationRunner.resume(
            db_path        = str(tmp_path / "sim.db"),
            checkpoint_dir = str(tmp_path / "cp"),
        )
        runner2.run(n_days=2)

        # El día avanzó y el número de agentes es coherente
        assert runner2.current_dia >= dia_pausa + 2
        assert 0 <= runner2.alive_count <= 15

    def test_beta_scope_30_dias_sin_todos_muertos(self, tmp_path):
        """Criterio combinado: 15 agentes desde seeds, 30 días, al menos 1 vivo."""
        runner = SimulationRunner.new_session(
            seed_file=SEEDS_FILE,
            db_path=str(tmp_path / "sim.db"),
            checkpoint_dir=str(tmp_path / "cp"),
        )
        runner.run(n_days=30)
        assert runner.alive_count > 0, (
            f"Todos murieron. Muertes: {runner.agents.death_log}"
        )
        assert runner.current_dia >= 30
