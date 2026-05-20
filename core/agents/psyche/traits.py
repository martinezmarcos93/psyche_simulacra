from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TraitProfile:
    """
    Rasgos psicológicos dimensionales: Big Five + 9 dimensiones clínicas.
    Todos en rango 0.0 → 1.0.
    """
    # Big Five
    apertura:        float = 0.50
    responsabilidad: float = 0.50
    extraversion:    float = 0.50
    amabilidad:      float = 0.50
    neuroticismo:    float = 0.40

    # Dimensiones clínicas
    impulsividad:               float = 0.30
    disociacion:                float = 0.20
    empatia:                    float = 0.55
    paranoia:                   float = 0.20
    narcisismo:                 float = 0.30
    estabilidad_emocional:      float = 0.60
    sensibilidad_dopaminergica: float = 0.50
    agresividad:                float = 0.25
    ansiedad_rasgo:             float = 0.35

    def mood_modifier(self) -> float:
        """
        Modificador base del estado de ánimo derivado de rasgos estables.
        Positivo → tendencia al humor positivo; negativo → al negativo.
        """
        positivo = (self.estabilidad_emocional + self.amabilidad + self.empatia) / 3
        negativo = (self.neuroticismo + self.ansiedad_rasgo + self.paranoia) / 3
        return (positivo - negativo)

    def action_bias(self, action: str) -> float:
        """
        Sesgo de rasgo para una acción cuántica. Delta entre -0.5 y +0.5.
        """
        if action == "cooperacion":
            return (self.amabilidad + self.empatia - self.agresividad - self.paranoia) * 0.25
        if action == "competencia":
            return (self.agresividad + self.narcisismo + self.sensibilidad_dopaminergica - self.amabilidad) * 0.25
        if action == "aislamiento":
            return ((1.0 - self.extraversion) + self.disociacion + self.ansiedad_rasgo - self.amabilidad) * 0.20
        if action == "manipulacion":
            return (self.narcisismo + self.impulsividad + self.paranoia - self.empatia - self.amabilidad) * 0.20
        return 0.0

    def exploration_drive(self) -> float:
        """Impulso a explorar territorio nuevo (0→1)."""
        return (self.apertura + self.sensibilidad_dopaminergica * 0.5) / 1.5

    def social_drive(self) -> float:
        """Impulso a interactuar con otros (0→1)."""
        return (self.extraversion + self.amabilidad * 0.5) / 1.5

    def stress_sensitivity(self) -> float:
        """Cuánto amplifican los rasgos el estrés por necesidades críticas."""
        return (self.neuroticismo + self.ansiedad_rasgo) * 0.5

    def to_dict(self) -> dict[str, float]:
        return {
            "apertura":                    self.apertura,
            "responsabilidad":             self.responsabilidad,
            "extraversion":                self.extraversion,
            "amabilidad":                  self.amabilidad,
            "neuroticismo":                self.neuroticismo,
            "impulsividad":                self.impulsividad,
            "disociacion":                 self.disociacion,
            "empatia":                     self.empatia,
            "paranoia":                    self.paranoia,
            "narcisismo":                  self.narcisismo,
            "estabilidad_emocional":       self.estabilidad_emocional,
            "sensibilidad_dopaminergica":  self.sensibilidad_dopaminergica,
            "agresividad":                 self.agresividad,
            "ansiedad_rasgo":              self.ansiedad_rasgo,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> TraitProfile:
        tp = cls()
        for attr in tp.to_dict():
            if attr in data:
                setattr(tp, attr, float(data[attr]))
        return tp
