from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents import Agent
    from core.world.terrain import TerrainGrid

# ── Definiciones de estructuras ───────────────────────────────────────────────

@dataclass
class StructureRecord:
    """Una estructura material erigida por una tribu en una coordenada del mapa."""
    tipo:      str                    # "totem" | "altar" | "muralla" | "hoguera"
    tribe_id:  str
    coord:     tuple[int, int]
    day_built: int
    radio:     int                    # radio de influencia en hexes
    humor_d:   float                  # delta diario de humor (tribu)
    ansiedad_d: float                 # delta diario de ansiedad (tribu)
    arch_push: dict[str, float]       # arquetipo attr → delta/día (tribu)
    duration:  int | None = None      # días de vida; None = permanente
    # Efectos para no-miembros (forasteros dentro del radio)
    humor_d_ext:    float = 0.0
    ansiedad_d_ext: float = 0.0


# Plantillas de cada tipo de estructura
_TEMPLATES: dict[str, dict] = {
    "totem": dict(
        radio=2,
        humor_d=+0.015, ansiedad_d=-0.010,
        arch_push={"gobernante": 0.0005},
        duration=None,
        humor_d_ext=0.0, ansiedad_d_ext=0.0,
    ),
    "altar": dict(
        radio=2,
        humor_d=+0.010, ansiedad_d=-0.015,
        arch_push={"sabio": 0.0005, "self_": 0.0005},
        duration=None,
        humor_d_ext=0.0, ansiedad_d_ext=0.0,
    ),
    "muralla": dict(
        radio=1,
        humor_d=0.0, ansiedad_d=-0.020,
        arch_push={"sombra": 0.0003},
        duration=None,
        humor_d_ext=0.0, ansiedad_d_ext=+0.025,  # tensa a los forasteros
    ),
    "hoguera": dict(
        radio=3,
        humor_d=+0.025, ansiedad_d=-0.015,
        arch_push={"madre": 0.0008},
        duration=30,
        humor_d_ext=+0.008, ansiedad_d_ext=-0.005,
    ),
}

# Separación mínima entre estructuras del mismo tipo (en hexes)
_MIN_DIST: dict[str, int] = {
    "totem":   5,
    "altar":   5,
    "muralla": 3,
    "hoguera": 4,
}

# Intervalo mínimo de días entre construcciones de una tribu (E1)
_BUILD_COOLDOWN = 25


