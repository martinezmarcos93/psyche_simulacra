from __future__ import annotations

import random
from dataclasses import dataclass

_MAX_SHORT = 8
_MAX_LONG  = 8

# Probabilidad base de re-vivencia por día = intensidad × _REVIVAL_BASE
_REVIVAL_BASE        = 0.03
# Impacto emocional de la re-vivencia = intensidad × _REVIVAL_IMPACT
_REVIVAL_IMPACT      = 0.60
# Factor de atenuación acumulativa por número de re-vivencias (0.90^n)
_REVIVAL_DECAY       = 0.90
# Umbral de trauma activo (contribuye diariamente al ICL)
_ACTIVE_TRAUMA_FLOOR = 0.80


@dataclass
class MemoryRecord:
    """Registro de una memoria episódica estructurada."""
    tipo_evento:          str    # "muerte_vinculo", "trauma_catastrofe", "vision", ...
    intensidad_emocional: float  # 0.0–1.0
    dia_origen:           int
    agente_protagonista:  str    # nombre del agente central del recuerdo
    arquetipo_dominante:  str    # arquetipo que carga este recuerdo
    dia_ultimo_revivido:  int = -1
    n_revivencias:        int = 0

    def revival_impact(self) -> float:
        """Impacto emocional en el agente al re-vivir, decrece con cada re-vivencia."""
        return (
            self.intensidad_emocional
            * _REVIVAL_IMPACT
            * (_REVIVAL_DECAY ** self.n_revivencias)
        )

    def to_dict(self) -> dict:
        return {
            "tipo_evento":          self.tipo_evento,
            "intensidad_emocional": self.intensidad_emocional,
            "dia_origen":           self.dia_origen,
            "agente_protagonista":  self.agente_protagonista,
            "arquetipo_dominante":  self.arquetipo_dominante,
            "dia_ultimo_revivido":  self.dia_ultimo_revivido,
            "n_revivencias":        self.n_revivencias,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MemoryRecord:
        return cls(
            tipo_evento          = d["tipo_evento"],
            intensidad_emocional = float(d["intensidad_emocional"]),
            dia_origen           = int(d["dia_origen"]),
            agente_protagonista  = d["agente_protagonista"],
            arquetipo_dominante  = d["arquetipo_dominante"],
            dia_ultimo_revivido  = int(d.get("dia_ultimo_revivido", -1)),
            n_revivencias        = int(d.get("n_revivencias", 0)),
        )


class EpisodicMemory:
    """
    Memoria episódica en dos capas:

    Corto plazo (max 8, FIFO): recuerdos recientes que decaen por desplazamiento.
    Largo plazo (max 8, por intensidad): traumas que *regresan* probabilísticamente.

    La re-vivencia no restaura el hecho original — amplifica el elemento arquetípico
    y borra detalles periféricos (Freud: compulsión de repetición; Jung: irrupción
    del complejo). El impacto emocional del recuerdo se atenúa con cada re-vivencia.
    """

    def __init__(self) -> None:
        self._short: list[MemoryRecord] = []
        self._long:  list[MemoryRecord] = []

    def record(self, rec: MemoryRecord) -> None:
        """
        Ingresa un nuevo recuerdo al sistema.
        - Siempre al corto plazo (FIFO).
        - Si intensidad ≥ 0.60, también al largo plazo (desplaza el de menor intensidad).
        """
        self._short.append(rec)
        if len(self._short) > _MAX_SHORT:
            self._short.pop(0)

        if rec.intensidad_emocional >= 0.60:
            self._long.append(rec)
            if len(self._long) > _MAX_LONG:
                self._long.sort(key=lambda r: r.intensidad_emocional)
                self._long.pop(0)

    def process_revivals(self, dia: int, rng: random.Random) -> list[MemoryRecord]:
        """
        Procesa re-vivencias de largo plazo para este día.

        Cada registro tiene probabilidad = intensidad × _REVIVAL_BASE de re-activarse.
        Los registros revividos se retornan; el llamador aplica sus efectos.
        El arquetipo del recuerdo se amplifica con cada re-vivencia (distorsión).
        """
        revived: list[MemoryRecord] = []
        for rec in self._long:
            if rng.random() < rec.intensidad_emocional * _REVIVAL_BASE:
                rec.dia_ultimo_revivido = dia
                rec.n_revivencias      += 1
                revived.append(rec)
        return revived

    def active_traumas(self) -> list[MemoryRecord]:
        """Traumas activos: largo plazo con intensidad > _ACTIVE_TRAUMA_FLOOR."""
        return [r for r in self._long if r.intensidad_emocional > _ACTIVE_TRAUMA_FLOOR]

    def all_long_term(self) -> list[MemoryRecord]:
        return list(self._long)

    def all_short_term(self) -> list[MemoryRecord]:
        return list(self._short)

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "short": [r.to_dict() for r in self._short],
            "long":  [r.to_dict() for r in self._long],
        }

    @classmethod
    def from_dict(cls, data: dict) -> EpisodicMemory:
        em = cls()
        em._short = [MemoryRecord.from_dict(r) for r in data.get("short", [])]
        em._long  = [MemoryRecord.from_dict(r) for r in data.get("long",  [])]
        return em
