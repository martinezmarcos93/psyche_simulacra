from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SYMBOLS = {
    "heroe": 0.0,
    "sombra": 0.0,
    "muerte": 0.0,
    "fuego": 0.0,
    "comida": 0.0,
    "trickster": 0.0,
    "madre": 0.0,
    # Arquetipos extendidos para soporte N-dimensional de mitos
    "sabio":       0.0,
    "padre":       0.0,
    "gobernante":  0.0,
    "rebelde":     0.0,
    "nino_divino": 0.0,
}


@dataclass
class ContextoEnunciativo:
    """
    Contexto de cristalización simbólica — portado de Saussure-Quantum (collapse.py).

    Parámetros que determinan cómo y cuándo un proto-mito colapsa en mito real:

        temperatura_semantica: Intensidad emocional colectiva (0=fría, 1=ardiente).
            Alta temperatura → colapso más probable y más rápido.
            Equivalente a emotional_pressure + myth_pressure combinados.

        intencionalidad: Presión del par arquetípico dominante en el campo.
            Qué arquetipo está "empujando" para volverse mito.
            Deriva de los símbolos más cargados del CollectiveField.

        ruido_ambiental: Confusión epistémica colectiva (0=claridad, 1=caos).
            Alta confusión → el mito puede nacer de forma más distorsionada.
            Deriva del campo confusion acumulado por eventos inexplicables.
    """
    temperatura_semantica: float = 0.0
    intencionalidad: float = 0.0
    ruido_ambiental: float = 0.0

    def probabilidad_cristalizacion(self) -> float:
        """
        Probabilidad base de que un proto-mito cristalice en este contexto.

        Fórmula inspirada en la medición débil de Saussure-Quantum:
        la cristalización necesita temperatura alta + intencionalidad alta,
        y el ruido la perturba (puede acelerar o distorsionar).
        """
        base = self.temperatura_semantica * self.intencionalidad
        perturbacion = self.ruido_ambiental * 0.3
        return min(1.0, max(0.0, base + perturbacion))


