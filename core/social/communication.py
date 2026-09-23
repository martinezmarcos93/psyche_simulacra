"""
Reinterpretación del receptor en el encuentro social.

Cada agente que participa de un encuentro reinterpreta lo ocurrido a través de
su propia Ecuación Personal (InterpretiveFilter, Fase 1): el mismo intercambio
objetivo, resuelto por InteractionEngine.resolve_encounter, puede sentirse
distinto según el conocimiento (asociaciones causales del propio agente),
los intereses (vínculo previo con el otro) y las inclinaciones (arquetipos,
complejos, rasgos) de quien lo recibe.

Principio Capa A / Capa B (src/02-PSYCHE_ORIGEN_INCONSCIENTE.md): este módulo
NO extiende InterpretiveFilter ni inventa contenido simbólico — solo traduce
el rol que tuvo un agente en un encuentro a un Stimulus físico (categoría +
magnitudes, sin significado) y deja que el filtro ya existente haga su trabajo.
El vocabulario simbólico que la reinterpretación pueda tomar prestado
(narrative_frame/attributed_cause/moral_judgment) sigue naciendo vacío salvo
que ya haya cristalizado en el campo que se le pase — de ahí que quien llama
a `reinterpret_encounter` deba pasar el campo/mitología LOCAL del receptor
(su propia tribu) y no necesariamente el global: la misma interacción puede
cristalizar distinto vocabulario, o ningún vocabulario, según qué tribu la
vive (multiacentualidad — Voloshinov).
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from core.interface.perceived_event import PerceivedEvent, Stimulus

if TYPE_CHECKING:
    from core.agents.agent import Agent
    from core.social.network import SocialNetwork
    from core.social.collective_field import CollectiveField
    from core.social.mythology import MythologyEngine

# Off por defecto — preserva la reproducibilidad de corridas existentes.
# Mismo patrón que _INTERPRETIVE_FILTER_ENABLED en agent.py. Requiere además
# que el agente tenga su propio filtro activado (Agent.perceive_social_event
# devuelve None si no lo tiene).
REINTERPRETATION_ENABLED = (
    os.environ.get("COMM_REINTERPRETATION_ENABLED", "0").strip() not in ("0", "false", "no")
)

# Rol que tuvo el receptor en el encuentro -> categoría física del estímulo
# (kind). Se reutiliza vocabulario ya existente en ARCHETYPE_ATTENTION
# (core/social/perception.py) donde encaja semánticamente, en vez de inventar
# categorías nuevas sin necesidad.
_ROLE_KIND: dict[str, str] = {
    "cooperacion_mutua":       "cooperacion_mutua",
    "explotado":               "traicion",              # ya existe: atención de sombra
    "explotador":               "explotacion_exitosa",
    "choque_violento":         "choque_violento",        # ya existe: atención de heroe
    "manipulado_exitosamente": "engano",                 # ya existe: atención de trickster
    "manipulador_exitoso":     "manipulacion_lograda",
    "manipulador_fracasado":   "engano",
    "manipulacion_resistida":  "engano",
    "juego_mental_mutuo":      "engano",
}

# Rol -> (threat, benefit) físicos base. Magnitudes proporcionales a los
# efectos "objetivos" que InteractionEngine.resolve_encounter ya aplica a
# cada agente según su rol en esa misma rama (ver docstring del módulo:
# la víctima de una explotación y quien explota viven el MISMO evento
# objetivo con polaridad física opuesta — eso es lo que hace posible que la
# reinterpretación diverja).
_ROLE_PHYSICS: dict[str, tuple[float, float]] = {
    "cooperacion_mutua":       (0.00, 0.50),
    "explotado":               (0.50, 0.00),
    "explotador":               (0.00, 0.30),
    "choque_violento":         (0.70, 0.00),
    "manipulado_exitosamente": (0.15, 0.25),
    "manipulador_exitoso":     (0.00, 0.40),
    "manipulador_fracasado":   (0.30, 0.00),
    "manipulacion_resistida":  (0.25, 0.10),
    "juego_mental_mutuo":      (0.20, 0.00),
}


def build_encounter_stimulus(
    role:        str,
    other:       "Agent",
    network:     "SocialNetwork",
    receiver_id: str,
) -> Stimulus:
    """
    Construye el estímulo físico de un encuentro para quien lo recibe.

    El vínculo previo con el otro agente (bond_strength, positivo o negativo)
    se traduce en `social` como magnitud de cuánto importa el otro —no como
    contenido oculto: es la misma semántica que ya usa Stimulus.social para
    cualquier estímulo con carga social.
    """
    kind = _ROLE_KIND.get(role, role)
    threat, benefit = _ROLE_PHYSICS.get(role, (0.0, 0.0))
    bond = network.get_bond(receiver_id, other.id)
    social = min(1.0, abs(bond) * 0.6 + 0.3)
    return Stimulus(
        kind=kind,
        stimulus_id=f"encuentro_{other.id}",
        threat=threat,
        benefit=benefit,
        social=social,
        proximity=1.0,
        raw={"role": role, "other_id": other.id, "bond": bond},
    )


def reinterpret_encounter(
    receiver:         "Agent",
    other:            "Agent",
    role:             str,
    network:          "SocialNetwork",
    field:            "CollectiveField | None",
    mythology_engine: "MythologyEngine | None",
) -> PerceivedEvent | None:
    """
    El receptor reinterpreta el encuentro a través de su propia Ecuación
    Personal. `field`/`mythology_engine` deben ser los del receptor (locales
    a su tribu si corresponde) — quien llama decide esa resolución.

    Devuelve None si el filtro interpretativo está desactivado en este
    agente; en ese caso no hay efecto alguno (mismo criterio que el resto
    de la Fase 1: apagado por defecto, sin alterar corridas existentes).
    """
    stim = build_encounter_stimulus(role, other, network, receiver.id)
    pe = receiver.perceive_social_event(stim, field, mythology_engine)
    if pe is not None:
        receiver.complexes.check_activation([stim.kind])
    return pe
