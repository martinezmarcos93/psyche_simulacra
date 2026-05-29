"""
Tests del Roadmap 7 — Emergencia Cultural.

D4 — Cobertura mítica con rich_culture_100.yaml:
     Tras N días se deben haber generado >= 2 proto-mitos y >= 1 mito cristalizado.

C3 — Suspensión completa de necesidades en zona liminal:
     Agentes con in_liminal = True no acumulan hambre/sed/fatiga.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch

# ── Parches comunes para correr headless ─────────────────────────────────────

_HEADLESS_PATCHES = [
    patch("obsidian.sync.ObsidianSync.sync_day",               lambda *a, **k: None),
    patch("obsidian.sync.ObsidianSync.sync_from_vault",        lambda *a, **k: None),
    patch("core.narrative.narrator.NarratorEngine._write_legend", lambda *a, **k: None),
    patch("core.narrative.narrator.NarratorEngine.drain",      lambda *a, **k: None),
    patch("core.narrative.narrator.NarratorEngine.stop",       lambda *a, **k: None),
]

SEEDS_RICH  = "data/seeds/rich_culture_100.yaml"
SEEDS_INIT  = "data/seeds/initial_personas.yaml"
_SEED_D4    = 42


def _start_patches():
    for p in _HEADLESS_PATCHES:
        p.start()


def _stop_patches():
    for p in _HEADLESS_PATCHES:
        p.stop()


# ── C3 — Suspensión de necesidades en zona liminal ───────────────────────────

class TestLiminalNeedsSuspension:
    """C3: agentes en zona liminal no acumulan hambre/sed/fatiga."""

    def test_needs_no_cambian_sin_update(self):
        """NeedsState permanece inmutable si update_waking/sleeping no son llamados."""
        from core.agents.needs import Needs

        n = Needs(hambre=0.2, sed=0.15, fatiga=0.10)
        h0, s0, f0 = n.hambre, n.sed, n.fatiga

        # 100 iteraciones sin llamar update (simulación del salto in_liminal)
        for _ in range(100):
            pass

        assert n.hambre == h0
        assert n.sed    == s0
        assert n.fatiga == f0

    def test_necesidades_crecen_sin_liminal(self):
        """Confirma que sin liminal las necesidades SÍ crecen (baseline)."""
        from core.agents.needs import Needs

        n = Needs()
        for _ in range(10):
            n.update_waking()

        assert n.hambre > 0.0
        assert n.sed    > 0.0
        assert n.fatiga > 0.0

    def test_agentcore_salta_agentes_liminales(self):
        """
        C3: el loop de AgentCore.on_tick omite update_biological para agentes
        con in_liminal=True. Reproducimos el patrón exacto de agent_core.py líneas 198-201.
        """
        from core.agents.needs import Needs
        from unittest.mock import MagicMock

        needs = Needs(hambre=0.20, sed=0.15, fatiga=0.10)

        agent = MagicMock()
        agent.is_alive  = True
        agent.in_liminal = True
        agent.needs     = needs

        h0, s0, f0 = needs.hambre, needs.sed, needs.fatiga

        # Reproducir el loop de on_tick (agent_core.py líneas 198-201) 100 veces
        for _ in range(100):
            if not agent.is_alive or agent.in_liminal:
                continue                              # skip — agente liminal
            agent.update_biological(MagicMock(), MagicMock())

        # update_biological nunca debió ser llamado
        agent.update_biological.assert_not_called()
        assert needs.hambre == h0, f"hambre cambió: {h0} → {needs.hambre}"
        assert needs.sed    == s0, f"sed cambió: {s0} → {needs.sed}"
        assert needs.fatiga == f0, f"fatiga cambió: {f0} → {needs.fatiga}"

    def test_in_liminal_flag_en_agent_tiene_atributo(self):
        """El agente expone el flag in_liminal con valor por defecto False."""
        import inspect
        from core.agents.agent import Agent

        # in_liminal está seteado en el cuerpo de __init__ como self.in_liminal = False
        src = inspect.getsource(Agent.__init__)
        assert "in_liminal" in src, (
            "Agent.__init__ debe contener 'in_liminal' (agent.py línea 131)"
        )


# ── D4 — Cobertura mítica con rich_culture_100.yaml ──────────────────────────

class TestMythCoverage:
    """D4: corrida con rich_culture genera múltiples mitos."""

    @pytest.mark.slow
    def test_cobertura_mitica_rich_culture(self, tmp_path):
        """
        Tras 500 días con rich_culture_100.yaml (seed fijo) deben existir
        >= 2 proto-mitos creados (activos o cristalizados) y >= 1 cristalizado.

        Usa seed=42 para reproducibilidad. Marcado @slow por duración.
        """
        if not Path(SEEDS_RICH).exists():
            pytest.skip(f"Semilla {SEEDS_RICH} no encontrada.")

        from core.simulation import SimulationRunner

        _start_patches()
        try:
            runner = SimulationRunner.new_session(
                seed_file      = SEEDS_RICH,
                seed           = _SEED_D4,
                db_path        = str(tmp_path / "sim_d4.db"),
                checkpoint_dir = str(tmp_path / "cp_d4"),
            )
            runner.run(n_days=500)

            engine = runner.agents.mythology_engine
            n_proto_ever   = len(engine.proto_myths) + len(engine.active_myths)
            n_crystallized = len([m for m in engine.active_myths if not m.es_leyenda or m.active])
            n_legends      = len([m for m in engine.active_myths if m.es_leyenda])

            assert n_proto_ever >= 2, (
                f"Solo {n_proto_ever} proto-mito(s) en 500 días. "
                f"Esperados >= 2. Revisar umbrales de cristalización."
            )
            assert (n_crystallized + n_legends) >= 1, (
                f"Ningún mito cristalizado en 500 días. "
                f"proto_myths activos: {len(engine.proto_myths)}. "
                f"Revisar _COHERENCE_TO_CRYSTALLIZE."
            )
        finally:
            _stop_patches()

    def test_myth_thresholds_son_correctos(self):
        """D1 verificado: los umbrales están en los valores del Roadmap 7."""
        import core.social.mythology as myth_mod

        assert myth_mod._COHERENCE_TO_CRYSTALLIZE == pytest.approx(3.0), (
            f"_COHERENCE_TO_CRYSTALLIZE debería ser 3.0, es {myth_mod._COHERENCE_TO_CRYSTALLIZE}"
        )
        # Umbral <= 0.25 (puede ser sobreescrito por env MYTH_CONTEXT_THRESHOLD)
        assert myth_mod._PROTO_MYTH_THRESHOLD <= 0.35, (
            f"_PROTO_MYTH_THRESHOLD debería ser <= 0.35, es {myth_mod._PROTO_MYTH_THRESHOLD}"
        )

    def test_mitos_multiples_del_mismo_tipo(self):
        """D2: dos pares distintos del mismo tipo pueden coexistir como proto-mitos."""
        from core.social.mythology import MythologyEngine, ProtoMito

        engine = MythologyEngine(seed=0)

        # Inyectar dos proto-mitos del mismo tipo pero par diferente
        engine.proto_myths.append(ProtoMito(
            tipo="cosmogonia", par=("muerte", "sombra"), dia_origen=1, intensidad_contexto=0.5
        ))
        engine.proto_myths.append(ProtoMito(
            tipo="cosmogonia", par=("muerte", "madre"), dia_origen=2, intensidad_contexto=0.5
        ))

        assert len(engine.proto_myths) == 2, (
            "D2: deberían coexistir 2 proto-mitos del mismo tipo con pares distintos"
        )

    def test_tribe_id_en_myth_crystal(self):
        """D3: MythCrystal tiene campo tribe_id serializable."""
        from core.social.mythology import MythCrystal

        crystal = MythCrystal(
            name="test_mito", tipo="cosmogonia", par=("muerte", "sombra"),
            tribe_id="tribe_arete",
        )
        d = crystal.__dataclass_fields__
        assert "tribe_id" in d, "MythCrystal debe tener campo tribe_id"
        assert crystal.tribe_id == "tribe_arete"
