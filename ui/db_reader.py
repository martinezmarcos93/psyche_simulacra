"""
Lecturas no bloqueantes de la DB SQLite y del checkpoint JSON.
Espejo de lo que hace el Streamlit dashboard, adaptado para NiceGUI.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


_DB_PATH   = Path("data/db/simulation.db")
_CP_DIR    = Path("data/checkpoints")


# ── Checkpoint JSON ───────────────────────────────────────────────────────────

def load_checkpoint() -> dict | None:
    candidates = sorted(_CP_DIR.glob("checkpoint_*.json"), reverse=True)
    for path in candidates[:2]:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
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
    except Exception:
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
    except Exception:
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
    except Exception:
        return []
    finally:
        conn.close()


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
    except Exception:
        return []
    finally:
        conn.close()