class CultureEngine:
    """
    Gestiona la construcción de estructuras culturales y la irradiación
    de sus auras psicológicas sobre los agentes.
    """

    def __init__(self) -> None:
        self.structures:  list[StructureRecord] = []
        self._last_build: dict[str, int]        = {}  # tribe_id → último día construido

    # ── Construcción motivada ─────────────────────────────────────────────────

    def on_day(
        self,
        agents:         dict[str, Agent],
        tribes:         dict[str, list[str]],   # tribe_id → [agent_ids]
        terrain:        TerrainGrid,
        day:            int,
        tribal_memories: dict | None = None,    # E2/E3: tribe_id → CulturalMemory
        local_fields:   dict | None = None,     # E3: tribe_id → CollectiveField
    ) -> None:
        """Evalúa triggers de construcción y aplica auras a todos los agentes."""
        # 1. Expirar estructuras temporales; registrar ruinas (E3)
        expired: list[StructureRecord] = [
            s for s in self.structures
            if s.duration is not None and (day - s.day_built) >= s.duration
        ]
        self.structures = [
            s for s in self.structures
            if s.duration is None or (day - s.day_built) < s.duration
        ]
        for s in expired:
            if tribal_memories:
                cmem = tribal_memories.get(s.tribe_id)
                if cmem is not None:
                    cmem.record_event(
                        dia                 = day,
                        agente_nombre       = "colectivo",
                        arquetipo_dominante = "sabio",
                        tipo_evento         = "ruina",
                        descripcion         = (
                            f"El {s.tipo} construido en el día {s.day_built} "
                            f"quedó en ruinas. El recuerdo de lo que fue persiste."
                        ),
                        intensidad          = 0.40,
                    )
            if local_fields:
                lf = local_fields.get(s.tribe_id)
                if lf is not None:
                    lf.myth_pressure = min(1.0, lf.myth_pressure + 0.05)

        # 2. Intentar construcción por tribu
        for tribe_id, member_ids in tribes.items():
            alive = [agents[aid] for aid in member_ids if aid in agents and agents[aid].is_alive]
            if len(alive) < 2:  # E1: mínimo 2 miembros
                continue
            last = self._last_build.get(tribe_id, -_BUILD_COOLDOWN)
            if day - last < _BUILD_COOLDOWN:
                continue
            tipo = self._choose_structure(alive)
            if tipo is None:
                continue
            coord = self._choose_location(alive, terrain, tipo)
            if coord is None:
                continue
            self._build(tribe_id, tipo, coord, day, terrain, tribal_memories)
            self._last_build[tribe_id] = day

        # 3. Aplicar auras a agentes vivos
        self._apply_auras(agents, tribes, terrain)

    def _choose_structure(self, alive: list[Agent]) -> str | None:
        """Decide qué estructura construye la tribu según su psicología dominante."""
        # Promediar complejos y arquetipos
        def avg_complex(name: str) -> float:
            return sum(getattr(a.complexes, name, 0.0) for a in alive) / len(alive)

        def avg_arch(attr: str) -> float:
            return sum(getattr(a.archetypes, attr, 0.0) for a in alive) / len(alive)

        def avg_pressure() -> float:
            # Proxy de presión: ansiedad promedio
            return sum(a.ansiedad for a in alive) / len(alive)

        inferioridad = avg_complex("inferioridad")
        abandono     = avg_complex("abandono")
        trascendencia = avg_complex("trascendencia")
        culpa        = avg_complex("culpa")
        self_val     = avg_arch("self_")
        sabio_val    = avg_arch("sabio")
        gobernante   = avg_arch("gobernante")
        padre        = avg_arch("padre")
        presion      = avg_pressure()

        # Prioridad de triggers
        if (inferioridad > 0.50 or abandono > 0.50) and not self._has_nearby_type("muralla", alive):
            return "muralla"
        if (trascendencia > 0.45 or self_val > 0.60) and not self._has_nearby_type("altar", alive):
            return "altar"
        if (culpa > 0.45 or sabio_val > 0.60) and not self._has_nearby_type("altar", alive):
            return "altar"
        if (gobernante > 0.60 or padre > 0.60) and not self._has_nearby_type("totem", alive):
            return "totem"
        if presion > 0.55 and not self._has_nearby_type("hoguera", alive):
            return "hoguera"
        return None

    def _has_nearby_type(self, tipo: str, alive: list[Agent]) -> bool:
        """True si ya existe una estructura de ese tipo cerca de algún miembro."""
        min_dist = _MIN_DIST.get(tipo, 4)
        for agent in alive:
            for s in self.structures:
                if s.tipo != tipo:
                    continue
                d = abs(agent.posicion[0] - s.coord[0]) + abs(agent.posicion[1] - s.coord[1])
                if d <= min_dist:
                    return True
        return False

    def _choose_location(
        self,
        alive:   list[Agent],
        terrain: TerrainGrid,
        tipo:    str,
    ) -> tuple[int, int] | None:
        """Elige la coordenada más concurrida del grupo como sitio de construcción."""
        counts: dict[tuple[int, int], int] = {}
        for a in alive:
            counts[a.posicion] = counts.get(a.posicion, 0) + 1
        # Preferir hex más poblado; si hay empate, usar el primero (determinista)
        sorted_coords = sorted(counts.keys(), key=lambda c: -counts[c])
        for coord in sorted_coords:
            if terrain.get(*coord) is not None:
                return coord
        return None

    def _build(
        self,
        tribe_id:        str,
        tipo:            str,
        coord:           tuple[int, int],
        day:             int,
        terrain:         TerrainGrid,
        tribal_memories: dict | None = None,
    ) -> None:
        tmpl = _TEMPLATES[tipo]
        record = StructureRecord(
            tipo=tipo, tribe_id=tribe_id, coord=coord, day_built=day,
            radio=tmpl["radio"],
            humor_d=tmpl["humor_d"], ansiedad_d=tmpl["ansiedad_d"],
            arch_push=dict(tmpl["arch_push"]),
            duration=tmpl["duration"],
            humor_d_ext=tmpl["humor_d_ext"],
            ansiedad_d_ext=tmpl["ansiedad_d_ext"],
        )
        self.structures.append(record)
        terrain.add_structure(*coord, tipo)
        print(f"  [Cultura] Dia {day}: Tribu '{tribe_id}' erigió un {tipo} en {coord}")
        # E2 — registrar construcción como evento cultural
        if tribal_memories:
            cmem = tribal_memories.get(tribe_id)
            if cmem is not None:
                cmem.record_event(
                    dia                 = day,
                    agente_nombre       = "colectivo",
                    arquetipo_dominante = "gobernante",
                    tipo_evento         = "construccion",
                    descripcion         = (
                        f"La tribu {tribe_id} erigió un {tipo} en {coord} "
                        f"el día {day}. La estructura marcó el territorio."
                    ),
                    intensidad          = 0.55,
                )

    # ── Irradiación de auras ──────────────────────────────────────────────────

    def _apply_auras(
        self,
        agents:  dict[str, Agent],
        tribes:  dict[str, list[str]],
        terrain: TerrainGrid,
    ) -> None:
        """Aplica los deltas diarios de aura a cada agente según las estructuras cercanas."""
        # Pre-computar qué tribu pertenece cada agente
        agent_tribe: dict[str, str] = {}
        for tid, mids in tribes.items():
            for aid in mids:
                agent_tribe[aid] = tid

        for agent in agents.values():
            if not agent.is_alive:
                continue
            aq, ar = agent.posicion
            for s in self.structures:
                sq, sr = s.coord
                # Distancia hexagonal simplificada (Manhattan axial)
                dist = (abs(aq - sq) + abs(aq + ar - sq - sr) + abs(ar - sr)) // 2
                if dist > s.radio:
                    continue

                is_member = agent_tribe.get(agent.id) == s.tribe_id

                if is_member:
                    agent.humor    = max(0.0, min(1.0, agent.humor    + s.humor_d))
                    agent.ansiedad = max(0.0, min(1.0, agent.ansiedad + s.ansiedad_d))
                    for attr, delta in s.arch_push.items():
                        current = getattr(agent.archetypes, attr, None)
                        if current is not None:
                            setattr(agent.archetypes, attr, min(1.0, current + delta))
                else:
                    if s.humor_d_ext != 0.0 or s.ansiedad_d_ext != 0.0:
                        agent.humor    = max(0.0, min(1.0, agent.humor    + s.humor_d_ext))
                        agent.ansiedad = max(0.0, min(1.0, agent.ansiedad + s.ansiedad_d_ext))

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "structures": [
                {
                    "tipo":      s.tipo,
                    "tribe_id":  s.tribe_id,
                    "coord":     list(s.coord),
                    "day_built": s.day_built,
                    "radio":     s.radio,
                    "humor_d":   s.humor_d,
                    "ansiedad_d": s.ansiedad_d,
                    "arch_push": dict(s.arch_push),
                    "duration":  s.duration,
                    "humor_d_ext":    s.humor_d_ext,
                    "ansiedad_d_ext": s.ansiedad_d_ext,
                }
                for s in self.structures
            ],
            "last_build": dict(self._last_build),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CultureEngine:
        engine = cls()
        for sd in data.get("structures", []):
            engine.structures.append(StructureRecord(
                tipo=sd["tipo"],
                tribe_id=sd["tribe_id"],
                coord=tuple(sd["coord"]),
                day_built=sd["day_built"],
                radio=sd["radio"],
                humor_d=sd["humor_d"],
                ansiedad_d=sd["ansiedad_d"],
                arch_push=dict(sd.get("arch_push", {})),
                duration=sd.get("duration"),
                humor_d_ext=sd.get("humor_d_ext", 0.0),
                ansiedad_d_ext=sd.get("ansiedad_d_ext", 0.0),
            ))
        engine._last_build = dict(data.get("last_build", {}))
        return engine
