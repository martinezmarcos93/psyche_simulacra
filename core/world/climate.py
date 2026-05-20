from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from core.time import TimePoint


# Parámetros base por estación
ESTACIONES: dict[str, dict] = {
    "primavera": {
        "temperatura":      (8.0, 20.0),
        "precipitacion":    0.55,
        "luminosidad_dia":  0.80,
        "viento_base":      0.30,
    },
    "verano": {
        "temperatura":      (18.0, 35.0),
        "precipitacion":    0.30,
        "luminosidad_dia":  0.95,
        "viento_base":      0.20,
    },
    "otoño": {
        "temperatura":      (5.0, 18.0),
        "precipitacion":    0.65,
        "luminosidad_dia":  0.70,
        "viento_base":      0.45,
    },
    "invierno": {
        "temperatura":      (-5.0, 8.0),
        "precipitacion":    0.45,
        "luminosidad_dia":  0.55,
        "viento_base":      0.55,
    },
}

# Probabilidad de cada evento por estación
_EVENTOS        = ["tormenta", "helada", "sequia"]
_PROB_EVENTOS: dict[str, list[float]] = {
    "primavera": [0.50, 0.30, 0.20],
    "verano":    [0.30, 0.00, 0.70],
    "otoño":     [0.60, 0.20, 0.20],
    "invierno":  [0.30, 0.70, 0.00],
}


@dataclass(frozen=True)
class ClimateState:
    temperatura:      float
    precipitacion:    float
    luminosidad:      float
    viento:           float
    humedad:          float
    estacion:         str
    evento_activo:    str | None
    mood_modifier:    float        # efecto en humor base de los agentes
    productivity_mod: float        # efecto en productividad
    survival_risk:    float        # riesgo climático (0=nulo, 1=letal)


class ClimateSystem:
    """
    Sistema climático autónomo y determinista.
    Funciona sin agentes. Mismos parámetros = mismo resultado.
    """

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)

        self.temperatura:   float    = 16.0
        self.precipitacion: float    = 0.45
        self.luminosidad:   float    = 0.70
        self.viento:        float    = 0.30
        self.humedad:       float    = 0.55

        # Tendencias con decay — el clima cambia suavemente, no en saltos
        self._tend_temp:   float = 0.0
        self._tend_lluvia: float = 0.0

        self.evento_activo:   str | None = None
        self.evento_duracion: int        = 0

    def update(self, tp: TimePoint) -> ClimateState:
        base = ESTACIONES[tp.estacion]
        temp_min, temp_max = base["temperatura"]

        # Ciclo diario: más frío de madrugada, pico al mediodía
        ciclo = float(np.sin((tp.hora_del_dia - 6) * np.pi / 12))
        temp_base = temp_min + (temp_max - temp_min) * (ciclo * 0.5 + 0.5)

        self._tend_temp  += float(self.rng.normal(0, 0.4))
        self._tend_temp  *= 0.92
        self.temperatura  = float(np.clip(
            temp_base + self._tend_temp, temp_min - 8.0, temp_max + 8.0
        ))

        # Precipitación
        prob_base = base["precipitacion"]
        if self.evento_activo == "tormenta":
            prob_base = min(1.0, prob_base * 2.5)
        elif self.evento_activo == "sequia":
            prob_base = max(0.0, prob_base * 0.2)
        self._tend_lluvia += float(self.rng.normal(0, 0.06))
        self._tend_lluvia *= 0.88
        self.precipitacion = float(np.clip(
            prob_base + self._tend_lluvia, 0.0, 1.0
        ))

        # Luminosidad (noche casi nula; día reducida por lluvia)
        if tp.es_dia:
            self.luminosidad = float(np.clip(
                base["luminosidad_dia"] - self.precipitacion * 0.55, 0.05, 1.0
            ))
        else:
            self.luminosidad = 0.05

        # Viento
        self.viento = float(np.clip(
            base["viento_base"] + float(self.rng.normal(0, 0.08)), 0.0, 1.0
        ))

        # Humedad
        self.humedad = float(np.clip(
            0.50 + self.precipitacion * 0.40 + float(self.rng.normal(0, 0.04)),
            0.0, 1.0,
        ))

        # Eventos climáticos
        self._update_weather_event(tp.estacion)

        return ClimateState(
            temperatura      = self.temperatura,
            precipitacion    = self.precipitacion,
            luminosidad      = self.luminosidad,
            viento           = self.viento,
            humedad          = self.humedad,
            estacion         = tp.estacion,
            evento_activo    = self.evento_activo,
            mood_modifier    = self._mood_modifier(),
            productivity_mod = self._productivity_modifier(),
            survival_risk    = self._survival_risk(),
        )

    def _update_weather_event(self, estacion: str) -> None:
        if self.evento_activo:
            self.evento_duracion -= 1
            if self.evento_duracion <= 0:
                self.evento_activo = None
        elif float(self.rng.random()) < 0.002:  # ~2 eventos/año
            probs = _PROB_EVENTOS[estacion]
            self.evento_activo   = str(self.rng.choice(_EVENTOS, p=probs))
            self.evento_duracion = int(self.rng.integers(24, 96))

    def _mood_modifier(self) -> float:
        mod = 0.0
        if 15.0 <= self.temperatura <= 22.0:
            mod += 0.15
        elif self.temperatura < 0.0 or self.temperatura > 38.0:
            mod -= 0.30
        elif self.temperatura < 5.0 or self.temperatura > 33.0:
            mod -= 0.15
        if self.precipitacion > 0.70:
            mod -= 0.20
        elif 0.20 < self.precipitacion < 0.50:
            mod += 0.05
        mod += (self.luminosidad - 0.50) * 0.20
        if self.evento_activo:
            mod -= 0.10
        return float(np.clip(mod, -0.50, 0.30))

    def _productivity_modifier(self) -> float:
        mod = 0.0
        if 10.0 <= self.temperatura <= 28.0:
            mod += 0.10
        elif self.temperatura < -5.0 or self.temperatura > 40.0:
            mod -= 0.40
        if self.precipitacion > 0.80:
            mod -= 0.30
        if self.evento_activo in ("tormenta", "helada"):
            mod -= 0.50
        elif self.evento_activo == "sequia":
            mod -= 0.20
        return float(np.clip(mod, -0.80, 0.20))

    def _survival_risk(self) -> float:
        risk = 0.0
        if self.temperatura < -5.0:
            risk += (abs(self.temperatura) - 5.0) * 0.03
        elif self.temperatura > 42.0:
            risk += (self.temperatura - 42.0) * 0.04
        if self.evento_activo == "tormenta":
            risk += 0.08
        elif self.evento_activo == "helada":
            risk += 0.20
        return float(np.clip(risk, 0.0, 1.0))
