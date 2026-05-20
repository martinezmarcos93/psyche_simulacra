from __future__ import annotations

from dataclasses import dataclass, field

# Umbrales de activación
_ACTIVATION_THRESHOLD = 0.65  # el peso del complejo debe superar esto
_DECAY_PER_TICK       = 0.008  # decaimiento por tick cuando está activo
_DECAY_PER_DAY        = 0.025  # decaimiento adicional por día

# Triggers contextuales por defecto
_DEFAULT_TRIGGERS: dict[str, list[str]] = {
    "abandono":       ["muerte", "separacion", "rechazo", "perdida"],
    "inferioridad":   ["fracaso", "humillacion", "comparacion", "critica"],
    "poder":          ["amenaza_status", "competencia", "victoria", "derrota"],
    "culpa":          ["traicion", "fracaso_social", "violacion_norma", "daño_otro"],
    "materno":        ["cuidado", "crianza", "dependencia", "figura_materna"],
    "trascendencia":  ["muerte_cercana", "ritual", "vision", "crisis_existencial"],
}

# Cómo afecta cada complejo activo a las acciones cuánticas
_COMPLEX_ACTION_BIAS: dict[str, dict[str, float]] = {
    "abandono":      {"aislamiento": +0.20, "manipulacion": +0.10, "cooperacion": -0.15},
    "inferioridad":  {"aislamiento": +0.15, "competencia": +0.10, "cooperacion": -0.10},
    "poder":         {"competencia": +0.20, "manipulacion": +0.15, "cooperacion": -0.10},
    "culpa":         {"aislamiento": +0.10, "cooperacion": +0.10, "manipulacion": -0.15},
    "materno":       {"cooperacion": +0.20, "aislamiento": -0.15, "competencia": -0.10},
    "trascendencia": {"aislamiento": +0.15, "cooperacion": +0.10, "manipulacion": -0.10},
}


@dataclass
class ComplexProfile:
    """
    Seis complejos jungianos con pesos de intensidad (0.0 → 1.0).
    Cada complejo puede estar activo o inactivo; cuando está activo,
    modifica el vector de acción y decae gradualmente.
    """
    abandono:      float = 0.30
    inferioridad:  float = 0.30
    poder:         float = 0.30
    culpa:         float = 0.30
    materno:       float = 0.30
    trascendencia: float = 0.30

    # Cuáles están actualmente activos (nombre → intensidad residual)
    activos: dict[str, float] = field(default_factory=dict)

    # Triggers personalizados (se mezclan con los por defecto)
    custom_triggers: dict[str, list[str]] = field(default_factory=dict)

    def triggers_for(self, complejo: str) -> list[str]:
        base = _DEFAULT_TRIGGERS.get(complejo, [])
        custom = self.custom_triggers.get(complejo, [])
        return base + custom

    def check_activation(self, context_events: list[str]) -> list[str]:
        """
        Dado un contexto de eventos, activa los complejos cuyo peso
        supere el umbral Y que tengan un trigger en el contexto.
        Devuelve lista de complejos recién activados.
        """
        newly_activated: list[str] = []
        for nombre in self._nombres():
            peso = getattr(self, nombre)
            if peso < _ACTIVATION_THRESHOLD:
                continue
            triggers = self.triggers_for(nombre)
            for event in context_events:
                if event in triggers:
                    if nombre not in self.activos:
                        self.activos[nombre] = peso
                        newly_activated.append(nombre)
                    break
        return newly_activated

    def activate(self, complejo: str) -> None:
        """Activa un complejo directamente (ej: desde DreamEngine)."""
        peso = getattr(self, complejo, 0.0)
        self.activos[complejo] = max(self.activos.get(complejo, 0.0), peso)

    def action_bias(self, action: str) -> float:
        """
        Suma de modificadores de todos los complejos activos para una acción.
        Devuelve delta entre -1 y +1.
        """
        total = 0.0
        for nombre, intensidad in self.activos.items():
            bias_map = _COMPLEX_ACTION_BIAS.get(nombre, {})
            total += bias_map.get(action, 0.0) * intensidad
        return max(-1.0, min(1.0, total))

    def decay_tick(self) -> None:
        """Decaimiento por tick de los complejos activos."""
        agotados = []
        for nombre in list(self.activos):
            self.activos[nombre] = max(0.0, self.activos[nombre] - _DECAY_PER_TICK)
            if self.activos[nombre] <= 0.0:
                agotados.append(nombre)
        for nombre in agotados:
            del self.activos[nombre]

    def decay_day(self) -> None:
        """Decaimiento adicional al final de cada día."""
        agotados = []
        for nombre in list(self.activos):
            self.activos[nombre] = max(0.0, self.activos[nombre] - _DECAY_PER_DAY)
            if self.activos[nombre] <= 0.0:
                agotados.append(nombre)
        for nombre in agotados:
            del self.activos[nombre]

    def most_active(self) -> str | None:
        """Complejo con mayor intensidad activa, o None si ninguno activo."""
        if not self.activos:
            return None
        return max(self.activos, key=self.activos.get)

    def _nombres(self) -> list[str]:
        return ["abandono", "inferioridad", "poder", "culpa", "materno", "trascendencia"]

    def to_dict(self) -> dict:
        return {
            "abandono":      self.abandono,
            "inferioridad":  self.inferioridad,
            "poder":         self.poder,
            "culpa":         self.culpa,
            "materno":       self.materno,
            "trascendencia": self.trascendencia,
            "activos":       dict(self.activos),
            "custom_triggers": dict(self.custom_triggers),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ComplexProfile:
        cp = cls()
        for nombre in ["abandono", "inferioridad", "poder", "culpa", "materno", "trascendencia"]:
            if nombre in data:
                setattr(cp, nombre, float(data[nombre]))
        cp.activos = dict(data.get("activos", {}))
        cp.custom_triggers = dict(data.get("custom_triggers", {}))
        return cp
