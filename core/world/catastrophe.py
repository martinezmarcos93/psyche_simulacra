from __future__ import annotations

import random
from dataclasses import dataclass, field

# Biomas con fuentes de agua protegidas (no se secan del todo durante sequía)
_WATER_RESILIENT_BIOMES = frozenset({"rio_lago", "pantano_costero", "lago_interior"})

# Probabilidad diaria de catástrofe por tipo y estación
_PROB_PER_DAY: dict[str, dict[str, float]] = {
    "sequia_prolongada": {
        "verano": 0.0022, "primavera": 0.0010, "otoño": 0.0005, "invierno": 0.0000,
    },
    "invierno_brutal": {
        "invierno": 0.0020, "otoño": 0.0008, "primavera": 0.0003, "verano": 0.0000,
    },
    "incendio": {
        "verano": 0.0025, "primavera": 0.0008, "otoño": 0.0004, "invierno": 0.0000,
    },
    "plaga": {
        "primavera": 0.0015, "verano": 0.0015, "otoño": 0.0015, "invierno": 0.0010,
    },
    "eclipse": {
        "primavera": 0.0004, "verano": 0.0004, "otoño": 0.0004, "invierno": 0.0004,
    },
}

_DURATIONS: dict[str, tuple[int, int]] = {
    "sequia_prolongada": (60, 120),
    "invierno_brutal":   (40,  80),
    "incendio":          ( 7,  21),
    "plaga":             (40,  90),
    "eclipse":           ( 1,   3),
}

_SEVERIDAD: dict[str, tuple[float, float]] = {
    "sequia_prolongada": (0.55, 0.90),
    "invierno_brutal":   (0.50, 0.90),
    "incendio":          (0.65, 1.00),
    "plaga":             (0.30, 0.70),
    "eclipse":           (0.00, 0.00),  # no hay mortalidad directa
}

# Radio de hexes afectados para eventos locales (incendio, plaga inicial)
_LOCAL_RADIUS = 6

_HEX_RING1 = [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]


@dataclass
class CatastropheEvent:
    tipo:               str
    dia_inicio:         int
    duracion_dias:      int
    severidad:          float
    area_hexes:         set[tuple[int, int]] | None  # None = efecto global
    dias_transcurridos: int   = 0
    activa:             bool  = True


