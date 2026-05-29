"""
Lecturas no bloqueantes de la DB SQLite y del checkpoint JSON.
Espejo de lo que hace el Streamlit dashboard, adaptado para NiceGUI.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

_ROOT    = Path(__file__).parent.parent
_DB_PATH = _ROOT / "data" / "db" / "simulation.db"
_CP_DIR  = _ROOT / "data" / "checkpoints"


# ── Checkpoint JSON ───────────────────────────────────────────────────────────

def load_checkpoint() -> dict | None:
    candidates = sorted(_CP_DIR.glob("checkpoint_*.json"), reverse=True)
    for path in candidates[:2]:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[db_reader] load_checkpoint {path.name}: {e}", file=sys.stderr)
    return None


def checkpoint_summary(cp: dict | None) -> dict:
    """Métricas básicas del checkpoint para la página de inicio."""
    if cp is None:
        return {"dia": 0, "vivos": 0, "total": 0, "timestamp": ""}
    agents = cp.get("agentes", {}).get("agents", [])
    total  = len(agents)
    vivos  = sum(1 for a in agents if a.get("is_alive", False))
    return {
        "dia":       cp.get("dia_simulado", 0),
        "vivos":     vivos,
        "total":     total,
        "timestamp": cp.get("timestamp_real", "")[:19].replace("T", " "),
    }


# ── DB SQLite ─────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection | None:
    if not _DB_PATH.exists():
        return None
    try:
        c = sqlite3.connect(f"file:{_DB_PATH}?mode=ro", uri=True)
        c.row_factory = sqlite3.Row
        return c
    except Exception as e:
        print(f"[db_reader] _conn: {e}", file=sys.stderr)
        return None


def load_agent_metrics() -> list[dict]:
    """humor, energía, ansiedad promedio por día."""
    conn = _conn()
    if conn is None:
        return []
    try:
        rows = conn.execute("""
            SELECT dia,
                   AVG(humor)    as humor,
                   AVG(energia)  as energia,
                   AVG(ansiedad) as ansiedad,
                   SUM(is_alive) as vivos
            FROM agent_snapshots
            GROUP BY dia ORDER BY dia
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[db_reader] load_agent_metrics: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


def load_climate_metrics() -> list[dict]:
    """temperatura, riesgo, precipitación por día."""
    conn = _conn()
    if conn is None:
        return []
    try:
        rows = conn.execute("""
            SELECT dia,
                   AVG(temperatura)   as temperatura,
                   AVG(survival_risk) as riesgo,
                   AVG(precipitacion) as precipitacion
            FROM climate_log
            GROUP BY dia ORDER BY dia
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[db_reader] load_climate_metrics: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


def load_scenario_metrics() -> list[dict]:
    """resource_pressure, carrying_capacity, hexes explorados por día."""
    conn = _conn()
    if conn is None:
        return []
    try:
        rows = conn.execute("""
            SELECT dia,
                   AVG(resource_pressure)    as resource_pressure,
                   AVG(carrying_capacity)    as carrying_capacity,
                   MAX(n_hexes_explorados)   as hexes_explorados
            FROM scenario_state_log
            GROUP BY dia ORDER BY dia
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[db_reader] load_scenario_metrics: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


def load_climate_events() -> list[dict]:
    """Días con evento climático extremo (evento != NULL) para superposición en gráficos."""
    conn = _conn()
    if conn is None:
        return []
    try:
        rows = conn.execute("""
            SELECT dia, evento
            FROM climate_log
            WHERE evento IS NOT NULL AND evento != ''
            GROUP BY dia, evento
            ORDER BY dia
        """).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[db_reader] load_climate_events: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


_EMERGENCE_CSV = _ROOT / "data" / "metrics" / "emergence_series.csv"


def load_emergence_metrics(last_n_days: int = 300) -> list[dict]:
    """
    Lee emergence_series.csv y devuelve un punto por día (media de las métricas).
    Limitado a los últimos last_n_days días para rendimiento.
    """
    if not _EMERGENCE_CSV.exists():
        return []
    try:
        # Leer y agrupar por día
        sums: dict[int, dict] = {}
        counts: dict[int, int] = {}
        _COLS = ("kl_mean", "kl_max", "vfe_global", "vfe_tribe_mean", "imi")

        with open(_EMERGENCE_CSV, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    dia = int(row["dia"])
                except (KeyError, ValueError):
                    continue
                if dia not in sums:
                    sums[dia]   = {c: 0.0 for c in _COLS}
                    counts[dia] = 0
                counts[dia] += 1
                for c in _COLS:
                    try:
                        sums[dia][c] += float(row.get(c) or 0.0)
                    except (TypeError, ValueError):
                        pass

        if not sums:
            return []

        # Tomar los últimos N días
        all_dias = sorted(sums.keys())
        dias     = all_dias[-last_n_days:]

        return [
            {"dia": d, **{c: sums[d][c] / max(counts[d], 1) for c in _COLS}}
            for d in dias
        ]
    except Exception as e:
        print(f"[db_reader] load_emergence_metrics: {e}", file=sys.stderr)
        return []


def load_deaths_log(limit: int = 100) -> list[dict]:
    """Últimas N muertes en orden descendente."""
    conn = _conn()
    if conn is None:
        return []
    try:
        rows = conn.execute("""
            SELECT dia, nombre, causa
            FROM deaths_log
            ORDER BY dia DESC, tick DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[db_reader] load_deaths_log: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()
