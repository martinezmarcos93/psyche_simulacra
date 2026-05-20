from __future__ import annotations

import random
from dataclasses import dataclass, field

# Tabla de símbolos: (arquetipo_dominante, complejo_activo) → símbolo onírico
_SYMBOL_TABLE: dict[tuple[str, str | None], str] = {
    ("heroe",       "poder"):         "espada_rota",
    ("heroe",       "abandono"):      "camino_sin_fin",
    ("heroe",       None):            "montaña",
    ("sombra",      "culpa"):         "cueva_oscura",
    ("sombra",      "abandono"):      "espejo_partido",
    ("sombra",      None):            "figura_oscura",
    ("madre",       "materno"):       "árbol_raíces",
    ("madre",       "abandono"):      "nido_vacio",
    ("madre",       None):            "rio_quieto",
    ("sabio",       "trascendencia"): "libro_sin_palabras",
    ("sabio",       None):            "estrella_lejana",
    ("trickster",   "poder"):         "laberinto",
    ("trickster",   None):            "puerta_falsa",
    ("gobernante",  "poder"):         "trono_caido",
    ("gobernante",  None):            "ciudad_en_ruinas",
    ("rebelde",     "inferioridad"):  "muro_que_cae",
    ("rebelde",     None):            "fuego_libre",
    ("nino_divino", "abandono"):      "cuna_vacia",
    ("nino_divino", None):            "luz_primera",
    ("padre",       "culpa"):         "ley_escrita_en_piedra",
    ("padre",       None):            "tormenta_que_pasa",
    ("anima_animus", "trascendencia"):"reflejo_en_agua",
    ("anima_animus", None):           "voz_sin_cuerpo",
    ("persona",     "inferioridad"):  "máscara_que_no_encaja",
    ("persona",     None):            "escenario_vacio",
    ("self",        "trascendencia"): "mandala",
    ("self",        None):            "centro_del_mundo",
}

_DEFAULT_SYMBOL = "sombra_sin_forma"

# Tipos de procesamiento onírico
_PROCESSING_TYPES = ["integracion_parcial", "amplificacion", "compensacion", "proyeccion"]

# Qué proceso aplica según la tensión interna
def _select_processing(tension: float, rng: random.Random) -> str:
    if tension > 0.25:
        return rng.choice(["amplificacion", "proyeccion"])
    if tension > 0.15:
        return rng.choice(["integracion_parcial", "compensacion"])
    return "integracion_parcial"


@dataclass
class Dream:
    """Resultado de un ciclo de sueño."""
    dia:            int
    simbolo:        str
    arquetipo:      str
    complejo:       str | None
    procesamiento:  str
    insight:        str
    delta_arquetipo: dict[str, float]  # cambios aplicados tras el sueño


@dataclass
class DreamEngine:
    """
    Procesa el sueño nocturno de un agente.
    Opera una vez por noche (hora 22-23 del día simulado).
    """

    def generate_dream(
        self,
        dia:           int,
        dominante:     str,      # arquetipo dominante del agente
        tension:       float,    # tensión interna del vector arquetípico
        complejo_activo: str | None,
        rng:           random.Random | None = None,
    ) -> Dream:
        r = rng or random.Random()

        simbolo = self._select_symbol(dominante, complejo_activo, r)
        procesamiento = _select_processing(tension, r)
        insight = self._generate_insight(dominante, complejo_activo, procesamiento)
        delta = self._compute_delta(dominante, complejo_activo, procesamiento, r)

        return Dream(
            dia             = dia,
            simbolo         = simbolo,
            arquetipo       = dominante,
            complejo        = complejo_activo,
            procesamiento   = procesamiento,
            insight         = insight,
            delta_arquetipo = delta,
        )

    def _select_symbol(
        self,
        dominante:       str,
        complejo_activo: str | None,
        rng:             random.Random,
    ) -> str:
        # Buscar primero la combinación exacta, luego solo arquetipo
        key_specific = (dominante, complejo_activo)
        key_generic  = (dominante, None)
        if key_specific in _SYMBOL_TABLE:
            return _SYMBOL_TABLE[key_specific]
        if key_generic in _SYMBOL_TABLE:
            return _SYMBOL_TABLE[key_generic]
        return _DEFAULT_SYMBOL

    def _generate_insight(
        self,
        dominante:       str,
        complejo_activo: str | None,
        procesamiento:   str,
    ) -> str:
        if procesamiento == "integracion_parcial":
            return f"El {dominante} encuentra paz provisional con {complejo_activo or 'la oscuridad'}."
        if procesamiento == "amplificacion":
            return f"La tensión del {dominante} se intensifica; {complejo_activo or 'algo'} presiona desde abajo."
        if procesamiento == "compensacion":
            return f"El {dominante} compensa la energía de {complejo_activo or 'lo reprimido'}."
        return f"El {dominante} proyecta {complejo_activo or 'su sombra'} hacia afuera."

    def _compute_delta(
        self,
        dominante:       str,
        complejo_activo: str | None,
        procesamiento:   str,
        rng:             random.Random,
    ) -> dict[str, float]:
        """
        Pequeños cambios arquetípicos derivados del procesamiento onírico.
        La integración refuerza el self; la amplificación refuerza el arquetipo dominante;
        la compensación refuerza el opuesto; la proyección refuerza la sombra.
        """
        delta: dict[str, float] = {}
        magnitude = rng.uniform(0.02, 0.06)

        if procesamiento == "integracion_parcial":
            delta["self"] = +magnitude
            if complejo_activo:
                delta[dominante] = -magnitude * 0.5
        elif procesamiento == "amplificacion":
            delta[dominante] = +magnitude
        elif procesamiento == "compensacion":
            opuesto = _ARCHETYPE_OPPOSITES.get(dominante, "sombra")
            delta[opuesto] = +magnitude * 0.7
            delta[dominante] = -magnitude * 0.3
        else:  # proyeccion
            delta["sombra"] = +magnitude * 0.8
            delta[dominante] = -magnitude * 0.4

        return delta


# Pares opuestos arquetípicos para compensación
_ARCHETYPE_OPPOSITES: dict[str, str] = {
    "heroe":        "sombra",
    "sombra":       "heroe",
    "madre":        "padre",
    "padre":        "madre",
    "gobernante":   "rebelde",
    "rebelde":      "gobernante",
    "persona":      "sombra",
    "sabio":        "nino_divino",
    "nino_divino":  "sabio",
    "trickster":    "persona",
    "anima_animus": "self",
    "self":         "anima_animus",
}
