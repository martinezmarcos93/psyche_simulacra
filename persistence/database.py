from __future__ import annotations

import json
import sqlite3
from pathlib import Path


_SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_snapshots (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    dia       INTEGER NOT NULL,
    agent_id  TEXT NOT NULL,
    nombre    TEXT NOT NULL,
    posicion  TEXT NOT NULL,
    rol       TEXT,
    is_alive  INTEGER NOT NULL,
    hambre    REAL, fatiga REAL, sed REAL,
    humor     REAL, energia REAL, ansiedad REAL,
    data_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_snapshots_dia     ON agent_snapshots(dia);
CREATE INDEX IF NOT EXISTS idx_agent_snapshots_agent   ON agent_snapshots(agent_id);

CREATE TABLE IF NOT EXISTS deaths_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tick      INTEGER NOT NULL,
    dia       INTEGER NOT NULL,
    agent_id  TEXT NOT NULL,
    nombre    TEXT NOT NULL,
    causa     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS climate_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    dia            INTEGER NOT NULL,
    hora           INTEGER NOT NULL,
    temperatura    REAL,
    precipitacion  REAL,
    luminosidad    REAL,
    estacion       TEXT,
    evento         TEXT,
    survival_risk  REAL,
    mood_modifier  REAL
);
CREATE INDEX IF NOT EXISTS idx_climate_log_dia ON climate_log(dia);

CREATE TABLE IF NOT EXISTS scenario_state_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    dia               INTEGER NOT NULL,
    resource_pressure REAL,
    carrying_capacity INTEGER,
    fuego_activo      INTEGER,
    fuego_intensidad  REAL,
    n_hexes_explorados INTEGER,
    data_json         TEXT
);

CREATE TABLE IF NOT EXISTS session_log (
    session_id              TEXT PRIMARY KEY,
    timestamp_inicio        TEXT NOT NULL,
    timestamp_fin           TEXT,
    dia_inicio_simulado     INTEGER,
    dia_fin_simulado        INTEGER,
    dias_procesados         INTEGER DEFAULT 0,
    duracion_real_segundos  REAL,
    razon_fin               TEXT,
    muertes_sesion          INTEGER DEFAULT 0,
    nacimientos_sesion      INTEGER DEFAULT 0,
    version_motor           TEXT
);