class CollectiveField:
    """
    El inconsciente colectivo representado como un campo emergente de símbolos,
    tensión emocional y presión mítica.

    Extendido con:
    - myth_pressure: acumulación de trauma sin narrativa que lo contenga.
    - confusion: caos epistémico por eventos inexplicables.
    - contexto_enunciativo(): contexto de cristalización (Saussure-Quantum).
    - absorb_trauma(): eventos de alta intensidad que generan presión mítica.
    """

    def __init__(self) -> None:
        self.symbols = dict(DEFAULT_SYMBOLS)
        self.emotional_pressure = 0.0
        # Presión mítica: trauma acumulado sin narrativa que lo contenga.
        # Cuando supera el umbral, el motor de mitología puede cristalizar mitos.
        self.myth_pressure: float = 0.0
        # Confusión epistémica: cuánto no entiende la tribu lo que le pasa.
        # Alta confusión + alta presión = condiciones óptimas para crear mitos.
        self.confusion: float = 0.0

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
        """Absorbe eventos de alta significancia, como la muerte o el nacimiento de un agente."""
        if event_type == "muerte":
            self.symbols["muerte"] = min(1.0, self.symbols["muerte"] + 0.40 * intensity)
            self.symbols["sombra"] = min(1.0, self.symbols["sombra"] + 0.20 * intensity)
            self.emotional_pressure = min(1.0, self.emotional_pressure + 0.30 * intensity)
        elif event_type == "nacimiento":
            self.symbols["madre"]  = min(1.0, self.symbols["madre"]  + 0.25 * intensity)
            self.symbols["heroe"]  = min(1.0, self.symbols["heroe"]  + 0.10 * intensity)
            self.emotional_pressure = max(0.0, self.emotional_pressure - 0.10 * intensity)

    def absorb_trauma(self, causa: str, intensity: float = 1.0) -> None:
        """
        Absorbe eventos traumáticos inexplicables que generan presión mítica.

        La presión mítica es la acumulación de experiencias que la tribu no puede
        procesar con su modelo del mundo actual. Cuando supera el umbral, el motor
        de mitología tiene las condiciones para cristalizar un proto-mito.

        Args:
            causa: Tipo de trauma ('deshidratacion', 'muerte_masiva', 'hambruna',
                   'clima_extremo', 'extincion_inminente').
            intensity: Factor de intensidad (0.0–1.0).
        """
        # El trauma siempre aumenta la presión mítica y la confusión
        self.myth_pressure  = min(1.0, self.myth_pressure  + 0.20 * intensity)
        self.confusion      = min(1.0, self.confusion      + 0.15 * intensity)
        self.emotional_pressure = min(1.0, self.emotional_pressure + 0.10 * intensity)

        # Cargar los símbolos específicos según el tipo de trauma
        _trauma_symbols: dict[str, dict[str, float]] = {
            "deshidratacion":   {"muerte": 0.30, "sombra": 0.15},
            "muerte_masiva":    {"muerte": 0.50, "sombra": 0.25, "padre": 0.10},
            "hambruna":         {"muerte": 0.20, "madre": 0.20, "sombra": 0.10},
            "clima_extremo":    {"muerte": 0.15, "gobernante": 0.15, "nino_divino": 0.10},
            "extincion_inminente": {"muerte": 0.60, "sombra": 0.30, "sabio": 0.20},
        }
        for sym, delta in _trauma_symbols.get(causa, {}).items():
            self.symbols[sym] = min(1.0, self.symbols.get(sym, 0.0) + delta * intensity)

    def contexto_enunciativo(self) -> ContextoEnunciativo:
        """
        Calcula el contexto de cristalización simbólica actual del campo.

        Portado conceptualmente de Saussure-Quantum (collapse.py, ContextoEnunciativo).

        Returns:
            ContextoEnunciativo con los tres parámetros de cristalización:
            temperatura_semantica, intencionalidad, ruido_ambiental.
        """
        # Temperatura semántica: combinación de presión emocional y mítica
        temperatura = min(1.0, (self.emotional_pressure + self.myth_pressure) / 2.0)

        # Intencionalidad: cuánto el par arquetípico dominante está "empujando"
        # Se calcula como el promedio de los dos símbolos más cargados
        sorted_symbols = sorted(self.symbols.values(), reverse=True)
        intencionalidad = (sorted_symbols[0] + sorted_symbols[1]) / 2.0 if len(sorted_symbols) >= 2 else 0.0
        intencionalidad = min(1.0, intencionalidad)

        # Ruido ambiental: la confusión epistémica del campo
        ruido = self.confusion

        return ContextoEnunciativo(
            temperatura_semantica=temperatura,
            intencionalidad=intencionalidad,
            ruido_ambiental=ruido,
        )

    def dominant_archetype_pair(self) -> tuple[str, str]:
        """
        Retorna el par de arquetipos con mayor carga en el campo.
        Usado por el motor de mitología para determinar qué mito cristalizar.
        """
        sorted_syms = sorted(self.symbols.items(), key=lambda x: -x[1])
        if len(sorted_syms) >= 2:
            return sorted_syms[0][0], sorted_syms[1][0]
        elif sorted_syms:
            return sorted_syms[0][0], "sombra"
        return "heroe", "sombra"

    def decay(self, rate: float = 0.02) -> None:
        """Aplica decaimiento diario de cargas meméticas, presión y confusión."""
        factor = 1.0 - rate
        for k in self.symbols:
            self.symbols[k] = max(0.0, self.symbols[k] * factor)
        self.emotional_pressure = max(0.0, self.emotional_pressure * factor)
        # myth_pressure decae más lento que los símbolos (trauma persiste más)
        self.myth_pressure = max(0.0, self.myth_pressure * (1.0 - rate * 0.5))
        # La confusión se disipa cuando no hay nuevos traumas
        self.confusion = max(0.0, self.confusion * (1.0 - rate * 0.7))

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
            "symbols":            dict(self.symbols),
            "emotional_pressure": self.emotional_pressure,
            "myth_pressure":      self.myth_pressure,
            "confusion":          self.confusion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CollectiveField:
        f = cls()
        raw_symbols = data.get("symbols", dict(DEFAULT_SYMBOLS))
        # Asegurar que todos los símbolos del default estén presentes
        f.symbols = {**dict(DEFAULT_SYMBOLS), **raw_symbols}
        f.emotional_pressure = data.get("emotional_pressure", 0.0)
        f.myth_pressure      = data.get("myth_pressure",      0.0)
        f.confusion          = data.get("confusion",          0.0)
        return f
