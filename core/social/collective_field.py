from __future__ import annotations

DEFAULT_SYMBOLS = {
    "heroe": 0.0,
    "sombra": 0.0,
    "muerte": 0.0,
    "fuego": 0.0,
    "comida": 0.0,
    "trickster": 0.0,
    "madre": 0.0,
}


class CollectiveField:
    """
    El inconsciente colectivo representado como un campo emergente de símbolos
    y tensión emocional (presión). No es estático, decae con el tiempo y
    retroalimenta las probabilidades de colapso de todos los agentes.
    """

    def __init__(self) -> None:
        self.symbols = dict(DEFAULT_SYMBOLS)
        self.emotional_pressure = 0.0

    def absorb_interaction(self, state_a: str, state_b: str, outcome_type: str) -> None:
        """
        Cada interacción altera la carga memética de los símbolos y la
        presión emocional del campo colectivo.
        """
        if outcome_type == "cooperacion_pura":
            self.symbols["heroe"] = min(1.0, self.symbols["heroe"] + 0.08)
            self.symbols["madre"] = min(1.0, self.symbols["madre"] + 0.04)
            self.emotional_pressure = max(0.0, self.emotional_pressure - 0.05)

        elif outcome_type == "conflicto_explotacion":
            self.symbols["sombra"] = min(1.0, self.symbols["sombra"] + 0.10)
            self.emotional_pressure = min(1.0, self.emotional_pressure + 0.08)

        elif outcome_type == "choque_violento":
            self.symbols["sombra"] = min(1.0, self.symbols["sombra"] + 0.18)
            self.emotional_pressure = min(1.0, self.emotional_pressure + 0.15)

        elif outcome_type == "exito_manipulacion":
            self.symbols["trickster"] = min(1.0, self.symbols["trickster"] + 0.07)
            self.emotional_pressure = min(1.0, self.emotional_pressure + 0.03)

        elif outcome_type == "fracaso_manipulacion":
            self.symbols["trickster"] = min(1.0, self.symbols["trickster"] + 0.09)
            self.symbols["sombra"] = min(1.0, self.symbols["sombra"] + 0.05)
            self.emotional_pressure = min(1.0, self.emotional_pressure + 0.06)

    def absorb_event(self, event_type: str, intensity: float = 1.0) -> None:
        """Absorbe eventos de alta significancia, como la muerte de un agente."""
        if event_type == "muerte":
            self.symbols["muerte"] = min(1.0, self.symbols["muerte"] + 0.40 * intensity)
            self.symbols["sombra"] = min(1.0, self.symbols["sombra"] + 0.20 * intensity)
            self.emotional_pressure = min(1.0, self.emotional_pressure + 0.30 * intensity)

    def decay(self, rate: float = 0.02) -> None:
        """Aplica decaimiento diario (u horaria si se requiere) de cargas meméticas."""
        factor = 1.0 - rate
        for k in self.symbols:
            self.symbols[k] = max(0.0, self.symbols[k] * factor)
        self.emotional_pressure = max(0.0, self.emotional_pressure * factor)

    def radiate(self) -> dict[str, float]:
        """
        Calcula la radiación o deltas de retroalimentación para cada
        una de las 4 acciones de collapse_state.
        """
        return {
            "cooperacion": (self.symbols["heroe"] + self.symbols["madre"]) * 0.25 - self.emotional_pressure * 0.10,
            "competencia": self.symbols["sombra"] * 0.20 + self.emotional_pressure * 0.25,
            "aislamiento": self.emotional_pressure * 0.20 + self.symbols["sombra"] * 0.15,
            "manipulacion": self.symbols["trickster"] * 0.25,
        }

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "symbols": dict(self.symbols),
            "emotional_pressure": self.emotional_pressure,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CollectiveField:
        field = cls()
        field.symbols = data.get("symbols", dict(DEFAULT_SYMBOLS))
        field.emotional_pressure = data.get("emotional_pressure", 0.0)
        return field
