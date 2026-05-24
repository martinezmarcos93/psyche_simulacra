"""
Tests de Fase 5 — Validación Científica de la Emergencia.
Cubre: KL divergencia, VFE proxy (entropía), IMI, exportador CSV/JSON.
"""
import csv
import json
import math
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.metrics.emergence import EmergenceMetrics, DayMetrics, _EPSILON
from core.metrics.exporter import MetricsExporter


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_field(symbols: dict[str, float], pressure: float = 0.0):
    """Crea un CollectiveField mock con símbolos dados."""
    f = MagicMock()
    f.symbols = symbols
    f.emotional_pressure = pressure
    return f


def _make_archetype(values: dict[str, float]):
    """Crea un ArchetypeVector mock con los atributos dados."""
    arch = MagicMock()
    for k, v in values.items():
        setattr(arch, k, v)
    return arch


def _make_agent(agent_id: str, arch_values: dict[str, float], alive: bool = True):
    """Crea un Agent mock con id, is_alive y archetypes."""
    a = MagicMock()
    a.id       = agent_id
    a.is_alive = alive
    a.archetypes = _make_archetype(arch_values)
    return a


_UNIFORM_ARCH = {
    "self_": 0.5, "persona": 0.5, "sombra": 0.5, "anima_animus": 0.5,
    "heroe": 0.5, "sabio": 0.5, "trickster": 0.5, "madre": 0.5,
    "padre": 0.5, "nino_divino": 0.5, "gobernante": 0.5, "rebelde": 0.5,
}


# ── Tests de KL Divergencia ───────────────────────────────────────────────────

class TestKLDivergence:

    def test_distribucion_identica_da_cero(self):
        em  = EmergenceMetrics()
        p   = [1/12] * 12
        kl  = em._kl_divergence(p, p)
        assert kl == pytest.approx(0.0, abs=1e-6)

    def test_distribucion_opuesta_da_valor_alto(self):
        em = EmergenceMetrics()
        p  = [0.9 if i == 0 else 0.1 / 11 for i in range(12)]
        q  = [0.9 if i == 11 else 0.1 / 11 for i in range(12)]
        total = sum(p)
        p = [v / total for v in p]
        total = sum(q)
        q = [v / total for v in q]
        kl = em._kl_divergence(p, q)
        assert kl > 1.0

    def test_simetria(self):
        em = EmergenceMetrics()
        p  = [0.5, 0.3, 0.2] + [0.0] * 9
        q  = [0.2, 0.5, 0.3] + [0.0] * 9
        t  = sum(p) + _EPSILON
        p  = [v / t for v in p]
        t  = sum(q) + _EPSILON
        q  = [v / t for v in q]
        assert em._kl_divergence(p, q) == pytest.approx(em._kl_divergence(q, p), rel=1e-6)

    def test_pairwise_una_tribu_da_cero(self):
        em   = EmergenceMetrics()
        dist = {"t1": [1/12] * 12}
        kl_m, kl_x = em._pairwise_kl(dist)
        assert kl_m == 0.0
        assert kl_x == 0.0

    def test_pairwise_dos_tribus_distintas(self):
        em = EmergenceMetrics()
        p  = [0.9 if i == 0 else 0.1 / 11 for i in range(12)]
        q  = [0.9 if i == 11 else 0.1 / 11 for i in range(12)]
        tp = sum(p); tq = sum(q)
        dists = {"t1": [v / tp for v in p], "t2": [v / tq for v in q]}
        kl_m, kl_x = em._pairwise_kl(dists)
        assert kl_m > 0.0
        assert kl_x >= kl_m


# ── Tests de VFE (entropía de campo) ─────────────────────────────────────────

class TestVFEEntropy:

    def test_campo_uniforme_tiene_maxima_entropia(self):
        em  = EmergenceMetrics()
        symbols = {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0}
        field   = _make_field(symbols)
        h       = em._field_entropy(field)
        # Entropía máxima para 4 símbolos equiprobables = log(4) ≈ 1.386
        assert h == pytest.approx(math.log(4), rel=0.01)

    def test_campo_un_simbolo_dominante_tiene_baja_entropia(self):
        em = EmergenceMetrics()
        symbols = {"sombra": 10.0, "heroe": 0.001, "muerte": 0.001}
        field   = _make_field(symbols)
        h       = em._field_entropy(field)
        assert h < math.log(3) * 0.5

    def test_campo_vacio_retorna_cero(self):
        em    = EmergenceMetrics()
        field = _make_field({})
        assert em._field_entropy(field) == 0.0

    def test_entropia_siempre_no_negativa(self):
        em = EmergenceMetrics()
        for vals in [
            {"x": 0.0, "y": 0.0},
            {"x": 1.0},
            {"x": 0.3, "y": 0.7},
        ]:
            assert em._field_entropy(_make_field(vals)) >= 0.0


