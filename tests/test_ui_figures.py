"""
E1 — Smoke tests para funciones de construcción de figuras Plotly en la UI.

No requieren NiceGUI corriendo. Verifican que cada función devuelve un objeto
no-None ante inputs válidos y no lanza excepciones ante inputs vacíos/inválidos.
"""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── Importar funciones directamente desde el módulo UI ───────────────────────
# Agregamos el directorio raíz al path para que los imports del módulo UI funcionen
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from ui.psyche_ui import (
    _build_hex_map,
    _build_social_graph,
    _build_trend_panel,
    _build_icl_sparkline,
    _build_liminal_map,
    _build_emergence_figure,
    _build_icl_gauges,
    _build_agent_radar,
    _build_trend_figure,
)
from ui.db_reader import load_checkpoint


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def checkpoint():
    """Carga el checkpoint más reciente si existe, o devuelve None."""
    return load_checkpoint()


@pytest.fixture
def minimal_snap():
    """WorldSnapshot mínimo para pruebas del mapa."""
    snap = MagicMock()
    snap.liminal_hexes  = []
    snap.graves_activos = []
    snap.fauna_simbolica = []
    snap.fuego_activo   = False
    snap.fuego_coord    = None
    snap.recursos_por_hex = {}
    return snap


@pytest.fixture
def minimal_terrain():
    """Biomas mínimos para el mapa hex."""
    return {(0, 0): "bosque_templado", (1, 0): "pradera_humeda", (0, 1): "rio_lago"}


# ── _build_hex_map ────────────────────────────────────────────────────────────

class TestBuildHexMap:
    def test_retorna_figura_con_datos_minimos(self, minimal_snap, minimal_terrain):
        fig = _build_hex_map(minimal_snap, minimal_terrain)
        assert fig is not None

    def test_retorna_none_sin_snap(self, minimal_terrain):
        assert _build_hex_map(None, minimal_terrain) is None

    def test_retorna_none_sin_terreno(self, minimal_snap):
        assert _build_hex_map(minimal_snap, {}) is None

    def test_con_agentes_vivos(self, minimal_snap, minimal_terrain):
        agents = [
            {"id": "a1", "nombre": "Test", "pos": (0, 0), "alive": True,
             "humor": 0.7, "edad": 10, "arquetipo": "heroe",
             "estado": "cooperacion", "tribu": "t1"},
        ]
        fig = _build_hex_map(minimal_snap, minimal_terrain, agents_data=agents)
        assert fig is not None

    def test_con_agentes_muertos(self, minimal_snap, minimal_terrain):
        agents = [
            {"id": "a2", "nombre": "Muerto", "pos": (1, 0), "alive": False,
             "humor": 0.0, "edad": 30, "arquetipo": "sombra",
             "estado": "aislamiento", "tribu": "t1"},
        ]
        layer_flags = {"muertos": True, "agentes": True}
        fig = _build_hex_map(minimal_snap, minimal_terrain, agents_data=agents,
                             layer_flags=layer_flags)
        assert fig is not None

    def test_con_estructuras(self, minimal_snap, minimal_terrain):
        structures = [
            {"tipo": "altar",   "coord": (0, 0), "tribu": "t1", "estado": "activo"},
            {"tipo": "muralla", "coord": (1, 0), "tribu": "t1", "estado": "abandonado"},
            {"tipo": "totem",   "coord": (0, 1), "tribu": "t2", "estado": "activo"},
            {"tipo": "hoguera", "coord": (0, 0), "tribu": "t1", "estado": "activo"},
        ]
        layer_flags = {"estructuras": True}
        fig = _build_hex_map(minimal_snap, minimal_terrain, structures_data=structures,
                             layer_flags=layer_flags)
        assert fig is not None

    def test_con_hexes_liminales_y_portal(self, minimal_terrain):
        snap = MagicMock()
        snap.liminal_hexes = [
            {"coord": [0, 0], "misterio": 0.8, "symbol_pool": ["heroe", "sombra"], "es_portal": True},
            {"coord": [1, 0], "misterio": 0.5, "symbol_pool": ["sabio"],            "es_portal": False},
        ]
        snap.graves_activos  = []
        snap.fauna_simbolica = []
        snap.fuego_activo    = False
        snap.fuego_coord     = None
        snap.recursos_por_hex = {}
        fig = _build_hex_map(snap, minimal_terrain, layer_flags={"liminales": True})
        assert fig is not None

    def test_con_checkpoint_real(self, checkpoint, minimal_snap, minimal_terrain):
        """Smoke con checkpoint real si existe."""
        if checkpoint is None:
            pytest.skip("Sin checkpoint disponible")
        fig = _build_hex_map(minimal_snap, minimal_terrain)
        assert fig is not None


