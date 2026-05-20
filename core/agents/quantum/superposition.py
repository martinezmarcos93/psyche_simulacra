from __future__ import annotations

import random
from dataclasses import dataclass, field

# Los cuatro estados conductuales posibles
BEHAVIORAL_STATES = ("cooperacion", "competencia", "aislamiento", "manipulacion")


@dataclass
class BehavioralState:
    """
    Vector de superposición conductual.
    Cuatro amplitudes de probabilidad que suman 1.0.
    No son amplitudes complejas — usamos probabilidades reales por simplicidad
    computacional manteniendo la semántica cuántica del modelo.
    """
    cooperacion:  float = 0.40
    competencia:  float = 0.25
    aislamiento:  float = 0.20
    manipulacion: float = 0.15

    # Último colapso observado
    ultimo_colapso: str = "cooperacion"

    def __post_init__(self) -> None:
        self._normalize()

    def _normalize(self) -> None:
        total = self.cooperacion + self.competencia + self.aislamiento + self.manipulacion
        if total <= 0:
            self.cooperacion  = 0.40
            self.competencia  = 0.25
            self.aislamiento  = 0.20
            self.manipulacion = 0.15
            return
        self.cooperacion  /= total
        self.competencia  /= total
        self.aislamiento  /= total
        self.manipulacion /= total

    def apply_bias(self, deltas: dict[str, float]) -> None:
        """
        Aplica deltas externos al vector (de arquetipos, complejos, rasgos,
        campo colectivo) y renormaliza.
        """
        self.cooperacion  = max(0.01, self.cooperacion  + deltas.get("cooperacion",  0.0))
        self.competencia  = max(0.01, self.competencia  + deltas.get("competencia",  0.0))
        self.aislamiento  = max(0.01, self.aislamiento  + deltas.get("aislamiento",  0.0))
        self.manipulacion = max(0.01, self.manipulacion + deltas.get("manipulacion", 0.0))
        self._normalize()

    def probabilities(self) -> dict[str, float]:
        return {
            "cooperacion":  self.cooperacion,
            "competencia":  self.competencia,
            "aislamiento":  self.aislamiento,
            "manipulacion": self.manipulacion,
        }

    def dominant(self) -> str:
        probs = self.probabilities()
        return max(probs, key=probs.get)

    def sample(self, rng: random.Random | None = None) -> str:
        """Colapsa el estado por muestreo ponderado."""
        r = rng or random
        states  = list(BEHAVIORAL_STATES)
        weights = [self.cooperacion, self.competencia, self.aislamiento, self.manipulacion]
        return r.choices(states, weights=weights, k=1)[0]

    def decay_toward_base(
        self,
        base: BehavioralState,
        rate: float = 0.02,
    ) -> None:
        """
        Empuja suavemente el vector actual hacia un estado base (personalidad
        estable), simulando la resiliencia psicológica.
        """
        self.cooperacion  += (base.cooperacion  - self.cooperacion)  * rate
        self.competencia  += (base.competencia  - self.competencia)  * rate
        self.aislamiento  += (base.aislamiento  - self.aislamiento)  * rate
        self.manipulacion += (base.manipulacion - self.manipulacion) * rate
        self._normalize()

    def to_dict(self) -> dict:
        return {
            "cooperacion":   self.cooperacion,
            "competencia":   self.competencia,
            "aislamiento":   self.aislamiento,
            "manipulacion":  self.manipulacion,
            "ultimo_colapso": self.ultimo_colapso,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BehavioralState:
        bs = cls(
            cooperacion  = float(data.get("cooperacion",  0.40)),
            competencia  = float(data.get("competencia",  0.25)),
            aislamiento  = float(data.get("aislamiento",  0.20)),
            manipulacion = float(data.get("manipulacion", 0.15)),
        )
        bs.ultimo_colapso = data.get("ultimo_colapso", "cooperacion")
        return bs

    @classmethod
    def from_archetype_dominant(cls, dominant: str) -> BehavioralState:
        """
        Crea un BehavioralState base coherente con el arquetipo dominante.
        Usado para inicializar agentes desde YAML.
        """
        presets = {
            "heroe":       cls(0.35, 0.40, 0.10, 0.15),
            "madre":       cls(0.55, 0.15, 0.15, 0.15),
            "sombra":      cls(0.15, 0.30, 0.30, 0.25),
            "trickster":   cls(0.20, 0.25, 0.15, 0.40),
            "sabio":       cls(0.30, 0.15, 0.40, 0.15),
            "gobernante":  cls(0.25, 0.45, 0.10, 0.20),
            "rebelde":     cls(0.20, 0.35, 0.25, 0.20),
            "nino_divino": cls(0.50, 0.15, 0.25, 0.10),
            "persona":     cls(0.45, 0.25, 0.15, 0.15),
            "padre":       cls(0.30, 0.40, 0.15, 0.15),
            "anima_animus":cls(0.40, 0.20, 0.25, 0.15),
            "self":        cls(0.35, 0.25, 0.20, 0.20),
        }
        return presets.get(dominant, cls())
