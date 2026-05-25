from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SocialRole:
    """
    Rol social emergente reconocido colectivamente por la tribu (Hito H).

    Tipos (basados en etnografía real):
      anciano      — mayor edad + bonds altos; autoridad tradicional (Weber).
      big_man      — mayor redistribución simbólica de bonds; autoridad carismática (Sahlins).
      cazador_focal— mayor éxito de subsistencia; autoridad funcional, frágil.

    El rol no se asigna: emerge de la acumulación de métricas observables.
    La legitimidad decae si el portador deja de cumplir los criterios.
    """
    tipo:             str           # "anciano" | "big_man" | "cazador_focal"
    portador_id:      str
    portador_nombre:  str
    tribe_id:         str
    dia_inicio:       int
    legitimidad:      float = 1.0   # 0.0–1.0
    is_active:        bool  = True
    dias_transicion:  int   = 0     # > 0 → rol vacante en transición
    candidato_id:     str | None = None

    def to_dict(self) -> dict:
        return {
            "tipo":            self.tipo,
            "portador_id":     self.portador_id,
            "portador_nombre": self.portador_nombre,
            "tribe_id":        self.tribe_id,
            "dia_inicio":      self.dia_inicio,
            "legitimidad":     self.legitimidad,
            "is_active":       self.is_active,
            "dias_transicion": self.dias_transicion,
            "candidato_id":    self.candidato_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SocialRole:
        return cls(
            tipo            = d["tipo"],
            portador_id     = d["portador_id"],
            portador_nombre = d["portador_nombre"],
            tribe_id        = d["tribe_id"],
            dia_inicio      = int(d["dia_inicio"]),
            legitimidad     = float(d.get("legitimidad", 1.0)),
            is_active       = bool(d.get("is_active", True)),
            dias_transicion = int(d.get("dias_transicion", 0)),
            candidato_id    = d.get("candidato_id"),
        )
