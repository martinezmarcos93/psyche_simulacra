from __future__ import annotations

from dataclasses import dataclass, field


# Propiedades base de cada bioma.
# traversal_cost: ticks para atravesar (1.0 = pradera = referencia)
# base_resources: niveles base de cada recurso (0.0–1.0)
# fauna_base: densidad base por tipo de fauna (0.0–1.0)
# carrying_capacity: personas que puede sostener por hex sin degradarlo
# regen_rate: fracción de recuperación diaria (sobre el cap)
# temp_modifier: ajuste de temperatura respecto al clima global (°C)
# humidity_mod: ajuste de humedad relativa
BIOME_DATA: dict[str, dict] = {
    "bosque_templado": {
        "traversal_cost": 1.4,
        "base_resources": {
            "madera": 0.85, "frutos": 0.60, "raices": 0.55,
            "leña": 0.80, "fibras": 0.50, "agua_lluvia": 0.50,
        },
        "fauna_base": {"pequena": 0.60, "grande": 0.30},
        "carrying_capacity": 40,
        "regen_rate": 0.03,
        "temp_modifier": 0.0,
        "humidity_mod": 0.15,
    },
    "pradera_humeda": {
        "traversal_cost": 1.0,
        "base_resources": {
            "plantas": 0.70, "raices": 0.65, "agua_lluvia": 0.40,
        },
        "fauna_base": {"pequena": 0.50, "grande": 0.60},
        "carrying_capacity": 35,
        "regen_rate": 0.04,
        "temp_modifier": 0.0,
        "humidity_mod": 0.10,
    },
    "rio_lago": {
        "traversal_cost": 1.8,
        "base_resources": {
            "agua_fresca": 1.0, "peces": 0.70, "arcilla": 0.60,
            "juncos": 0.75, "cantos_rodados": 0.50,
        },
        "fauna_base": {"acuatica": 0.70, "pequena": 0.40},
        "carrying_capacity": 50,
        "regen_rate": 0.05,
        "temp_modifier": -1.0,
        "humidity_mod": 0.30,
    },
    "montana_alta": {
        "traversal_cost": 3.0,
        "base_resources": {
            "piedra": 0.90, "pedernal": 0.50, "nieve": 0.60,
        },
        "fauna_base": {"grande": 0.20, "pequena": 0.15},
        "carrying_capacity": 10,
        "regen_rate": 0.01,
        "temp_modifier": -8.0,
        "humidity_mod": 0.0,
    },
    "sabana_abierta": {
        "traversal_cost": 1.1,
        "base_resources": {
            "plantas": 0.45, "raices": 0.40,
        },
        "fauna_base": {"pequena": 0.40, "grande": 0.70},
        "carrying_capacity": 25,
        "regen_rate": 0.025,
        "temp_modifier": 4.0,
        "humidity_mod": -0.10,
    },
    "pantano_costero": {
        "traversal_cost": 2.5,
        "base_resources": {
            "agua_salobre": 0.80, "juncos": 0.85,
            "barro": 0.90, "peces_pequenos": 0.60,
        },
        "fauna_base": {"acuatica": 0.60, "insectos": 0.90},
        "carrying_capacity": 15,
        "regen_rate": 0.04,
        "temp_modifier": 0.0,
        "humidity_mod": 0.40,
    },
    "cueva": {
        "traversal_cost": 2.0,
        "base_resources": {
            "refugio": 1.0, "piedra": 0.80,
            "silex": 0.40, "agua_subterranea": 0.50,
        },
        "fauna_base": {"pequena": 0.20},
        "carrying_capacity": 20,
        "regen_rate": 0.01,
        "temp_modifier": -2.0,
        "humidity_mod": 0.20,
    },
    "valle_fertil": {
        "traversal_cost": 1.0,
        "base_resources": {
            "tierra_fertil": 0.90, "plantas": 0.80,
            "agua_lluvia": 0.60, "frutos": 0.70,
        },
        "fauna_base": {"pequena": 0.70, "grande": 0.40},
        "carrying_capacity": 60,
        "regen_rate": 0.05,
        "temp_modifier": 0.0,
        "humidity_mod": 0.20,
    },
    "costa_abierta": {
        "traversal_cost": 1.2,
        "base_resources": {
            "peces": 0.80, "mariscos": 0.75,
            "sal": 0.60, "algas": 0.65, "conchas": 0.50,
        },
        "fauna_base": {"acuatica": 0.80, "aves": 0.50},
        "carrying_capacity": 30,
        "regen_rate": 0.04,
        "temp_modifier": 0.0,
        "humidity_mod": 0.25,
    },
    "desierto_borde": {
        "traversal_cost": 1.8,
        "base_resources": {
            "piedra": 0.70, "arena": 0.95,
        },
        "fauna_base": {"pequena": 0.15, "reptiles": 0.30},
        "carrying_capacity": 5,
        "regen_rate": 0.005,
        "temp_modifier": 8.0,
        "humidity_mod": -0.30,
    },
    "colinas_suaves": {
        "traversal_cost": 1.3,
        "base_resources": {
            "piedra": 0.60, "plantas": 0.55,
            "raices": 0.50, "leña": 0.55,
        },
        "fauna_base": {"pequena": 0.55, "grande": 0.35},
        "carrying_capacity": 30,
        "regen_rate": 0.03,
        "temp_modifier": -1.0,
        "humidity_mod": 0.0,
    },
    "lago_interior": {
        "traversal_cost": 2.0,
        "base_resources": {
            "agua_fresca": 0.95, "peces": 0.80,
            "juncos": 0.70, "arcilla": 0.55,
        },
        "fauna_base": {"acuatica": 0.75, "aves": 0.40},
        "carrying_capacity": 45,
        "regen_rate": 0.04,
        "temp_modifier": -0.5,
        "humidity_mod": 0.25,
    },
}


@dataclass
class Hexagon:
    """Una celda de la grilla hexagonal del mundo."""
    q:          int
    r:          int
    biome:      str

    explored:   bool        = False
    structures: list[str]   = field(default_factory=list)

    @property
    def coords(self) -> tuple[int, int]:
        return (self.q, self.r)

    @property
    def traversal_cost(self) -> float:
        return BIOME_DATA[self.biome]["traversal_cost"]

    @property
    def carrying_capacity(self) -> int:
        return BIOME_DATA[self.biome]["carrying_capacity"]

    @property
    def regen_rate(self) -> float:
        return BIOME_DATA[self.biome]["regen_rate"]