# ── _build_social_graph ───────────────────────────────────────────────────────

class TestBuildSocialGraph:
    def test_retorna_none_con_cp_vacio(self):
        assert _build_social_graph({}) is None

    def test_retorna_none_sin_agentes(self):
        cp = {"agentes": {"agents": [], "tribe_manager": {}}}
        assert _build_social_graph(cp) is None

    def test_con_checkpoint_real(self, checkpoint):
        if checkpoint is None:
            pytest.skip("Sin checkpoint disponible")
        fig = _build_social_graph(checkpoint)
        # Puede ser None si hay <2 agentes con lazos, pero no debe lanzar excepción
        assert fig is None or hasattr(fig, "data")


# ── _build_trend_panel ────────────────────────────────────────────────────────

class TestBuildTrendPanel:
    def test_retorna_none_con_todo_vacio(self):
        assert _build_trend_panel([], [], []) is None

    def test_retorna_figura_con_agent_metrics(self):
        rows = [
            {"dia": 1, "humor": 0.6, "energia": 0.5, "ansiedad": 0.3, "vivos": 10},
            {"dia": 2, "humor": 0.7, "energia": 0.6, "ansiedad": 0.2, "vivos": 9},
        ]
        fig = _build_trend_panel(rows, [], [])
        assert fig is not None

    def test_retorna_figura_completa(self):
        agent_rows   = [{"dia": i, "humor": 0.5, "energia": 0.5, "ansiedad": 0.3, "vivos": 10 - i}
                        for i in range(1, 6)]
        climate_rows = [{"dia": i, "temperatura": 20.0 + i, "riesgo": 0.1 * i} for i in range(1, 6)]
        scen_rows    = [{"dia": i, "resource_pressure": 0.3, "carrying_capacity": 50} for i in range(1, 6)]
        events       = [{"dia": 3, "evento": "tormenta"}]
        fig = _build_trend_panel(agent_rows, climate_rows, scen_rows, events)
        assert fig is not None
        assert len(fig.data) >= 4

    def test_con_un_solo_dia(self):
        rows = [{"dia": 1, "humor": 0.5, "energia": 0.5, "ansiedad": 0.3, "vivos": 10}]
        fig = _build_trend_panel(rows, [], [])
        assert fig is not None


# ── _build_icl_sparkline ──────────────────────────────────────────────────────

class TestBuildIclSparkline:
    def test_retorna_none_con_menos_de_2_muestras(self):
        h = deque([{"dia": 1, "emotional_pressure": 0.5, "myth_pressure": 0.3, "confusion": 0.1}])
        assert _build_icl_sparkline(h) is None

    def test_retorna_figura_con_muestras_suficientes(self):
        h = deque([
            {"dia": i, "emotional_pressure": 0.3 + i * 0.01,
             "myth_pressure": 0.2, "confusion": 0.1}
            for i in range(5)
        ])
        fig = _build_icl_sparkline(h)
        assert fig is not None
        assert len(fig.data) == 3  # tres trazas: emocional, mítica, confusión

    def test_deque_maxlen_no_explota(self):
        h = deque(maxlen=120)
        for i in range(150):
            h.append({"dia": i, "emotional_pressure": 0.5, "myth_pressure": 0.3, "confusion": 0.1})
        fig = _build_icl_sparkline(h)
        assert fig is not None


