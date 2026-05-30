"""
Tests A3 — Reproducibilidad de corrida corta.
Dos ejecuciones con el mismo seed deben producir resultados idénticos:
primer nacimiento, primer proto-mito y primera estructura construida.
"""
import pytest
from pathlib import Path
from unittest.mock import patch
from core.simulation import SimulationRunner

SEEDS_FILE = "data/seeds/initial_personas.yaml"
_DAYS      = 200
_SEED      = 42

# Parchear ObsidianSync y NarratorEngine para no escribir en disco durante tests
_NOOP_PATCHES = [
    patch("obsidian.sync.ObsidianSync.sync_all",           lambda *a, **k: None),
    patch("obsidian.sync.ObsidianSync.sync_from_vault",    lambda *a, **k: None),
    patch("core.narrative.narrator.NarratorEngine.drain",  lambda *a, **k: None),
    patch("core.narrative.narrator.NarratorEngine.stop",   lambda *a, **k: None),
]


_run_counter = 0

def _run_and_collect(seed: int, days: int, tmp_path: Path) -> dict:
    """Corre la sim `days` días y devuelve hitos culturales."""
    global _run_counter
    _run_counter += 1
    run_id = _run_counter

    patches = [
        patch("obsidian.sync.ObsidianSync.sync_day",              lambda *a, **k: None),
        patch("obsidian.sync.ObsidianSync.sync_from_vault",       lambda *a, **k: None),
        patch("core.narrative.narrator.NarratorEngine._write_legend", lambda *a, **k: None),
        patch("core.narrative.narrator.NarratorEngine.drain",     lambda *a, **k: None),
        patch("core.narrative.narrator.NarratorEngine.stop",      lambda *a, **k: None),
    ]
    for p in patches:
        p.start()
    try:
        runner = SimulationRunner.new_session(
            seed_file      = SEEDS_FILE,
            seed           = seed,
            db_path        = str(tmp_path / f"sim_{seed}_{run_id}.db"),
            checkpoint_dir = str(tmp_path / f"cp_{run_id}"),
        )
        runner.run(n_days=days)

        births  = runner.agents._birth_log
        protos  = runner.agents.mythology_engine.proto_myths
        structs = runner.agents.culture_engine.structures

        return {
            "first_birth":     births[0]["dia"]                           if births  else None,
            "first_protomyth": getattr(protos[0], "dia_origen", None)  if protos  else None,
            "first_structure": getattr(structs[0], "day_built",   None) if structs else None,
            "agents_alive":    sum(1 for a in runner.agents.agents.values() if a.is_alive),
            "n_agents":        len(runner.agents.agents),
        }
    finally:
        for p in patches:
            p.stop()


class TestReproducibility:

    def test_dos_corridas_mismo_seed_son_identicas(self, tmp_path):
        """El resultado de dos corridas con el mismo seed debe ser igual."""
        run_a = _run_and_collect(_SEED, _DAYS, tmp_path)
        run_b = _run_and_collect(_SEED, _DAYS, tmp_path)
        assert run_a == run_b, (
            f"Las corridas difieren con seed={_SEED}:\n  A={run_a}\n  B={run_b}"
        )

    def test_seeds_distintos_producen_resultados_distintos(self, tmp_path):
        """Seeds diferentes deben divergir en al menos una métrica."""
        run_42 = _run_and_collect(42, _DAYS, tmp_path)
        run_99 = _run_and_collect(99, _DAYS, tmp_path)
        assert run_42 != run_99, (
            "Seeds distintos (42 vs 99) produjeron resultados idénticos — "
            "el azar puede no estar siendo sembrado correctamente."
        )