class CatastropheEngine:
    """
    Motor de catástrofes de gran escala e irreversibles.

    Genera eventos que duran semanas o meses y dejan huella permanente en el terreno.
    Las catástrofes impulsan mortalidad selectiva, migración forzada y terror
    epistemológico (plaga, eclipse) que alimenta la formación mítica emergente.
    """

    def __init__(self, seed: int = 42) -> None:
        self.active:      CatastropheEvent | None            = None
        self.history:     list[CatastropheEvent]             = []
        self._just_ended: CatastropheEvent | None            = None
        # coord → {tipo, severidad, dias_restantes}: marcas persistentes en el terreno
        self._terrain_marks: dict[tuple[int, int], dict]    = {}
        # hexes con plaga activa (expanden gradualmente)
        self._plague_hexes: set[tuple[int, int]]             = set()
        self._rng = random.Random(seed)

    @property
    def just_ended(self) -> CatastropheEvent | None:
        """Catástrofe que terminó en el día actual. Se resetea al inicio de cada on_day."""
        return self._just_ended

    # ── Ciclo principal ────────────────────────────────────────────────────────

    def on_day(
        self,
        dia:     int,
        estacion: str,
        terrain,                  # TerrainGrid | None
        graves   = None,          # GraveSystem | None
    ) -> CatastropheEvent | None:
        """Avanza estado de catástrofe activa; genera nuevas; decae las huellas."""
        self._just_ended = None   # resetear al inicio de cada día
        if self.active:
            self.active.dias_transcurridos += 1
            self._apply_daily_effects(terrain, graves)
            if self.active.dias_transcurridos >= self.active.duracion_dias:
                self._end_catastrophe()
        else:
            self._try_generate(dia, estacion, terrain)

        # Decaer huellas de terreno
        expired = [c for c, d in self._terrain_marks.items() if d["dias_restantes"] <= 0]
        for c in expired:
            del self._terrain_marks[c]
        for d in self._terrain_marks.values():
            d["dias_restantes"] -= 1

        return self.active

    # ── Generación ─────────────────────────────────────────────────────────────

    def _try_generate(self, dia: int, estacion: str, terrain) -> None:
        for tipo, probs in _PROB_PER_DAY.items():
            if self._rng.random() < probs.get(estacion, 0.0):
                self._start(tipo, dia, terrain)
                return

    def _start(self, tipo: str, dia: int, terrain) -> None:
        dur_min, dur_max   = _DURATIONS[tipo]
        sev_min, sev_max   = _SEVERIDAD[tipo]
        duracion  = self._rng.randint(dur_min, dur_max)
        severidad = sev_min + self._rng.random() * (sev_max - sev_min)

        area: set[tuple[int, int]] | None = None

        if terrain is not None:
            explored = list(terrain.explored_coords())
            if explored and tipo in ("incendio", "plaga"):
                origin = self._rng.choice(explored)
                if tipo == "incendio":
                    area = self._circle(origin, _LOCAL_RADIUS, terrain)
                    # Marcar hexes quemados con persistencia post-catástrofe
                    extra_dias = self._rng.randint(30, 90)
                    for coord in area:
                        self._terrain_marks[coord] = {
                            "tipo":           "quemado",
                            "severidad":      severidad,
                            "dias_restantes": duracion + extra_dias,
                        }
                elif tipo == "plaga":
                    self._plague_hexes = {origin}

        self.active = CatastropheEvent(
            tipo              = tipo,
            dia_inicio        = dia,
            duracion_dias     = duracion,
            severidad         = severidad,
            area_hexes        = area,
        )

    def _apply_daily_effects(self, terrain, graves) -> None:
        if self.active is None:
            return
        tipo = self.active.tipo

        # Expansión de plaga: cada día se extiende a hexes adyacentes (prob 0.12)
        if tipo == "plaga" and terrain is not None:
            new_hexes: set[tuple[int, int]] = set()
            for coord in list(self._plague_hexes):
                for dq, dr in _HEX_RING1:
                    nc = (coord[0] + dq, coord[1] + dr)
                    if nc not in self._plague_hexes and terrain.get(*nc) is not None:
                        if self._rng.random() < 0.12:
                            new_hexes.add(nc)
            self._plague_hexes.update(new_hexes)

        # Tumbas sagradas resistentes: si un GraveHex está en la zona afectada,
        # aumenta su carga simbólica (sobrevivir a la catástrofe los sacraliza más).
        if graves is not None and tipo in ("incendio", "sequia_prolongada"):
            area = self.active.area_hexes
            if area:
                for coord in area:
                    graves.boost_at(coord, delta=0.04)

    def _end_catastrophe(self) -> None:
        if self.active:
            self.active.activa = False
            self._just_ended   = self.active
            self.history.append(self.active)
            if self.active.tipo == "plaga":
                self._plague_hexes = set()
            self.active = None

    # ── Modificadores de recursos ─────────────────────────────────────────────

    def get_water_modifier(self, coord: tuple[int, int], biome: str = "") -> float:
        """Factor multiplicativo para recursos de agua en un hex (1.0 = sin cambio)."""
        # Huellas de terreno persistentes
        if coord in self._terrain_marks:
            mark = self._terrain_marks[coord]
            if mark["tipo"] in ("seco", "quemado"):
                return max(0.05, 1.0 - mark["severidad"] * 0.85)

        if self.active is None:
            return 1.0

        tipo = self.active.tipo
        sev  = self.active.severidad

        if tipo == "sequia_prolongada":
            if self.active.area_hexes is not None and coord not in self.active.area_hexes:
                return 1.0
            # Biomas con agua subterránea/persistente son más resistentes
            if biome in _WATER_RESILIENT_BIOMES:
                return max(0.20, 1.0 - sev * 0.50)
            return max(0.05, 1.0 - sev * 0.88)

        if tipo == "incendio":
            if self.active.area_hexes and coord in self.active.area_hexes:
                return max(0.05, 1.0 - sev * 0.80)

        return 1.0

    def get_food_modifier(self, coord: tuple[int, int]) -> float:
        """Factor multiplicativo para recursos de comida en un hex."""
        if coord in self._terrain_marks:
            mark = self._terrain_marks[coord]
            if mark["tipo"] == "quemado":
                return max(0.03, 1.0 - mark["severidad"] * 0.90)
            if mark["tipo"] == "seco":
                return max(0.15, 1.0 - mark["severidad"] * 0.60)

        if self.active is None:
            return 1.0

        tipo = self.active.tipo
        sev  = self.active.severidad

        if tipo == "sequia_prolongada":
            return max(0.15, 1.0 - sev * 0.55)
        if tipo == "invierno_brutal":
            return max(0.10, 1.0 - sev * 0.70)
        if tipo == "incendio":
            if self.active.area_hexes and coord in self.active.area_hexes:
                return max(0.03, 1.0 - sev * 0.90)

        return 1.0

    # ── Mortalidad selectiva ──────────────────────────────────────────────────

    def get_survival_risk_mod(
        self,
        coord:     tuple[int, int],
        edad:      int,
        is_infant: bool,
    ) -> float:
        """
        Riesgo diario adicional de muerte por catástrofe activa.
        Devuelve probabilidad de muerte en este día (0.0 = ninguna).
        Mortalidad selectiva: infantes y ancianos son más vulnerables.
        """
        if self.active is None:
            return 0.0

        cat  = self.active
        sev  = cat.severidad

        # Eclipse: no hay mortalidad directa (terror epistemológico puro)
        if cat.tipo == "eclipse":
            return 0.0

        # Verificar área afectada
        if cat.area_hexes is not None and coord not in cat.area_hexes:
            return 0.0
        if cat.tipo == "plaga" and coord not in self._plague_hexes:
            return 0.0

        base = sev * 0.006  # 0.6% por día en severidad máxima (adulto)

        if is_infant:
            base *= 1.80
        elif edad >= 60:
            base *= 1.50
        elif edad >= 50:
            base *= 1.20

        # Invierno afecta más a infantes/ancianos pero menos a adultos sanos
        if cat.tipo == "invierno_brutal" and not is_infant and edad < 50:
            base *= 0.70

        return min(0.35, base)  # cap diario para evitar exterminios

    # ── Datos para snapshot ───────────────────────────────────────────────────

    def get_snapshot_data(self) -> dict | None:
        if self.active is None:
            return None
        return {
            "tipo":               self.active.tipo,
            "severidad":          self.active.severidad,
            "dias_transcurridos": self.active.dias_transcurridos,
            "duracion_dias":      self.active.duracion_dias,
            "area_count":         len(self.active.area_hexes) if self.active.area_hexes else None,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _circle(
        self,
        origin: tuple[int, int],
        radio:  int,
        terrain,
    ) -> set[tuple[int, int]]:
        q, r = origin
        hexes: set[tuple[int, int]] = set()
        for dq in range(-radio, radio + 1):
            for dr in range(-radio, radio + 1):
                if abs(dq) + abs(dr) <= radio:
                    nc = (q + dq, r + dr)
                    if terrain.get(*nc) is not None:
                        hexes.add(nc)
        return hexes

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d: dict = {
            "terrain_marks": {
                f"{q},{r}": data for (q, r), data in self._terrain_marks.items()
            },
            "plague_hexes": [[q, r] for q, r in self._plague_hexes],
            "history": [
                {
                    "tipo":               c.tipo,
                    "dia_inicio":         c.dia_inicio,
                    "duracion_dias":      c.duracion_dias,
                    "severidad":          c.severidad,
                    "dias_transcurridos": c.dias_transcurridos,
                }
                for c in self.history[-10:]  # sólo las últimas 10
            ],
        }
        if self.active:
            d["active"] = {
                "tipo":               self.active.tipo,
                "dia_inicio":         self.active.dia_inicio,
                "duracion_dias":      self.active.duracion_dias,
                "severidad":          self.active.severidad,
                "area_hexes":         [[q, r] for q, r in self.active.area_hexes] if self.active.area_hexes else None,
                "dias_transcurridos": self.active.dias_transcurridos,
            }
        return d

    @classmethod
    def from_dict(cls, data: dict, seed: int = 42) -> CatastropheEngine:
        ce = cls(seed=seed)
        for key, mark_data in data.get("terrain_marks", {}).items():
            q, r = (int(x) for x in key.split(","))
            ce._terrain_marks[(q, r)] = mark_data
        ce._plague_hexes = {(int(c[0]), int(c[1])) for c in data.get("plague_hexes", [])}
        for h in data.get("history", []):
            ce.history.append(CatastropheEvent(
                tipo               = h["tipo"],
                dia_inicio         = h["dia_inicio"],
                duracion_dias      = h["duracion_dias"],
                severidad          = h["severidad"],
                area_hexes         = None,
                dias_transcurridos = h.get("dias_transcurridos", 0),
                activa             = False,
            ))
        if "active" in data:
            a = data["active"]
            area_raw = a.get("area_hexes")
            area = {(int(c[0]), int(c[1])) for c in area_raw} if area_raw else None
            ce.active = CatastropheEvent(
                tipo               = a["tipo"],
                dia_inicio         = a["dia_inicio"],
                duracion_dias      = a["duracion_dias"],
                severidad          = a["severidad"],
                area_hexes         = area,
                dias_transcurridos = a.get("dias_transcurridos", 0),
            )
        return ce
