from __future__ import annotations

import random

from .superposition import BehavioralState, BEHAVIORAL_STATES

# Cuánto peso tienen cada fuente de influencia en el colapso
_WEIGHT_ARCHETYPE  = 0.30
_WEIGHT_COMPLEX    = 0.25
_WEIGHT_TRAIT      = 0.20
_WEIGHT_CONTEXT    = 0.15
_WEIGHT_FIELD      = 0.10


def collapse_state(
    state:            BehavioralState,
    context:          dict,
    archetype_biases: dict[str, float],
    complex_biases:   dict[str, float],
    trait_biases:     dict[str, float],
    field_influence:  dict[str, float] | None = None,
    rng:              random.Random | None    = None,
) -> str:
    """
    Colapsa el vector de superposición en una acción concreta.

    Parámetros:
        state            : BehavioralState actual del agente
        context          : Dict con claves opcionales:
                           "peligro" (float 0-1), "recursos_escasos" (bool),
                           "hay_aliados" (bool), "hay_amenaza" (bool)
        archetype_biases : {acción: delta} de ArchetypeVector.action_bias()
        complex_biases   : {acción: delta} de ComplexProfile.action_bias()
        trait_biases     : {acción: delta} de TraitProfile.action_bias()
        field_influence  : {acción: delta} del CollectiveField (Fase 7)
        rng              : Random opcional para reproducibilidad

    Retorna: str — uno de BEHAVIORAL_STATES
    """
    # Construir vector de probabilidades modificado
    probs = dict(state.probabilities())

    # Aplicar contribuciones ponderadas de cada fuente
    for action in BEHAVIORAL_STATES:
        arch_delta    = archetype_biases.get(action, 0.0) * _WEIGHT_ARCHETYPE
        complex_delta = complex_biases.get(action, 0.0)   * _WEIGHT_COMPLEX
        trait_delta   = trait_biases.get(action, 0.0)     * _WEIGHT_TRAIT
        ctx_delta     = _context_bias(action, context)     * _WEIGHT_CONTEXT
        field_delta   = (field_influence or {}).get(action, 0.0) * _WEIGHT_FIELD

        probs[action] = max(
            0.01,
            probs[action] + arch_delta + complex_delta + trait_delta + ctx_delta + field_delta,
        )

    # Renormalizar
    total = sum(probs.values())
    weights = [probs[a] / total for a in BEHAVIORAL_STATES]

    # Muestreo estocástico
    r = rng or random.Random()
    result = r.choices(list(BEHAVIORAL_STATES), weights=weights, k=1)[0]

    state.ultimo_colapso = result
    return result


def _context_bias(action: str, context: dict) -> float:
    """
    Sesgo contextual puro — independiente de la psicología del agente.
    El contexto lo provee AgentCore desde el WorldSnapshot.
    """
    peligro         = float(context.get("peligro", 0.0))
    recursos_escasos = bool(context.get("recursos_escasos", False))
    hay_aliados     = bool(context.get("hay_aliados", False))
    hay_amenaza     = bool(context.get("hay_amenaza", False))

    if action == "cooperacion":
        bonus = 0.15 if hay_aliados else 0.0
        penalizacion = 0.10 if hay_amenaza else 0.0
        return bonus - penalizacion - peligro * 0.10

    if action == "competencia":
        bonus = 0.15 if recursos_escasos else 0.0
        bonus += 0.10 if hay_amenaza else 0.0
        return bonus

    if action == "aislamiento":
        bonus = 0.20 if peligro > 0.7 else 0.0
        bonus += 0.10 if not hay_aliados else 0.0
        return bonus

    if action == "manipulacion":
        bonus = 0.10 if recursos_escasos and hay_aliados else 0.0
        return bonus

    return 0.0
