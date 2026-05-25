from __future__ import annotations

from dataclasses import dataclass

# Duración del duelo según bond con el fallecido
def duracion_por_bond(bond: float) -> int:
    if bond > 0.90:
        return 90
    if bond > 0.70:
        return 50
    return 20  # bond 0.50-0.70


@dataclass
class GriefState:
    """
    Estado de duelo activo en un agente por la pérdida de un ser cercano.

    La duración es proporcional al bond: 20/50/90 días.
    Si ≥ 2 agentes dolientes se reúnen en el GraveHex en ≤ 5 días desde la muerte
    → ritual espontáneo → duración reducida × 0.50 + proto-mito emergente.
    Sin ritual: la memoria asociada revive con probabilidad aumentada × 1.5.
    """
    agente_fallecido:  str
    arquetipo:         str              # arquetipo del fallecido (para sueños)
    bond_al_morir:     float
    dia_inicio:        int
    duracion_dias:     int              # calculada según bond
    grave_coord:       tuple[int, int] | None
    ritual_realizado:  bool = False
    sin_anclaje:       bool = False     # murió sin GraveHex con carga previa
    dias_activo:       int  = 0

    def is_expired(self) -> bool:
        return self.dias_activo >= self.duracion_dias

    def ansiedad_delta(self) -> float:
        """Contribución diaria de ansiedad según intensidad del bond."""
        if self.bond_al_morir > 0.90:
            return 0.030
        if self.bond_al_morir > 0.70:
            return 0.018
        return 0.008

    def to_dict(self) -> dict:
        return {
            "agente_fallecido": self.agente_fallecido,
            "arquetipo":        self.arquetipo,
            "bond_al_morir":    self.bond_al_morir,
            "dia_inicio":       self.dia_inicio,
            "duracion_dias":    self.duracion_dias,
            "grave_coord":      list(self.grave_coord) if self.grave_coord else None,
            "ritual_realizado": self.ritual_realizado,
            "sin_anclaje":      self.sin_anclaje,
            "dias_activo":      self.dias_activo,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GriefState:
        gc = d.get("grave_coord")
        return cls(
            agente_fallecido = d["agente_fallecido"],
            arquetipo        = d["arquetipo"],
            bond_al_morir    = float(d["bond_al_morir"]),
            dia_inicio       = int(d["dia_inicio"]),
            duracion_dias    = int(d["duracion_dias"]),
            grave_coord      = tuple(gc) if gc else None,
            ritual_realizado = bool(d.get("ritual_realizado", False)),
            sin_anclaje      = bool(d.get("sin_anclaje", False)),
            dias_activo      = int(d.get("dias_activo", 0)),
        )