CREATE TABLE IF NOT EXISTS simulation_checkpoints (
    checkpoint_id   TEXT PRIMARY KEY,
    dia_simulado    INTEGER NOT NULL,
    hora_simulada   INTEGER NOT NULL,
    timestamp_real  TEXT NOT NULL,
    session_id      TEXT NOT NULL,
    razon           TEXT,
    archivo_json    TEXT NOT NULL
);
"""


class DatabaseManager:
    """Gestiona la base de datos SQLite de la simulación."""

    def __init__(self, db_path: str = "data/db/simulation.db") -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection = sqlite3.connect(
            str(self._path), check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._initialize_schema()

    # ── Inicialización ────────────────────────────────────────────────────────

    def _initialize_schema(self) -> None:
        self._conn.executescript(_DDL)
        cur = self._conn.execute("SELECT version FROM schema_version LIMIT 1")
        row = cur.fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO schema_version(version) VALUES (?)", (_SCHEMA_VERSION,)
            )
        self._conn.commit()

    # ── agent_snapshots ───────────────────────────────────────────────────────

    def insert_agent_snapshots(self, dia: int, agents_data: list[dict]) -> None:
        rows = []
        for a in agents_data:
            pos = a.get("posicion", [0, 0])
            rows.append((
                dia,
                a["id"], a["nombre"],
                f"{pos[0]},{pos[1]}",
                a.get("rol"),
                int(a.get("is_alive", True)),
                a.get("needs", {}).get("hambre"),
                a.get("needs", {}).get("fatiga"),
                a.get("needs", {}).get("sed"),
                a.get("humor"),
                a.get("energia"),
                a.get("ansiedad"),
                json.dumps(a, ensure_ascii=False),
            ))
        self._conn.executemany(
            """INSERT INTO agent_snapshots
               (dia, agent_id, nombre, posicion, rol, is_alive,
                hambre, fatiga, sed, humor, energia, ansiedad, data_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        self._conn.commit()

    # ── deaths_log ────────────────────────────────────────────────────────────

    def insert_death(self, death: dict) -> None:
        self._conn.execute(
            """INSERT INTO deaths_log(tick, dia, agent_id, nombre, causa)
               VALUES (?,?,?,?,?)""",
            (death["tick"], death["dia"], death["agent_id"], death["nombre"], death["causa"]),
        )
        self._conn.commit()

    def insert_deaths_batch(self, deaths: list[dict]) -> None:
        self._conn.executemany(
            """INSERT INTO deaths_log(tick, dia, agent_id, nombre, causa)
               VALUES (?,?,?,?,?)""",
            [(d["tick"], d["dia"], d["agent_id"], d["nombre"], d["causa"]) for d in deaths],
        )
        self._conn.commit()

    # ── climate_log ───────────────────────────────────────────────────────────

    def insert_climate_batch(self, rows: list[dict]) -> None:
        self._conn.executemany(
            """INSERT INTO climate_log
               (dia, hora, temperatura, precipitacion, luminosidad,
                estacion, evento, survival_risk, mood_modifier)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            [(r["dia"], r["hora"], r["temperatura"], r["precipitacion"],
              r["luminosidad"], r["estacion"], r.get("evento"),
              r["survival_risk"], r["mood_modifier"]) for r in rows],
        )
        self._conn.commit()

    # ── scenario_state_log ────────────────────────────────────────────────────

    def insert_scenario(self, dia: int, snap: object) -> None:
        self._conn.execute(
            """INSERT INTO scenario_state_log
               (dia, resource_pressure, carrying_capacity,
                fuego_activo, fuego_intensidad, n_hexes_explorados, data_json)
               VALUES (?,?,?,?,?,?,?)""",
            (
                dia,
                getattr(snap, "resource_pressure", None),
                getattr(snap, "carrying_capacity", None),
                int(getattr(snap, "fuego_activo", False)),
                getattr(snap, "fuego_intensidad", 0.0),
                len(getattr(snap, "recursos_por_hex", {})),
                None,
            ),
        )
        self._conn.commit()

    # ── session_log ───────────────────────────────────────────────────────────

    def upsert_session(self, session: dict) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO session_log
               (session_id, timestamp_inicio, timestamp_fin,
                dia_inicio_simulado, dia_fin_simulado, dias_procesados,
                duracion_real_segundos, razon_fin,
                muertes_sesion, nacimientos_sesion, version_motor)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                session["session_id"],
                session.get("timestamp_inicio"),
                session.get("timestamp_fin"),
                session.get("dia_inicio_simulado"),
                session.get("dia_fin_simulado"),
                session.get("dias_procesados", 0),
                session.get("duracion_real_segundos"),
                session.get("razon_fin"),
                session.get("muertes_sesion", 0),
                session.get("nacimientos_sesion", 0),
                session.get("version_motor", "0.1.0"),
            ),
        )
        self._conn.commit()

    # ── simulation_checkpoints ────────────────────────────────────────────────

    def insert_checkpoint_meta(self, meta: dict) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO simulation_checkpoints
               (checkpoint_id, dia_simulado, hora_simulada,
                timestamp_real, session_id, razon, archivo_json)
               VALUES (?,?,?,?,?,?,?)""",
            (
                meta["checkpoint_id"],
                meta["dia_simulado"],
                meta["hora_simulada"],
                meta["timestamp_real"],
                meta["session_id"],
                meta.get("razon"),
                meta["archivo_json"],
            ),
        )
        self._conn.commit()

    # ── Consultas ─────────────────────────────────────────────────────────────

    def get_deaths(self, desde_dia: int = 0) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM deaths_log WHERE dia >= ? ORDER BY dia", (desde_dia,)
        )
        return [dict(r) for r in cur.fetchall()]

    def get_agent_snapshot(self, agent_id: str, dia: int) -> dict | None:
        cur = self._conn.execute(
            "SELECT data_json FROM agent_snapshots WHERE agent_id=? AND dia=?",
            (agent_id, dia),
        )
        row = cur.fetchone()
        return json.loads(row["data_json"]) if row else None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        self._conn.close()

    @property
    def path(self) -> Path:
        return self._path
