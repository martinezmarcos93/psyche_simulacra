from __future__ import annotations

import random
from dataclasses import dataclass, field

# Biomas donde se generan hexes liminales
_LIMINAL_BIOMES = frozenset({"cueva", "montana_alta", "pantano_costero"})

_N_HEXES       = 3    # número de hexes liminales en el mapa
_EFFECT_RADIUS = 2    # radio de efectos sobre agentes
_DREAM_RADIUS  = 1    # radio para resonancia onírica aumentada

_ALL_ARCHETYPES = [
    "heroe", "sombra", "madre", "padre", "sabio", "trickster",
    "rebelde", "gobernante", "nino_divino",
]


@dataclass
class LiminalHexData:
    coord:       tuple[int, int]
    biome:       str
    misterio:    float        # 0.45 – 1.0: intensidad de efectos
    symbol_pool: list[str]    # 3 símbolos que inyecta autónomamente
    es_portal:   bool = False # punto de entrada cross-sim (PortalHex)


class LiminalHexSystem:
    """
    Gestiona hexágonos con propiedades de misterio configurable.

    Efectos:
    - Inyección autónoma de símbolos en el ICL cercano (sin origen en agente → superstición)
    - Amplificación no lineal de arquetipos dormidos en visitantes frecuentes
    - Resonancia onírica aumentada: sueños con símbolos ajenos al ICL actual
    - Punto de entrada cross-sim para el proyecto Zona Liminal externo
    """

    def __init__(self, seed: int = 0) -> None:
        self._rng:          random.Random    = random.Random(seed)
        self.hexes:         list[LiminalHexData] = []
        self._initialized:  bool             = False
        self._last_events:  list[dict]       = []

    # ── Inicialización ────────────────────────────────────────────────────────

    def initialize(self, terrain) -> None:
        """Escanea el terreno y elige N hexes en biomas liminales."""
        if self._initialized:
            return
        candidates = [
            (coord, cell.biome)
            for coord, cell in terrain._cells.items()
            if cell.biome in _LIMINAL_BIOMES
        ]
        if not candidates:
            self._initialized = True
            return

        chosen = self._rng.sample(candidates, min(_N_HEXES, len(candidates)))
        for i, (coord, biome) in enumerate(chosen):
            misterio = 0.45 + self._rng.random() * 0.55
            pool     = self._rng.sample(_ALL_ARCHETYPES, 3)
            self.hexes.append(LiminalHexData(
                coord       = coord,
                biome       = biome,
                misterio    = misterio,
                symbol_pool = pool,
                es_portal   = (i == 0),
            ))
        self._initialized = True

    # ── Ciclo diario ──────────────────────────────────────────────────────────

    def on_day(self, dia: int, terrain) -> list[dict]:
        """
        Emite eventos de inyección autónoma de símbolo para los hexes explorados.
        Los eventos son consumidos por AgentCore._process_liminal_hex_effects.
        """
        if not self._initialized:
            self.initialize(terrain)

        events: list[dict] = []
        for lhex in self.hexes:
            cell = terrain.get(*lhex.coord)
            if cell is None or not cell.explored:
                continue
            if self._rng.random() < lhex.misterio * 0.12:
                symbol = self._rng.choice(lhex.symbol_pool)
                events.append({
                    "tipo":     "inyeccion_liminal",
                    "symbol":   symbol,
                    "coord":    lhex.coord,
                    "misterio": lhex.misterio,
                })
        self._last_events = events
        return events

    # ── Consultas ─────────────────────────────────────────────────────────────

    def nearby_hexes(
        self,
        coord:  tuple[int, int],
        radius: int = _EFFECT_RADIUS,
    ) -> list[LiminalHexData]:
        q, r = coord
        return [
            lhex for lhex in self.hexes
            if abs(lhex.coord[0] - q) + abs(lhex.coord[1] - r) <= radius
        ]

    @property
    def portal_coord(self) -> tuple[int, int] | None:
        portal = next((lhex for lhex in self.hexes if lhex.es_portal), None)
        return portal.coord if portal else None

    def active_hexes(self) -> list[dict]:
        return [
            {
                "coord":       list(lhex.coord),
                "biome":       lhex.biome,
                "misterio":    lhex.misterio,
                "symbol_pool": lhex.symbol_pool,
                "es_portal":   lhex.es_portal,
            }
            for lhex in self.hexes
        ]

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "initialized": self._initialized,
            "hexes": [
                {
                    "coord":       list(h.coord),
                    "biome":       h.biome,
                    "misterio":    h.misterio,
                    "symbol_pool": h.symbol_pool,
                    "es_portal":   h.es_portal,
                }
                for h in self.hexes
            ],
        }

    @classmethod
    def from_dict(cls, data: dict, seed: int = 0) -> LiminalHexSystem:
        sys_ = cls(seed=seed)
        sys_._initialized = data.get("initialized", False)
        for hd in data.get("hexes", []):
            sys_.hexes.append(LiminalHexData(
                coord       = tuple(hd["coord"]),
                biome       = hd["biome"],
                misterio    = hd["misterio"],
                symbol_pool = hd["symbol_pool"],
                es_portal   = hd.get("es_portal", False),
            ))
        return sys_
