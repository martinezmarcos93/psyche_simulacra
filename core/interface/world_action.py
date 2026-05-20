from __future__ import annotations

from dataclasses import dataclass, field


class ActionType:
    # Recursos
    CAZAR             = "cazar"
    RECOLECTAR        = "recolectar"
    PESCAR            = "pescar"
    BEBER             = "beber"

    # Exploración y movimiento
    EXPLORAR          = "explorar"
    MOVERSE           = "moverse"
    CRUZAR_RIO        = "cruzar_rio"

    # Construcción
    CONSTRUIR_REFUGIO = "construir_refugio"
    MANTENER_FUEGO    = "mantener_fuego"

    # Tecnología
    ENCENDER_FUEGO    = "encender_fuego"
    TALLAR_PIEDRA     = "tallar_piedra"
    USAR_TECNOLOGIA   = "usar_tecnologia"

    # Recursos ocultos
    BUSCAR_RECURSO    = "buscar_recurso"


@dataclass
class WorldAction:
    """
    Todo lo que un agente puede hacer al mundo físico.
    El Núcleo 1 decide si es posible y qué efecto tiene.
    Los agentes no modifican el mundo directamente — solo emiten acciones.
    """
    agent_id:  str
    tick:      int
    type:      str               # Ver ActionType
    coord:     tuple[int, int]   # Hex (q, r) donde ocurre la acción

    # Parámetros específicos por tipo de acción
    params:    dict              = field(default_factory=dict)

    # Si dos agentes compiten por el mismo recurso, gana el de mayor prioridad
    priority:  float             = 0.5