# ── Tests de IMI ──────────────────────────────────────────────────────────────

class TestIMI:

    def test_sin_tribus_da_cero(self):
        em    = EmergenceMetrics()
        agent = _make_agent("a1", _UNIFORM_ARCH)
        assert em._imi({"a1": agent}, {}) == 0.0

    def test_una_tribu_da_cero(self):
        em     = EmergenceMetrics()
        agents = {f"a{i}": _make_agent(f"a{i}", _UNIFORM_ARCH) for i in range(5)}
        tribes = {"t1": list(agents.keys())}
        assert em._imi(agents, tribes) == 0.0

    def test_tribus_identicas_da_imi_bajo(self):
        """Dos tribus con misma distribución arquetípica → IMI ≈ 0."""
        em = EmergenceMetrics()
        arch = dict(_UNIFORM_ARCH)
        agents = {f"a{i}": _make_agent(f"a{i}", arch) for i in range(6)}
        tribes = {
            "t1": ["a0", "a1", "a2"],
            "t2": ["a3", "a4", "a5"],
        }
        imi = em._imi(agents, tribes)
        assert imi < 0.05

    def test_tribus_muy_distintas_da_imi_alto(self):
        """Dos tribus con arquetipos opuestos → IMI alto."""
        em = EmergenceMetrics()
        arch_a = {**_UNIFORM_ARCH, "heroe": 0.95, "sombra": 0.05}
        arch_b = {**_UNIFORM_ARCH, "heroe": 0.05, "sombra": 0.95}
        agents = {
            **{f"a{i}": _make_agent(f"a{i}", arch_a) for i in range(3)},
            **{f"b{i}": _make_agent(f"b{i}", arch_b) for i in range(3)},
        }
        tribes = {
            "t1": ["a0", "a1", "a2"],
            "t2": ["b0", "b1", "b2"],
        }
        imi = em._imi(agents, tribes)
        assert imi > 0.30

    def test_imi_rango_valido(self):
        """IMI siempre en [0, 1]."""
        em = EmergenceMetrics()
        import random
        rng = random.Random(777)
        for _ in range(20):
            archs = [
                {attr: rng.random() for attr in _UNIFORM_ARCH}
                for _ in range(8)
            ]
            agents = {f"a{i}": _make_agent(f"a{i}", archs[i]) for i in range(8)}
            tribes = {
                "t1": ["a0", "a1", "a2", "a3"],
                "t2": ["a4", "a5", "a6", "a7"],
            }
            imi = em._imi(agents, tribes)
            assert 0.0 <= imi <= 1.0 + 1e-6


# ── Tests de compute_day ──────────────────────────────────────────────────────

