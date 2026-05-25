from __future__ import annotations

from dataclasses import dataclass, field

# Prefijos por tipo de objeto — nombre procedural generado en el momento de creación
_SACRED_OBJECT_PREFIXES: dict[str, list[str]] = {
    "protector":   ["Amuleto", "Fetiche", "Tótem"],
    "ambiguo":     ["Reliquia", "Símbolo", "Objeto Sagrado"],
    "duelo":       ["Recuerdo", "Memoria del Caído", "Reliquia Funeraria"],
    "perturbador": ["Tótem Maldito", "Objeto Tapu", "Símbolo Oscuro"],
}


@dataclass
class SacredObject:
    """
    Objeto material que cristaliza el estado psicológico colectivo del creador.

    Cuatro tipos (Hito C, Roadmap 4):
      protector   — ICL cohesionado, baja ansiedad: reduce ansiedad de portadores afines.
      ambiguo     — ICL en tensión: efectos opuestos según arquetipo del portador.
      duelo       — trauma de muerte activo: ancla pérdida en GraveHex.
      perturbador — sombra dominante o disociación: eleva ansiedad de portadores y vecinos.

    Puede heredarse, perderse o quedar en un hex sin portador.
    """
    nombre:               str
    tipo:                 str                        # "protector" | "ambiguo" | "duelo" | "perturbador"
    arquetipo_dominante:  str
    intensidad_simbolica: float                      # 0.0–1.0
    creador_id:           str
    creador_nombre:       str
    dia_creacion:         int
    propietario_id:       str | None                 # None = sin portador (en hex)
    hex_coord:            tuple[int, int] | None
    historial:            list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nombre":               self.nombre,
            "tipo":                 self.tipo,
            "arquetipo_dominante":  self.arquetipo_dominante,
            "intensidad_simbolica": self.intensidad_simbolica,
            "creador_id":           self.creador_id,
            "creador_nombre":       self.creador_nombre,
            "dia_creacion":         self.dia_creacion,
            "propietario_id":       self.propietario_id,
            "hex_coord":            list(self.hex_coord) if self.hex_coord else None,
            "historial":            list(self.historial),
        }

    @classmethod
    def from_dict(cls, d: dict) -> SacredObject:
        hc = d.get("hex_coord")
        return cls(
            nombre               = d["nombre"],
            tipo                 = d["tipo"],
            arquetipo_dominante  = d["arquetipo_dominante"],
            intensidad_simbolica = float(d.get("intensidad_simbolica", 0.5)),
            creador_id           = d["creador_id"],
            creador_nombre       = d["creador_nombre"],
            dia_creacion         = int(d["dia_creacion"]),
            propietario_id       = d.get("propietario_id"),
            hex_coord            = tuple(hc) if hc else None,
            historial            = list(d.get("historial", [])),
        )
