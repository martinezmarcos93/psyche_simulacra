from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class SubstanceType(str, Enum):
    ENTEOGENO          = "enteogeno"
    VENENO             = "veneno"
    ALCOHOL            = "alcohol"
    MEDICINAL          = "medicinal"
    ALUCINOGENO_VISUAL = "alucinogeno_visual"
    ADICTIVO           = "adictivo"


@dataclass(frozen=True)
class SubstanceDefinition:
    name:                str
    type:                SubstanceType
    biomes:              tuple[str, ...]
    discovery_prob:      float           # probabilidad por tick de exploración
    archetype_effects:   dict[str, float]
    myth_pressure_boost: float
    physical_effect:     float           # positivo = cura; negativo = daño (fatiga)
    duration_ticks:      int
    addiction_rate:      float           # 0.0 = ninguna; 1.0 = máxima
    is_psychoactive:     bool            # activa la cadena chamánica


# ── Definición de las 6 sustancias ───────────────────────────────────────────

SUBSTANCES: dict[str, SubstanceDefinition] = {
    "setas_sagradas": SubstanceDefinition(
        name                = "setas_sagradas",
        type                = SubstanceType.ENTEOGENO,
        biomes              = ("bosque_templado", "pantano_costero", "cueva"),
        discovery_prob      = 0.030,
        archetype_effects   = {"sabio": 0.08, "sombra": 0.05, "self_": 0.06},
        myth_pressure_boost = 0.25,
        physical_effect     = -0.05,
        duration_ticks      = 12,
        addiction_rate      = 0.05,
        is_psychoactive     = True,
    ),
    "raiz_visionaria": SubstanceDefinition(
        name                = "raiz_visionaria",
        type                = SubstanceType.ALUCINOGENO_VISUAL,
        biomes              = ("sabana_abierta", "desierto_borde", "colinas_suaves"),
        discovery_prob      = 0.025,
        archetype_effects   = {"sombra": 0.10, "anima_animus": 0.08, "trickster": 0.05},
        myth_pressure_boost = 0.20,
        physical_effect     = -0.08,
        duration_ticks      = 8,
        addiction_rate      = 0.08,
        is_psychoactive     = True,
    ),
    "baya_fermentada": SubstanceDefinition(
        name                = "baya_fermentada",
        type                = SubstanceType.ALCOHOL,
        biomes              = ("valle_fertil", "pradera_humeda", "bosque_templado"),
        discovery_prob      = 0.050,
        archetype_effects   = {"persona": 0.05, "gobernante": -0.03},
        myth_pressure_boost = 0.05,
        physical_effect     = 0.00,
        duration_ticks      = 6,
        addiction_rate      = 0.12,
        is_psychoactive     = False,
    ),
    "planta_medicinal": SubstanceDefinition(
        name                = "planta_medicinal",
        type                = SubstanceType.MEDICINAL,
        biomes              = ("valle_fertil", "rio_lago", "pradera_humeda", "bosque_templado"),
        discovery_prob      = 0.040,
        archetype_effects   = {"madre": 0.05},
        myth_pressure_boost = 0.03,
        physical_effect     = 0.15,
        duration_ticks      = 4,
        addiction_rate      = 0.01,
        is_psychoactive     = False,
    ),
    "hongo_venenoso": SubstanceDefinition(
        name                = "hongo_venenoso",
        type                = SubstanceType.VENENO,
        biomes              = ("pantano_costero", "cueva", "bosque_templado"),
        discovery_prob      = 0.020,
        archetype_effects   = {"sombra": 0.12, "heroe": -0.05},
        myth_pressure_boost = 0.15,
        physical_effect     = -0.30,
        duration_ticks      = 24,
        addiction_rate      = 0.00,
        is_psychoactive     = False,
    ),
    "resina_adictiva": SubstanceDefinition(
        name                = "resina_adictiva",
        type                = SubstanceType.ADICTIVO,
        biomes              = ("montana_alta", "desierto_borde"),
        discovery_prob      = 0.015,
        archetype_effects   = {"anima_animus": 0.06, "sombra": 0.04},
        myth_pressure_boost = 0.10,
        physical_effect     = -0.10,
        duration_ticks      = 8,
        addiction_rate      = 0.25,
        is_psychoactive     = True,
    ),
}

