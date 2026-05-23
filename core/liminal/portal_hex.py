"""
core/liminal/portal_hex.py — Hexágono portal hacia la Zona Liminal.

La posición es determinista: se calcula a partir del seed de la simulación.
Siempre está a ~18 hexágonos del centro (spawn), por lo que los agentes
deben explorar el mapa para encontrarlo.
"""

from __future__ import annotations

import math


# Mapa de PSYCHE SIMULACRA: 80×60, spawn en (40, 30)
_MAP_W = 80
_MAP_H = 60
_CENTER = (40, 30)


def compute_portal_position(seed: int) -> tuple[int, int]:
    """
    Calcula la posición del portal basándose en el seed de la simulación.
    El portal queda en una corona de radio 15-20 alrededor del spawn central.
    """
    cx, cy = _CENTER
    # El ángulo varía suavemente con el seed
    angle_deg = (seed * 137.5) % 360   # golden-angle spread para distribución uniforme
    radius_q  = 18
    radius_r  = 12   # mapa más ancho que alto

    q = int(cx + radius_q * math.cos(math.radians(angle_deg)))
    r = int(cy + radius_r * math.sin(math.radians(angle_deg)))

    # Clamp dentro del mapa (con margen de 2 del borde)
    q = max(2, min(_MAP_W - 3, q))
    r = max(2, min(_MAP_H - 3, r))

    return (q, r)


class PortalHex:
    """
    Representa el hexágono portal en el mapa de PSYCHE SIMULACRA.
    El portal detecta cuando un agente lo pisa y dispara la transferencia.
    """

    BIOME_LABEL = "portal"   # Biome visual especial para el renderer

    def __init__(self, seed: int) -> None:
        self.pos: tuple[int, int] = compute_portal_position(seed)
        self._activated: bool = False

    @property
    def q(self) -> int:
        return self.pos[0]

    @property
    def r(self) -> int:
        return self.pos[1]

    def agent_at_portal(self, agent) -> bool:
        """Retorna True si el agente está parado exactamente sobre el portal."""
        return (
            agent.is_alive
            and not agent.in_liminal
            and agent.posicion == self.pos
        )
