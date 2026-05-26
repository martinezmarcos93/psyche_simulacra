"""
R5-E2: Zona Liminal como inconsciente colectivo del multiverso.

Cuando varias tribus convergen en el mismo símbolo dominante, ese arquetipo
"resuena" en los hexes liminales con amplificación extra — como si el
inconsciente colectivo de múltiples mundos psíquicos (cada tribu = un mundo
psíquico autónomo) se manifestara en las zonas de umbral.

El resultado (MultiverseEcho) se expone como "multiverse_echo" en el
WorldSnapshot para que la UI lo muestre.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.social.tribe_manager import TribeManager
    from core.social.collective_field import CollectiveField


# ── Parámetros ────────────────────────────────────────────────────────────────

_MIN_TRIBES_FOR_ECHO   = 2     # mínimo de tribus que deben compartir el símbolo
_ECHO_BOOST_PER_TRIBE  = 0.006 # myth_pressure extra por tribu convergente en hexes liminales
_ECHO_SYMBOL_BOOST     = 0.008 # boost al símbolo en el campo global


@dataclass
class MultiverseEcho:
    """Resultado del análisis de convergencia simbólica inter-tribal."""
    symbol:      str         # símbolo que converge entre más tribus
    level:       float       # nivel promedio de ese símbolo en las tribus convergentes
    tribe_count: int         # cuántas tribus lo comparten como dominante
    boost:       float       # boost de myth_pressure aplicado a hexes liminales

    def to_dict(self) -> dict:
        return {
            "symbol":      self.symbol,
            "level":       round(self.level, 3),
            "tribe_count": self.tribe_count,
            "boost":       round(self.boost, 4),
        }


class MultiverseCollectiveEcho:
    """
    Analiza los campos locales de todas las tribus y detecta convergencia
    simbólica inter-tribal. Aplica el eco a los hexes liminales.
    """

    def __init__(self) -> None:
        self._last_echo: MultiverseEcho | None = None

    # ── API principal ─────────────────────────────────────────────────────────

    def on_day(
        self,
        tribe_fields:   dict,        # tribe_id → CollectiveField
        liminal_sys,                  # LiminalHexSystem | None
        global_field,                 # CollectiveField global
        cultural_memories: dict,      # tribe_id → CulturalMemory
        dia: int,
    ) -> MultiverseEcho | None:
        """
        Calcula el eco del multiverso y aplica sus efectos.
        Devuelve el echo para exponerlo en el WorldSnapshot.
        """
        if len(tribe_fields) < _MIN_TRIBES_FOR_ECHO:
            self._last_echo = None
            return None

        echo = self._compute_echo(tribe_fields)
        if echo is None:
            self._last_echo = None
            return None

        self._last_echo = echo
        self._apply_echo(echo, liminal_sys, global_field, cultural_memories, dia)
        return echo

    @property
    def last_echo(self) -> MultiverseEcho | None:
        return self._last_echo

    # ── Cálculo de convergencia ───────────────────────────────────────────────

    def _compute_echo(self, tribe_fields: dict) -> MultiverseEcho | None:
        # Contar cuántas tribus tienen cada símbolo como dominante
        dominant_counts: dict[str, list[float]] = {}
        for lf in tribe_fields.values():
            dom, _ = lf.dominant_archetype_pair()
            level  = lf.symbols.get(dom, 0.0)
            dominant_counts.setdefault(dom, []).append(level)

        # Símbolo con mayor convergencia
        best_sym   = max(dominant_counts, key=lambda s: len(dominant_counts[s]))
        tribe_list = dominant_counts[best_sym]

        if len(tribe_list) < _MIN_TRIBES_FOR_ECHO:
            return None

        avg_level = sum(tribe_list) / len(tribe_list)
        boost     = len(tribe_list) * _ECHO_BOOST_PER_TRIBE

        return MultiverseEcho(
            symbol      = best_sym,
            level       = avg_level,
            tribe_count = len(tribe_list),
            boost       = boost,
        )

    # ── Aplicación del eco ────────────────────────────────────────────────────

    def _apply_echo(
        self,
        echo:              MultiverseEcho,
        liminal_sys,
        global_field,
        cultural_memories: dict,
        dia:               int,
    ) -> None:
        # Amplificar el símbolo convergente en el campo global
        global_field.symbols[echo.symbol] = min(
            1.0,
            global_field.symbols.get(echo.symbol, 0.0) + _ECHO_SYMBOL_BOOST * echo.tribe_count
        )
        global_field.myth_pressure = min(1.0, global_field.myth_pressure + echo.boost * 0.5)

        # Amplificar myth_pressure en hexes liminales
        if liminal_sys is not None:
            for lhex in liminal_sys.hexes:
                # El eco resuena en el pool simbólico del hex
                if echo.symbol in lhex.symbol_pool:
                    global_field.myth_pressure = min(
                        1.0,
                        global_field.myth_pressure + echo.boost
                    )

        # Registrar en memorias culturales de las tribus convergentes
        if echo.tribe_count >= 3:
            for cmem in cultural_memories.values():
                if cmem is None:
                    continue
                try:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = "multiverso",
                        arquetipo_dominante = echo.symbol,
                        tipo_evento         = "eco_del_multiverso",
                        descripcion         = (
                            f"El arquetipo «{echo.symbol}» resuena en {echo.tribe_count} tribus "
                            f"simultáneamente, amplificando los hexes liminales del mundo."
                        ),
                        intensidad          = min(1.0, echo.tribe_count * 0.15),
                    )
                except Exception:
                    pass