SUBSTANCE_NAMES: frozenset[str] = frozenset(SUBSTANCES.keys())

# Bioma → lista de sustancias presentes (precalculado)
_BIOME_TO_SUBSTANCES: dict[str, list[str]] = {}
for _name, _defn in SUBSTANCES.items():
    for _biome in _defn.biomes:
        _BIOME_TO_SUBSTANCES.setdefault(_biome, []).append(_name)


class SubstanceSystem:
    """
    Gestiona la distribución, descubrimiento y consumo de sustancias en el mundo.

    Las sustancias no son recursos normales: son fenomenológicamente distintas
    (no se ven hasta que se descubren, tienen efectos sobre la psique, crean
    dependencia y generan dinámicas chamánicas emergentes).
    """

    _REGEN_RATE = 0.015  # recuperación diaria por hex

    def __init__(self) -> None:
        # coord → nombre de la sustancia descubierta en ese hex
        self._revealed: dict[tuple[int, int], str] = {}
        # coord → cantidad actual (0.0 – 1.0)
        self._amounts:  dict[tuple[int, int], float] = {}

    # ── Descubrimiento ────────────────────────────────────────────────────────

    def maybe_reveal(
        self,
        coord: tuple[int, int],
        biome: str,
        rng:   random.Random,
    ) -> str | None:
        """
        Llamado cuando un agente explora un hex.
        Devuelve el nombre de la sustancia si se descubre por primera vez, si no None.
        """
        if coord in self._revealed:
            return None
        candidates = _BIOME_TO_SUBSTANCES.get(biome, [])
        for name in candidates:
            defn = SUBSTANCES[name]
            if rng.random() < defn.discovery_prob:
                self._revealed[coord] = name
                self._amounts[coord]  = 1.0
                return name
        return None

    # ── Consumo ───────────────────────────────────────────────────────────────

    def consume(
        self,
        coord:    tuple[int, int],
        resource: str,
        amount:   float,
        agent_id: str,
    ) -> float:
        """Consume cantidad de la sustancia. Devuelve la cantidad real consumida."""
        if self._revealed.get(coord) != resource:
            return 0.0
        available = self._amounts.get(coord, 0.0)
        if available < 0.05:
            return 0.0
        taken = min(amount, available)
        self._amounts[coord] = available - taken
        return taken

    # ── Consulta para snapshot ────────────────────────────────────────────────

    def get_for_snapshot(
        self,
        explored_coords: list[tuple[int, int]],
    ) -> dict[tuple[int, int], dict[str, float]]:
        """Devuelve {coord: {sustancia: cantidad}} para hexes explorados con sustancia activa."""
        result: dict[tuple[int, int], dict[str, float]] = {}
        for coord in explored_coords:
            name   = self._revealed.get(coord)
            amount = self._amounts.get(coord, 0.0)
            if name and amount >= 0.05:
                result[coord] = {name: amount}
        return result

    # ── Regeneración diaria ───────────────────────────────────────────────────

    def daily_regen(self) -> None:
        for coord in self._amounts:
            self._amounts[coord] = min(1.0, self._amounts[coord] + self._REGEN_RATE)

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "revealed": {f"{q},{r}": name for (q, r), name in self._revealed.items()},
            "amounts":  {f"{q},{r}": amt  for (q, r), amt  in self._amounts.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> SubstanceSystem:
        ss = cls()
        for key, name in data.get("revealed", {}).items():
            q, r = (int(x) for x in key.split(","))
            ss._revealed[(q, r)] = name
        for key, amt in data.get("amounts", {}).items():
            q, r = (int(x) for x in key.split(","))
            ss._amounts[(q, r)] = float(amt)
        return ss
