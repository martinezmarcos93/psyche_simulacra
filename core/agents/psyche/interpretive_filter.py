"""
InterpretiveFilter — la Ecuación Personal (Fase 1, content-free).

Cada agente transforma un Stimulus *físico* en un PerceivedEvent. El filtro solo
calcula ESCALARES (valence, arousal, relevancia, activación arquetípica). NUNCA
devuelve un símbolo, un juicio moral ni una causa: esos slots nacen vacíos y solo
se rellenan tomando prestado un nombre que YA cristalizó en el campo colectivo.

Principio (02-PSYCHE_ORIGEN_INCONSCIENTE): la *facultad* de interpretar es Capa A
(estructura a priori, legítimo instalarla). El *vocabulario* simbólico es Capa B y
debe emerger. Por eso aquí no hay ningún `if kind == X: return "símbolo"`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from core.interface.perceived_event import PerceivedEvent, Stimulus
from core.social.perception import ARCHETYPE_ATTENTION

if TYPE_CHECKING:
    from core.agents.agent import Agent
    from core.social.collective_field import CollectiveField

# Un símbolo del campo cuenta como "vocabulario disponible" (cristalizado) a partir
# de esta carga. Solo entonces el agente puede tomarlo prestado como narrative_frame.
_VOCAB_THRESHOLD = 0.55

# Mapa inverso de ARCHETYPE_ATTENTION: kind físico → arquetipos que lo atienden.
# Se construye una sola vez. NO asigna significado: solo dice qué arquetipo "mira"
# esa categoría física, igual que ya hace PerceptionSystem.
_ATTENTION_BY_KIND: dict[str, list[str]] = {}
for _arch, _kinds in ARCHETYPE_ATTENTION.items():
    for _k in _kinds:
        _ATTENTION_BY_KIND.setdefault(_k, []).append(_arch)


class AttentionOperator:
    """Cuánta saliencia asigna el agente al estímulo (0..1). Solo escalar."""

    @staticmethod
    def salience(stim: Stimulus, agent: "Agent") -> float:
        base = max(stim.threat, stim.benefit, stim.social) * stim.proximity

        # Amplificación por necesidad: el hambre/sed hace saliente el beneficio.
        if stim.benefit > 0.0:
            need = max(agent.needs.hambre, agent.needs.sed)
            base += stim.benefit * need * 0.5

        # Atención selectiva arquetípica (reutiliza la lógica de PerceptionSystem):
        # si el arquetipo dominante "mira" esta categoría física, amplifica.
        dominante = agent.archetypes.dominant()
        dom_key = "self_" if dominante == "self" else dominante
        if dom_key in _ATTENTION_BY_KIND.get(stim.kind, []):
            base *= 1.5

        # Un complejo activo tensa la atención.
        if agent.complexes.activos:
            base += 0.05

        return max(0.0, min(1.0, base))


class AffectiveOperator:
    """Respuesta afectiva escalar: (valence, arousal). Sin contenido simbólico."""

    @staticmethod
    def appraise(stim: Stimulus, agent: "Agent", salience: float) -> tuple[float, float]:
        # El corazón de la ecuación personal: la MISMA realidad física se aprecia
        # distinto —y hasta con signo opuesto— según la psique. No es un reflejo
        # compartido (eso homogeneizaría); es interpretación idiosincrática.
        t = agent.traits

        # Ganancia idiosincrática de la amenaza: la paranoia/neuroticismo/ansiedad
        # la amplifican; la estabilidad emocional la atenúa. La misma amenaza física
        # duele el doble en una psique frágil que en una serena.
        threat_gain = max(0.2, 1.0 + (t.paranoia + t.neuroticismo + t.ansiedad_rasgo
                                      - t.estabilidad_emocional) * 0.6)
        # Ganancia idiosincrática del beneficio: la apertura/estabilidad lo realzan;
        # el neuroticismo lo empaña (anhedonia).
        benefit_gain = max(0.2, 1.0 + (t.apertura + t.estabilidad_emocional
                                       - t.neuroticismo) * 0.4)

        # La carga social puede leerse como vínculo (+) o como amenaza (−): para el
        # amable/empático el otro es refugio; para el paranoico/agresivo es peligro.
        # Aquí el mismo "otro" significa cosas opuestas en psiques distintas.
        social_val = stim.social * (t.amabilidad + t.empatia
                                    - t.paranoia - t.agresividad - 0.5) * 0.8

        valence = stim.benefit * benefit_gain - stim.threat * threat_gain + social_val

        # La necesidad amplifica la apuesta de supervivencia (hambre/sed).
        need = max(agent.needs.hambre, agent.needs.sed)
        valence += (stim.benefit - stim.threat) * need * 0.3

        valence = max(-1.0, min(1.0, valence))

        # Arousal: la saliencia es la base; la amenaza activa más que el beneficio.
        # Los rasgos ansiosos amplifican la activación.
        arousal = salience * (1.0 + stim.threat * 0.5)
        arousal *= 1.0 + agent.traits.ansiedad_rasgo * 0.5
        arousal = max(0.0, min(1.0, arousal))

        return valence, arousal


class RelevanceOperator:
    """¿Me afecta directamente? (0..1). Solo escalar."""

    @staticmethod
    def relevance(stim: Stimulus, agent: "Agent") -> float:
        rel = stim.proximity * 0.4

        # Toca una necesidad activa → muy relevante.
        if stim.benefit > 0.0:
            rel += max(agent.needs.hambre, agent.needs.sed) * 0.4
        if stim.threat > 0.0:
            rel += stim.threat * 0.4

        # La carga social es relevante para los extravertidos/empáticos.
        rel += stim.social * agent.traits.social_drive() * 0.3

        return max(0.0, min(1.0, rel))


class ResonanceOperator:
    """
    Qué arquetipos se activan ante el estímulo (deltas pequeños). Content-free:
    dice "tu arquetipo X se encendió", no "esto significa X". Usa el ArchetypeVector
    del agente como prior — el mismo estímulo resuena distinto en cada psique.
    """

    @staticmethod
    def activation(stim: Stimulus, agent: "Agent", arousal: float) -> dict[str, float]:
        attending = _ATTENTION_BY_KIND.get(stim.kind, [])
        if not attending:
            return {}

        weights = agent.archetypes.to_dict()
        deltas: dict[str, float] = {}
        for arch in attending:
            key = "self" if arch == "self_" else arch
            prior = weights.get(key, 0.0)
            # Delta acotado: a mayor peso previo y mayor activación, más resuena.
            deltas[key] = round(0.02 * prior * (0.5 + 0.5 * arousal), 4)
        return deltas


class InterpretiveFilter:
    """
    La ecuación personal de un agente. Instanciada por agente (sin estado propio;
    toda la varianza viene de la psique del agente que recibe en cada llamada).
    """

    def __init__(self) -> None:
        self.attention  = AttentionOperator()
        self.affective  = AffectiveOperator()
        self.relevance  = RelevanceOperator()
        self.resonance  = ResonanceOperator()

    def interpret(
        self,
        stim:  Stimulus,
        agent: "Agent",
        field: "CollectiveField | None" = None,
    ) -> PerceivedEvent:
        salience            = self.attention.salience(stim, agent)
        valence, arousal    = self.affective.appraise(stim, agent, salience)
        relevance           = self.relevance.relevance(stim, agent)
        activation          = self.resonance.activation(stim, agent, arousal)

        pe = PerceivedEvent(
            stimulus_type        = stim.kind,
            stimulus_id          = stim.stimulus_id,
            valence              = valence,
            arousal              = arousal,
            relevance_to_self    = relevance,
            archetype_activation = activation,
            raw_stimulus         = dict(stim.raw),
        )

        # Préstamo de vocabulario emergente — NO invención.
        # Si el arquetipo que más resonó coincide con un símbolo que YA cristalizó
        # en el campo (carga ≥ umbral), el agente puede nombrar el frame con él.
        # Si no hay vocabulario, narrative_frame queda None: siente pero no nombra.
        pe.narrative_frame = self._borrow_frame(activation, field)
        return pe

    @staticmethod
    def _borrow_frame(
        activation: dict[str, float],
        field: "CollectiveField | None",
    ) -> str | None:
        if field is None or not activation:
            return None
        top_arch = max(activation, key=activation.get)
        charge = field.symbols.get(top_arch, 0.0)
        if charge >= _VOCAB_THRESHOLD:
            return top_arch    # el nombre del símbolo cristalizado, prestado
        return None