# ── _build_liminal_map ────────────────────────────────────────────────────────

class TestBuildLiminalMap:
    def test_retorna_none_sin_hexes(self):
        assert _build_liminal_map({}) is None
        assert _build_liminal_map({"hexes": []}) is None

    def test_retorna_figura_con_hexes(self):
        state = {
            "tick": 10,
            "n_sims": 0,
            "n_agents": 0,
            "hexes": [
                {"q": 0, "r": 0, "sub_biome": "vacio"},
                {"q": 1, "r": 0, "sub_biome": "nebulosa"},
                {"q": 0, "r": 1, "sub_biome": "aurora"},
            ],
            "agents": [],
            "sims": [],
        }
        fig = _build_liminal_map(state)
        assert fig is not None

    def test_retorna_figura_con_agentes_multisim(self):
        state = {
            "tick": 5,
            "n_sims": 2, "n_agents": 2,
            "hexes": [{"q": q, "r": 0, "sub_biome": "cristalino"} for q in range(5)],
            "agents": [
                {"agent_id": "a1", "nombre": "Erra",  "from_sim": "SIM_A",
                 "pos": [0, 0], "arquetipo": "heroe"},
                {"agent_id": "a2", "nombre": "Kael",  "from_sim": "SIM_B",
                 "pos": [2, 0], "arquetipo": "sombra"},
            ],
            "sims": [
                {"sim_id": "SIM_A", "n_agents": 1},
                {"sim_id": "SIM_B", "n_agents": 1},
            ],
        }
        fig = _build_liminal_map(state)
        assert fig is not None
        # 1 traza de terreno + 2 trazas de agentes (una por sim)
        assert len(fig.data) == 3


# ── _build_icl_gauges ─────────────────────────────────────────────────────────

class TestBuildIclGauges:
    @pytest.mark.parametrize("ep,mp,conf", [
        (0.0, 0.0, 0.0),
        (0.5, 0.3, 0.7),
        (1.0, 1.0, 1.0),
    ])
    def test_retorna_figura(self, ep, mp, conf):
        fig = _build_icl_gauges(ep, mp, conf)
        assert fig is not None
        assert len(fig.data) == 3


# ── _build_agent_radar ────────────────────────────────────────────────────────

class TestBuildAgentRadar:
    def test_retorna_none_sin_datos(self):
        assert _build_agent_radar({}) is None
        assert _build_agent_radar({"nombre": "X", "archetypes": {}}) is None

    def test_retorna_figura_con_arquetipos(self):
        ad = {
            "nombre": "Erra",
            "archetypes": {
                "self_": 0.8, "persona": 0.4, "sombra": 0.6,
                "anima_animus": 0.3, "heroe": 0.9, "sabio": 0.2,
                "trickster": 0.5, "madre": 0.1, "padre": 0.3,
                "nino_divino": 0.4, "gobernante": 0.2, "rebelde": 0.7,
            },
        }
        fig = _build_agent_radar(ad)
        assert fig is not None


# ── _build_emergence_figure ───────────────────────────────────────────────────

class TestBuildEmergenceFigure:
    def test_retorna_none_sin_datos(self):
        assert _build_emergence_figure([]) is None

    def test_retorna_figura_con_datos(self):
        rows = [
            {"dia": i, "kl_mean": 0.1 * i, "kl_max": 0.2 * i,
             "vfe_global": 0.3, "vfe_tribe_mean": 0.25, "imi": 0.05 * i}
            for i in range(1, 6)
        ]
        fig = _build_emergence_figure(rows)
        assert fig is not None


# ── _build_trend_figure (legacy, aún usada para compatibilidad) ───────────────

class TestBuildTrendFigure:
    def test_retorna_none_sin_rows(self):
        assert _build_trend_figure([], ["humor"], "Test") is None

    def test_retorna_figura_con_datos(self):
        rows = [{"dia": i, "humor": 0.5 + i * 0.01} for i in range(5)]
        fig = _build_trend_figure(rows, ["humor"], "Humor test")
        assert fig is not None
