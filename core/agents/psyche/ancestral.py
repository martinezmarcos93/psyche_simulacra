from __future__ import annotations

from dataclasses import dataclass


def _significance(edad: int, sabio: float, n_conocimientos: int) -> float:
    """
    Significancia simbólica de un agente al morir.
    Cualquiera de las tres condiciones es suficiente por sí sola para alcanzar
    el umbral de 0.40 que activa UnprocessedGrief en la tribu.

    Elder (edad ≥ 50):              +0.45
    Sabio alto (> 0.55):            +min(0.45, sabio × 0.60)
    Portador de conocimiento (≥ 2): +min(0.45, n × 0.18)
    """
    score = 0.0
    if edad >= 50:
        score += 0.45
    if sabio > 0.55:
        score += min(0.45, sabio * 0.60)
    if n_conocimientos >= 2:
        score += min(0.45, n_conocimientos * 0.18)
    return min(1.0, score)


@dataclass
class UnprocessedGrief:
    """
    Duelo colectivo no procesado por la pérdida de una figura de alta significancia.

    NO es un estado sobrenatural: es la perturbación psicológica colectiva
    que ocurre cuando una figura simbólicamente central muere sin cierre ritual.
    Los arquetipos del fallecido siguen cargándose en el ICL de forma autónoma
    porque la tribu habla de él, lo evoca, lo usa como referencia en decisiones.

    Efectos mientras esté activo (no convertido):
      - Carga diaria del arquetipo del fallecido en el ICL tribal.
      - Agentes en el GraveHex experimentan presión simbólica (ansiedad + compulsión).
      - Descendientes directos heredan complejo de culpa aumentado.

    Resolución: un agente con sabio alto realiza ritual de integración colectiva.
      → convertido = True: los mismos efectos se invierten (protección ancestral).
    """
    nombre_fallecido: str
    arquetipo:        str
    dia_muerte:       int
    grave_coord:      tuple[int, int] | None
    intensidad:       float   # significancia simbólica (0.0–1.0)
    tribe_id:         str
    dias_activo:      int  = 0
    convertido:       bool = False   # True = presencia ancestral protectora
    resuelto:         bool = False   # True = eliminar de la lista

    def to_dict(self) -> dict:
        return {
            "nombre_fallecido": self.nombre_fallecido,
            "arquetipo":        self.arquetipo,
            "dia_muerte":       self.dia_muerte,
            "grave_coord":      list(self.grave_coord) if self.grave_coord else None,
            "intensidad":       self.intensidad,
            "tribe_id":         self.tribe_id,
            "dias_activo":      self.dias_activo,
            "convertido":       self.convertido,
            "resuelto":         self.resuelto,
        }

    @classmethod
    def from_dict(cls, d: dict) -> UnprocessedGrief:
        gc = d.get("grave_coord")
        return cls(
            nombre_fallecido = d["nombre_fallecido"],
            arquetipo        = d["arquetipo"],
            dia_muerte       = int(d["dia_muerte"]),
            grave_coord      = tuple(gc) if gc else None,
            intensidad       = float(d["intensidad"]),
            tribe_id         = d["tribe_id"],
            dias_activo      = int(d.get("dias_activo", 0)),
            convertido       = bool(d.get("convertido", False)),
            resuelto         = bool(d.get("resuelto", False)),
        )
