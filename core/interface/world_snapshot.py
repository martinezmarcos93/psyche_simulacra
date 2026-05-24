from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorldSnapshot:
    """
    Foto inmutable del estado del mundo en un tick.
    Los agentes leen esto — nunca el estado vivo directamente.
    Garantiza que todos los agentes toman decisiones sobre el mismo mundo.
    """
    tick:      int
    dia:       int
    hora:      int
    estacion:  str

    # ── Clima ────────────────────────────────────────────────────────────────
    temperatura:      float
    precipitacion:    float        # 0.0 = seco, 1.0 = lluvia intensa
    luminosidad:      float        # 0.0 = noche cerrada, 1.0 = pleno sol
    viento:           float
    evento_climatico: str | None   # "tormenta", "helada", "sequia", None

    # Modificadores precalculados por el Núcleo 1
    # El Núcleo 2 los aplica directamente sin recalcular
    mood_modifier:      float      # efecto del clima en el humor base
    productivity_mod:   float      # efecto en productividad de actividades
    survival_risk:      float      # riesgo climático base (0=nulo, 1=letal)

    # ── Recursos ─────────────────────────────────────────────────────────────
    # Solo hexs conocidos por el grupo (exploración limita visibilidad)
    recursos_por_hex: dict         # {(q,r): {"planta": qty, "agua": qty, ...}}
    fauna_visible:    dict         # {(q,r): {"especie": densidad}}

    # ── Fuego ────────────────────────────────────────────────────────────────
    fuego_activo:     bool
    fuego_coord:      tuple[int, int] | None
    fuego_intensidad: float
    fuego_calor_bonus: float       # beneficio de estar cerca del fuego

    # ── Estado global ────────────────────────────────────────────────────────
    carrying_capacity: int         # cuántos agentes puede sostener el entorno
    resource_pressure: float       # 0=abundancia, 1=crisis

    # ── Resultados del tick anterior ─────────────────────────────────────────
    # El agente sabe si su caza tuvo éxito, qué descubrió, etc.
    action_results: dict           # {agent_id: ActionResult}

    # ── Tumbas sagradas activas ──────────────────────────────────────────────
    # [(coord, carga_simbolica, arquetipo_dominante)] — solo las que superan umbral
    graves_activos: list = field(default_factory=list)

    # ── Catástrofe activa (Hito 5) ───────────────────────────────────────────
    catastrofe_activa: dict | None = None

    # ── Fauna simbólica activa (Hito 6) ──────────────────────────────────────
    # [{nombre, tipo, coord}] — entidades con comportamiento simbólico activas
    fauna_simbolica: list = field(default_factory=list)

    # ── Hexágonos liminales (Hito 8) ─────────────────────────────────────────
    # [{coord, biome, misterio, symbol_pool, es_portal}]
    liminal_hexes: list = field(default_factory=list)
