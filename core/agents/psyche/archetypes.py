from __future__ import annotations

from dataclasses import dataclass, field

# Los 12 arquetipos jungianos
ARCHETYPE_NAMES = (
    "self", "persona", "sombra", "anima_animus",
    "heroe", "sabio", "trickster", "madre",
    "padre", "nino_divino", "gobernante", "rebelde",
)

# Qué arquetipos refuerzan/debilitan qué acción cuántica
# Cada clave es una acción, valor es dict {arquetipo: peso_modificador}
_ACTION_AFFINITY: dict[str, dict[str, float]] = {
    "cooperacion": {
        "madre": 0.20, "amante": 0.15, "self": 0.10,
        "sombra": -0.15, "rebelde": -0.10,
    },
    "competencia": {
        "heroe": 0.20, "gobernante": 0.15, "padre": 0.10,
        "nino_divino": -0.10, "madre": -0.10,
    },
    "aislamiento": {
        "sombra": 0.20, "sabio": 0.10, "anima_animus": 0.10,
        "persona": -0.15, "gobernante": -0.10,
    },
    "manipulacion": {
        "trickster": 0.25, "sombra": 0.15, "gobernante": 0.10,
        "self": -0.15, "sabio": -0.10,
    },
}

# Transformaciones: evento → cambio en arquetipos
_TRANSFORMATIONS: dict[str, dict[str, float]] = {
    "trauma":              {"sombra": +0.12, "heroe": -0.08, "self": -0.05},
    "power_corruption":    {"gobernante": +0.10, "sombra": +0.08, "self": -0.10},
    "prolonged_isolation": {"sombra": +0.08, "anima_animus": +0.06, "persona": -0.10},
    "sacred_crisis":       {"self": +0.12, "nino_divino": +0.08, "sombra": -0.05},
    "deep_bond":           {"madre": +0.08, "anima_animus": +0.06, "sombra": -0.05},
    "heroic_act":          {"heroe": +0.10, "self": +0.06, "trickster": -0.05},
    "betrayal":            {"sombra": +0.10, "trickster": +0.06, "madre": -0.08},
    "death_witness":       {"sombra": +0.08, "sabio": +0.06, "nino_divino": -0.08},
}


@dataclass
class ArchetypeVector:
    """
    Vector de 12 pesos arquetípicos (0.0 → 1.0).
    Los pesos NO se normalizan a suma=1 — cada uno es independiente.
    """
    self_:          float = 0.50
    persona:        float = 0.50
    sombra:         float = 0.30
    anima_animus:   float = 0.40
    heroe:          float = 0.50
    sabio:          float = 0.40
    trickster:      float = 0.25
    madre:          float = 0.40
    padre:          float = 0.40
    nino_divino:    float = 0.30
    gobernante:     float = 0.40
    rebelde:        float = 0.30

    def dominant(self) -> str:
        """Arquetipo con mayor peso."""
        vals = self._as_dict()
        return max(vals, key=vals.get)

    def top_n(self, n: int = 3) -> list[tuple[str, float]]:
        vals = self._as_dict()
        return sorted(vals.items(), key=lambda x: -x[1])[:n]

    def action_bias(self, action: str) -> float:
        """
        Suma ponderada de afinidades para la acción dada.
        Devuelve un delta entre -1 y +1.
        """
        affinity = _ACTION_AFFINITY.get(action, {})
        vals = self._as_dict()
        delta = 0.0
        for arch, weight in affinity.items():
            delta += vals.get(arch, 0.0) * weight
        return max(-1.0, min(1.0, delta))

    def update_from_event(self, event_type: str) -> None:
        """Aplica una transformación arquetípica por evento."""
        changes = _TRANSFORMATIONS.get(event_type, {})
        for arch_key, delta in changes.items():
            attr = "self_" if arch_key == "self" else arch_key
            current = getattr(self, attr, 0.0)
            setattr(self, attr, max(0.0, min(1.0, current + delta)))

    def tension(self) -> float:
        """
        Tensión interna: desviación estándar de los pesos.
        Alta tensión → contenido inconsciente presionando hacia superficie.
        """
        vals = list(self._as_dict().values())
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        return variance ** 0.5

    def _as_dict(self) -> dict[str, float]:
        return {
            "self":         self.self_,
            "persona":      self.persona,
            "sombra":       self.sombra,
            "anima_animus": self.anima_animus,
            "heroe":        self.heroe,
            "sabio":        self.sabio,
            "trickster":    self.trickster,
            "madre":        self.madre,
            "padre":        self.padre,
            "nino_divino":  self.nino_divino,
            "gobernante":   self.gobernante,
            "rebelde":      self.rebelde,
        }

    def to_dict(self) -> dict[str, float]:
        return self._as_dict()

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> ArchetypeVector:
        v = cls()
        for key, val in data.items():
            attr = "self_" if key == "self" else key
            if hasattr(v, attr):
                setattr(v, attr, float(val))
        return v
