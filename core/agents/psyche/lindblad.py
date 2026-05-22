"""
Decoherencia arquetípica — Canal de Lindblad psicológico.

Portado conceptualmente del Laboratorio Cuántico-Junguiano (core/lindblad.py).

En mecánica cuántica, el canal de Lindblad describe cómo un sistema cuántico
pierde coherencia al interactuar con su entorno. Aquí se aplica a la psique:

    T1 — Relajación (olvido activo):
        El arquetipo decae hacia su valor baseline. El contenido psíquico es
        "absorbido" por el inconsciente: sigue existiendo pero pierde intensidad.
        Ejemplo: un agente que experimentó un trauma (sombra alta) gradualmente
        normaliza si el entorno deja de reforzarlo.

    T2 — Desfase (represión activa):
        El arquetipo mantiene su peso pero pierde capacidad de influir en la
        acción. El contenido existe, pero está disociado del comportamiento.
        Ejemplo: la sombra está presente (peso alto) pero el agente actúa
        como si no lo estuviera (acción_bias suprimido).

Uso:
    from core.agents.psyche.lindblad import LindBladChannel

    canal = LindBladChannel(gamma1=0.01, gamma2=0.02)
    canal.apply(agent.archetypes, dt=1)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents.psyche.archetypes import ArchetypeVector

# Valores baseline de cada arquetipo (los valores por defecto de ArchetypeVector)
_ARCHETYPE_BASELINE: dict[str, float] = {
    "self":         0.50,
    "persona":      0.50,
    "sombra":       0.30,
    "anima_animus": 0.40,
    "heroe":        0.50,
    "sabio":        0.40,
    "trickster":    0.25,
    "madre":        0.40,
    "padre":        0.40,
    "nino_divino":  0.30,
    "gobernante":   0.40,
    "rebelde":      0.30,
}


@dataclass
class LindBladChannel:
    """
    Canal de decoherencia arquetípica con dos mecanismos independientes:

    Attributes:
        gamma1: Tasa de relajación T1 — qué tan rápido decae hacia el baseline.
                0.0 = sin relajación. 0.05 = decay notable por día.
        gamma2: Tasa de desfase T2 — qué tan rápido se reprime la acción_bias.
                0.0 = sin represión. 1.0 = bias completamente suprimido.
        represion: Estado actual de represión por arquetipo (0.0–1.0).
                   Calculado internamente por apply_dephasing().
    """
    gamma1: float = 0.005
    gamma2: float = 0.010
    represion: dict[str, float] = field(default_factory=lambda: {
        k: 0.0 for k in _ARCHETYPE_BASELINE
    })

    def apply(self, archetypes: ArchetypeVector, dt: float = 1.0) -> None:
        """
        Aplica T1 y T2 en un paso de tiempo dt.

        Args:
            archetypes: El vector arquetípico del agente a modificar in-place.
            dt: Paso de tiempo en días simulados.
        """
        self._apply_relaxation(archetypes, dt)
        self._apply_dephasing(archetypes, dt)

    def _apply_relaxation(self, archetypes: ArchetypeVector, dt: float) -> None:
        """
        T1 — Relajación: cada arquetipo decae exponencialmente hacia su baseline.

        La fórmula es:  v(t+dt) = baseline + (v(t) - baseline) * exp(-gamma1 * dt)

        Un gamma1 = 0.005 implica que en 200 días un trauma +0.20 sobre baseline
        habrá decaído a +0.07 (caída al ~37% en 1/gamma1 días).
        """
        if self.gamma1 <= 0:
            return

        decay_factor = math.exp(-self.gamma1 * dt)
        vals = archetypes._as_dict()

        for arch, current in vals.items():
            baseline = _ARCHETYPE_BASELINE.get(arch, 0.40)
            new_val = baseline + (current - baseline) * decay_factor
            attr = "self_" if arch == "self" else arch
            setattr(archetypes, attr, max(0.0, min(1.0, new_val)))

    def _apply_dephasing(self, archetypes: ArchetypeVector, dt: float) -> None:
        """
        T2 — Desfase: la represión aumenta cuando el arquetipo supera su baseline.

        Un arquetipo fuertemente activado acumula represión gradualmente.
        La represión se aplica al action_bias en el momento del colapso cuántico
        (ver quantum/collapse.py: multiply bias by (1 - represion[arch])).

        La represión decae cuando el arquetipo vuelve a baseline.
        """
        if self.gamma2 <= 0:
            return

        vals = archetypes._as_dict()
        for arch, current in vals.items():
            baseline = _ARCHETYPE_BASELINE.get(arch, 0.40)
            exceso = max(0.0, current - baseline)

            if exceso > 0.1:
                # Acumular represión si el arquetipo está sobre-activado
                delta_rep = self.gamma2 * exceso * dt
                self.represion[arch] = min(1.0, self.represion.get(arch, 0.0) + delta_rep)
            else:
                # Relajar represión cuando el arquetipo vuelve a baseline
                self.represion[arch] = max(0.0, self.represion.get(arch, 0.0) - self.gamma2 * dt)

    def get_bias_modifier(self, arch: str) -> float:
        """
        Factor multiplicador para el action_bias de un arquetipo dado.

        Returns:
            1.0 - represion[arch], en rango [0.0, 1.0].
            1.0 = sin represión (acción normal).
            0.0 = represión total (acción suprimida).
        """
        return 1.0 - self.represion.get(arch, 0.0)

    def represion_total(self) -> float:
        """Nivel promedio de represión sobre todos los arquetipos."""
        if not self.represion:
            return 0.0
        return sum(self.represion.values()) / len(self.represion)

    def reset(self) -> None:
        """Elimina toda represión acumulada (evento de catarsis o sanación)."""
        for k in self.represion:
            self.represion[k] = 0.0

    # ── Serialización ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "gamma1":    self.gamma1,
            "gamma2":    self.gamma2,
            "represion": dict(self.represion),
        }

    @classmethod
    def from_dict(cls, data: dict) -> LindBladChannel:
        ch = cls(
            gamma1=data.get("gamma1", 0.005),
            gamma2=data.get("gamma2", 0.010),
        )
        ch.represion = data.get("represion", {k: 0.0 for k in _ARCHETYPE_BASELINE})
        return ch
