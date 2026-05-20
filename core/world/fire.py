from __future__ import annotations

import numpy as np

from .climate import ClimateState
from core.interface import ActionResult


class FireSystem:
    """
    Sistema de fuego. En beta: un único fuego activo por vez.
    El fuego decae naturalmente; la lluvia lo apaga; el viento lo mantiene.
    Proporciona calor a los agentes cercanos.
    """

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed + 200)

        self.is_active:   bool                    = False
        self.location:    tuple[int, int] | None  = None
        self.intensity:   float                   = 0.0
        self.heat_bonus:  float                   = 0.0  # beneficio para agentes cercanos

    # ── Encendido ────────────────────────────────────────────────────────────

    def ignite(
        self,
        coord:    tuple[int, int],
        agent_id: str,
        climate:  ClimateState,
    ) -> ActionResult:
        """
        Un agente enciende fuego.
        Con lluvia intensa o viento muy alto, hay probabilidad de fallo.
        """
        # Probabilidad de éxito del encendido
        success_prob = 0.80
        if climate.precipitacion > 0.60:
            success_prob *= (1.0 - climate.precipitacion)
        if climate.viento > 0.70:
            success_prob *= 0.70

        if float(self.rng.random()) > success_prob:
            return ActionResult(
                agent_id      = agent_id,
                action_type   = "encender_fuego",
                success       = False,
                failure_reason = "condiciones_adversas",
                world_effects  = {},
            )

        self.is_active  = True
        self.location   = coord
        self.intensity  = 0.80
        self.heat_bonus = self.intensity * 0.35

        return ActionResult(
            agent_id      = agent_id,
            action_type   = "encender_fuego",
            success       = True,
            world_effects  = {"fuego_encendido": True, "coord": coord},
        )

    # ── Mantenimiento ─────────────────────────────────────────────────────────

    def maintain(self, agent_id: str) -> ActionResult:
        """Un agente mantiene el fuego activo, aumentando su intensidad."""
        if not self.is_active:
            return ActionResult(
                agent_id      = agent_id,
                action_type   = "mantener_fuego",
                success       = False,
                failure_reason = "no_hay_fuego",
                world_effects  = {},
            )
        self.intensity  = min(1.0, self.intensity + 0.15)
        self.heat_bonus = self.intensity * 0.35
        return ActionResult(
            agent_id      = agent_id,
            action_type   = "mantener_fuego",
            success       = True,
            world_effects  = {"intensidad_fuego": self.intensity},
        )

    # ── Actualización ─────────────────────────────────────────────────────────

    def update(self, climate: ClimateState) -> None:
        """Actualiza el fuego cada tick."""
        if not self.is_active:
            return

        # Tasa de decaimiento
        if climate.precipitacion > 0.70:
            decay = 0.12   # Lluvia intensa apaga rápido
        elif climate.precipitacion > 0.40:
            decay = 0.05
        elif climate.viento > 0.70:
            decay = 0.03   # Viento fuerte mantiene el fuego
        else:
            decay = 0.025  # Decaimiento natural

        self.intensity  = max(0.0, self.intensity - decay)
        self.heat_bonus = self.intensity * 0.35

        if self.intensity < 0.04:
            self.is_active  = False
            self.location   = None
            self.intensity  = 0.0
            self.heat_bonus = 0.0

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "is_active":  self.is_active,
            "location":   list(self.location) if self.location else None,
            "intensity":  self.intensity,
            "heat_bonus": self.heat_bonus,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FireSystem:
        f = cls()
        f.is_active  = data["is_active"]
        f.location   = tuple(data["location"]) if data["location"] else None
        f.intensity  = data["intensity"]
        f.heat_bonus = data["heat_bonus"]
        return f