class TestComputeDay:

    def _make_tribe_manager(self, tribes, local_fields=None):
        tm = MagicMock()
        tm.tribes = tribes
        tm.local_fields = local_fields or {}
        return tm

    def test_retorna_daymetrics(self):
        em     = EmergenceMetrics()
        agents = {"a1": _make_agent("a1", _UNIFORM_ARCH)}
        tm     = self._make_tribe_manager({"t1": ["a1"]})
        cf     = _make_field({"heroe": 0.5, "sombra": 0.3})
        result = em.compute_day(0, agents, tm, cf)
        assert isinstance(result, DayMetrics)
        assert result.dia == 0

    def test_n_alive_correcto(self):
        em = EmergenceMetrics()
        agents = {
            "a1": _make_agent("a1", _UNIFORM_ARCH, alive=True),
            "a2": _make_agent("a2", _UNIFORM_ARCH, alive=False),
        }
        tm = self._make_tribe_manager({})
        cf = _make_field({"heroe": 1.0})
        m  = em.compute_day(5, agents, tm, cf)
        assert m.n_alive == 1

    def test_n_structures_con_culture_engine(self):
        em  = EmergenceMetrics()
        agents = {"a1": _make_agent("a1", _UNIFORM_ARCH)}
        tm  = self._make_tribe_manager({})
        cf  = _make_field({"heroe": 0.5})
        ce  = MagicMock()
        ce.structures = [MagicMock(), MagicMock()]
        m   = em.compute_day(10, agents, tm, cf, culture_engine=ce)
        assert m.n_structures == 2

    def test_sin_culture_engine_n_structures_cero(self):
        em = EmergenceMetrics()
        agents = {}
        tm = self._make_tribe_manager({})
        cf = _make_field({"heroe": 0.5})
        m  = em.compute_day(1, agents, tm, cf)
        assert m.n_structures == 0

    def test_metricas_numericamente_validas(self):
        em = EmergenceMetrics()
        arch_a = {**_UNIFORM_ARCH, "heroe": 0.9, "sombra": 0.1}
        arch_b = {**_UNIFORM_ARCH, "heroe": 0.1, "sombra": 0.9}
        agents = {
            **{f"a{i}": _make_agent(f"a{i}", arch_a) for i in range(3)},
            **{f"b{i}": _make_agent(f"b{i}", arch_b) for i in range(3)},
        }
        cf1 = _make_field({"heroe": 0.8, "sombra": 0.1, "muerte": 0.1})
        cf2 = _make_field({"heroe": 0.1, "sombra": 0.8, "muerte": 0.1})
        tm  = self._make_tribe_manager(
            tribes={"t1": ["a0", "a1", "a2"], "t2": ["b0", "b1", "b2"]},
            local_fields={"t1": cf1, "t2": cf2},
        )
        cf_global = _make_field({"heroe": 0.5, "sombra": 0.5})
        m = em.compute_day(50, agents, tm, cf_global)
        assert m.kl_mean >= 0.0
        assert m.kl_max  >= m.kl_mean
        assert m.vfe_global >= 0.0
        assert m.vfe_tribe_mean >= 0.0
        assert 0.0 <= m.imi <= 1.0 + 1e-6


# ── Tests del exportador ──────────────────────────────────────────────────────

class TestMetricsExporter:

    def _make_metric(self, dia: int) -> DayMetrics:
        return DayMetrics(
            dia=dia, kl_mean=0.1, kl_max=0.2,
            vfe_global=1.3, vfe_tribe_mean=1.1,
            imi=0.4, n_alive=10, n_tribes=2, n_structures=3,
            mig=0.5,
        )

    def test_flush_crea_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = MetricsExporter(output_dir=tmpdir)
            exp.record(self._make_metric(1))
            exp.record(self._make_metric(2))
            exp.flush()
            csv_path = Path(tmpdir) / "emergence_series.csv"
            assert csv_path.exists()
            with open(csv_path, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 2
            assert rows[0]["dia"] == "1"
            assert rows[1]["dia"] == "2"

    def test_flush_vacio_no_crea_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = MetricsExporter(output_dir=tmpdir)
            exp.flush()
            assert not (Path(tmpdir) / "emergence_series.csv").exists()

    def test_export_summary_crea_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = MetricsExporter(output_dir=tmpdir)
            for d in range(5):
                exp.record(self._make_metric(d))
            exp.export_summary()
            json_path = Path(tmpdir) / "emergence_summary.json"
            assert json_path.exists()
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["n_days"] == 5
            assert "kl_mean" in data
            assert "imi" in data

    def test_multiples_flushes_acumulan_filas(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = MetricsExporter(output_dir=tmpdir)
            exp.record(self._make_metric(1))
            exp.flush()
            exp.record(self._make_metric(2))
            exp.flush()
            with open(Path(tmpdir) / "emergence_series.csv", "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 2

    def test_summary_calcula_estadisticas_correctas(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = MetricsExporter(output_dir=tmpdir)
            # IMI: 0.0 y 1.0 → media=0.5
            m1 = DayMetrics(dia=1, kl_mean=0.0, kl_max=0.0, vfe_global=0.0,
                            vfe_tribe_mean=0.0, imi=0.0, n_alive=5, n_tribes=1, n_structures=0, mig=0.0)
            m2 = DayMetrics(dia=2, kl_mean=0.0, kl_max=0.0, vfe_global=0.0,
                            vfe_tribe_mean=0.0, imi=1.0, n_alive=5, n_tribes=2, n_structures=0, mig=0.0)
            exp.record(m1)
            exp.record(m2)
            exp.export_summary()
            with open(Path(tmpdir) / "emergence_summary.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["imi"]["mean"] == pytest.approx(0.5)
            assert data["imi"]["min"]  == pytest.approx(0.0)
            assert data["imi"]["max"]  == pytest.approx(1.0)
