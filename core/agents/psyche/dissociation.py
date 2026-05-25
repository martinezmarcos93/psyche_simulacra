from __future__ import annotations

from dataclasses import dataclass

# ── Constantes ────────────────────────────────────────────────────────────────

ANSIEDAD_UMBRAL   = 0.85   # ansiedad mínima para contar día de riesgo
DIAS_UMBRAL       = 5      # días consecutivos en umbral → colapso
DIAS_PERMANENCIA  = 15     # días sin intervención → estado permanente

TIPOS = [
    "melancolia_disociativa",
    "amok",
    "fuga_disociativa",
    "estupor_catatonico",
]

# Arquetipo dominante → estado más probable al colapsar
# Basado en la polaridad sombra de cada arquetipo (Jung, "Aion")
_ARCH_TO_TIPO: dict[str, str] = {
    "heroe":        "amok",                 # héroe poseído → guerrero destructor
    "padre":        "amok",
    "gobernante":   "amok",
    "sombra":       "melancolia_disociativa",
    "muerte":       "melancolia_disociativa",
    "nino_divino":  "melancolia_disociativa",
    "trickster":    "fuga_disociativa",     # trickster poseído → caos puro
    "rebelde":      "fuga_disociativa",
    "madre":        "fuga_disociativa",
    "sabio":        "estupor_catatonico",   # sabio poseído → vacío contemplativo
    "self_":        "estupor_catatonico",
    "persona":      "estupor_catatonico",
    "anima_animus": "fuga_disociativa",
}


@dataclass
class DissociativeState:
    """
    Estado de disociación por sombra activo en un agente.

    Tipos:
      melancolia_disociativa — aceptación pasiva de la muerte; no busca recursos.
      amok                  — violencia dirigida a los vínculos más fuertes.
      fuga_disociativa      — comportamiento errático, desconectado del arquetipo.
      estupor_catatonico    — inacción total; consume recursos sin producir.

    Entrada: ansiedad > 0.85 durante ≥ 5 días consecutivos.
    Permanencia: sin intervención en 15 días → estado irrecuperable.
    Salida natural: si ansiedad cae por debajo de 0.50 antes de los 15 días.
    """
    tipo:                  str
    dia_inicio:            int
    dias_activo:           int  = 0
    permanente:            bool = False
    intervencion_recibida: bool = False

    def to_dict(self) -> dict:
        return {
            "tipo":                  self.tipo,
            "dia_inicio":            self.dia_inicio,
            "dias_activo":           self.dias_activo,
            "permanente":            self.permanente,
            "intervencion_recibida": self.intervencion_recibida,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DissociativeState:
        return cls(
            tipo                  = d["tipo"],
            dia_inicio            = int(d["dia_inicio"]),
            dias_activo           = int(d.get("dias_activo", 0)),
            permanente            = bool(d.get("permanente", False)),
            intervencion_recibida = bool(d.get("intervencion_recibida", False)),
        )


def select_tipo(arch_dominante: str, rng) -> str:
    """
    Selecciona el tipo de disociación según el arquetipo dominante del agente.
    20% de varianza: el colapso no es completamente predecible.
    """
    tipo_base = _ARCH_TO_TIPO.get(arch_dominante, "melancolia_disociativa")
    if rng.random() < 0.20:
        alternates = [t for t in TIPOS if t != tipo_base]
        return rng.choice(alternates)
    return tipo_base
