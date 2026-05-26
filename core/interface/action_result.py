from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ActionResult:
    """
    La respuesta del mundo a una acción de un agente.
    El agente actualiza su estado interno basándose en este resultado.
    """
    agent_id:    str
    action_type: str
    success:     bool

    # Si tuvo éxito: recursos obtenidos
    # {"carne": 0.3, "cuero": 0.1, "huesos": 0.05}
    resource_gained: dict | None = None

    # Si falló: razón del fallo
    # "fauna_insuficiente" / "terreno_inaccesible" / "sin_tecnologia"
    failure_reason: str | None = None

    # Efectos en el mundo, siempre presentes (éxito o fallo)
    # {"fauna_density": -0.02, "noise_level": +0.1}
    world_effects: dict = field(default_factory=dict)

    # Información nueva descubierta durante la acción
    # [{"tipo": "recurso_oculto", "recurso": "miel", "coord": (41, 30)}]
    discoveries: list = field(default_factory=list)

    # Destino posicional autorizado para acciones de movimiento o exploración
    coord_dest: tuple[int, int] | None = None

