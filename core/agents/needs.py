from __future__ import annotations

from dataclasses import dataclass, field

# Decay per tick while awake
_HAMBRE_DECAY_WAKING  = 0.020
_FATIGA_DECAY_WAKING  = 0.035
_SED_DECAY_WAKING     = 0.040

# Decay per tick while sleeping
_HAMBRE_DECAY_SLEEPING = 0.008
_FATIGA_RECOVER_SLEEP  = 0.075  # fatigue goes DOWN while sleeping
_SED_DECAY_SLEEPING    = 0.005

OVERRIDE_THRESHOLD = 0.80   # need is critical — overrides schedule
CRITICAL_THRESHOLD = 0.95   # need is life-threatening


@dataclass
class Needs:
    hambre:      float = 0.0   # 0=full, 1=starving
    fatiga:      float = 0.0   # 0=rested, 1=exhausted
    sed:         float = 0.0   # 0=hydrated, 1=dehydrated
    sociabilidad: float = 0.5  # 0=satiated, 1=isolated

    def update_waking(self, need_factor: float = 1.0) -> None:
        self.hambre      = min(1.0, self.hambre      + _HAMBRE_DECAY_WAKING  * need_factor)
        self.fatiga      = min(1.0, self.fatiga      + _FATIGA_DECAY_WAKING  * need_factor)
        self.sed         = min(1.0, self.sed         + _SED_DECAY_WAKING     * need_factor)
        self.sociabilidad = min(1.0, self.sociabilidad + 0.010)

    def update_sleeping(self, need_factor: float = 1.0) -> None:
        self.hambre      = min(1.0, self.hambre      + _HAMBRE_DECAY_SLEEPING * need_factor)
        self.fatiga      = max(0.0, self.fatiga      - _FATIGA_RECOVER_SLEEP)
        self.sed         = min(1.0, self.sed         + _SED_DECAY_SLEEPING    * need_factor)

    def eat(self, amount: float) -> None:
        self.hambre = max(0.0, self.hambre - amount)

    def drink(self, amount: float) -> None:
        self.sed = max(0.0, self.sed - amount)

    def socialize(self) -> None:
        self.sociabilidad = max(0.0, self.sociabilidad - 0.30)

    def survival_override_active(self) -> bool:
        return (
            self.hambre  >= OVERRIDE_THRESHOLD or
            self.sed     >= OVERRIDE_THRESHOLD or
            self.fatiga  >= OVERRIDE_THRESHOLD
        )

    def social_override_active(self) -> bool:
        """El aislamiento es tan alto que el agente priorizará interacción social."""
        return self.sociabilidad >= OVERRIDE_THRESHOLD

    def most_critical_need(self) -> str:
        """Returns the name of the most pressing need at or above override threshold."""
        candidates = {
            "sed":    self.sed,
            "hambre": self.hambre,
            "fatiga": self.fatiga,
        }
        worst = max(candidates, key=lambda k: candidates[k])
        if candidates[worst] >= OVERRIDE_THRESHOLD:
            return worst
        return "ninguna"

    @property
    def stress_level(self) -> float:
        return (self.hambre * 0.35 + self.sed * 0.40 + self.fatiga * 0.25)

    def to_dict(self) -> dict:
        return {
            "hambre":      self.hambre,
            "fatiga":      self.fatiga,
            "sed":         self.sed,
            "sociabilidad": self.sociabilidad,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Needs:
        return cls(
            hambre=data.get("hambre", 0.0),
            fatiga=data.get("fatiga", 0.0),
            sed=data.get("sed", 0.0),
            sociabilidad=data.get("sociabilidad", 0.5),
        )
