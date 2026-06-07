from __future__ import annotations

from dataclasses import dataclass, field

# Las 4 acciones del colapso conductual (espejo de BEHAVIORAL_STATES)
_ACTIONS = ("cooperacion", "competencia", "aislamiento", "manipulacion")


@dataclass
class Stimulus:
    """
    Un estímulo *físico* que el agente puede percibir. NO lleva significado:
    solo categorías y magnitudes físicas. El significado (si lo hay) lo construye
    el InterpretiveFilter como respuesta afectiva escalar, y el *nombre* simbólico
    solo se toma prestado del vocabulario que ya cristalizó en el colectivo.

    kind      : categoría física, no juicio ("amenaza", "recurso", "agente",
                "estructura", "muerte", "clima", "neutro")
    threat    : 0..1 — peligro físico inmediato del estímulo
    benefit   : 0..1 — beneficio potencial (recurso, ayuda) relativo a la necesidad
    social    : 0..1 — carga social (presencia de otros, relevancia relacional)
    proximity : 0..1 — 1.0 = aquí mismo, 0.0 = en el límite perceptivo
    """
    kind:        str
    stimulus_id: str = "?"
    threat:      float = 0.0
    benefit:     float = 0.0
    social:      float = 0.0
    proximity:   float = 1.0
    raw:         dict = field(default_factory=dict)


@dataclass
class PerceivedEvent:
    """
    El estímulo ya pasado por la ecuación personal del agente.

    Capa A (escalares que el filtro SÍ calcula — estructura, no contenido):
        valence, arousal, relevance_to_self, archetype_activation.

    Capa B (SLOTS VACÍOS): attributed_cause, moral_judgment, narrative_frame.
        Nacen None. Solo se rellenan por *referencia* a un símbolo que ya
        cristalizó en el campo colectivo — nunca por un enum del diseñador.
        Si la cultura aún no tiene la palabra, el agente siente pero no nombra.
    """
    # ── Identidad del estímulo ───────────────────────────────────────────────
    stimulus_type: str
    stimulus_id:   str

    # ── Capa A — respuesta afectiva escalar ──────────────────────────────────
    valence:              float                 # -1.0 (muy negativo) → +1.0 (muy positivo)
    arousal:              float                 # 0.0 → 1.0 (intensidad emocional)
    relevance_to_self:    float                 # 0.0 → 1.0 (¿me afecta?)
    archetype_activation: dict = field(default_factory=dict)  # {arquetipo: delta}

    # ── Capa B — slots vacíos (emergen, no se programan) ─────────────────────
    attributed_cause: str | None = None
    moral_judgment:   str | None = None
    narrative_frame:  str | None = None

    raw_stimulus: dict = field(default_factory=dict)

    def intensity(self) -> float:
        """Cuánto 'pesa' este evento: intensidad emocional ponderada por relevancia."""
        return self.arousal * (0.5 + 0.5 * self.relevance_to_self)

    def action_bias(self) -> dict[str, float]:
        """
        Convierte los escalares de Capa A en deltas para las 4 acciones del colapso.

        Espejo conceptual de CollectiveField.radiate(): NINGÚN contenido simbólico
        participa. Solo valence/arousal/relevance, con una lógica psicofisiológica
        content-free:

          - valence positiva  → impulso a cooperar (afiliación).
          - valence negativa + arousal ALTO → competir (respuesta de lucha).
          - valence negativa + arousal BAJO → aislarse (respuesta de retirada).
          - manipulación NO se induce afectivamente; queda a rasgos/complejos.

        La relevancia amplifica todo el efecto.
        """
        pos = max(0.0, self.valence)
        neg = max(0.0, -self.valence)
        rel = 0.5 + 0.5 * self.relevance_to_self    # 0.5 .. 1.0

        cooperacion  = pos * (0.5 + 0.5 * self.arousal) * rel
        competencia  = neg * self.arousal             * rel    # lucha (arousal alto)
        aislamiento  = neg * (1.0 - self.arousal)     * rel    # retirada (arousal bajo)
        manipulacion = 0.0

        return {
            "cooperacion":  cooperacion,
            "competencia":  competencia,
            "aislamiento":  aislamiento,
            "manipulacion": manipulacion,
        }

    def to_dict(self) -> dict:
        return {
            "stimulus_type":        self.stimulus_type,
            "stimulus_id":          self.stimulus_id,
            "valence":              self.valence,
            "arousal":              self.arousal,
            "relevance_to_self":    self.relevance_to_self,
            "archetype_activation": dict(self.archetype_activation),
            "attributed_cause":     self.attributed_cause,
            "moral_judgment":       self.moral_judgment,
            "narrative_frame":      self.narrative_frame,
        }
