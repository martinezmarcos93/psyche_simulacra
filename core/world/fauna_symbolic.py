from __future__ import annotations

import random
from dataclasses import dataclass, field

# R4-D: Bestias Olvidadas — generación procedural de fauna mítica única
_ADJETIVOS_BESTIA = [
    "eterno", "silencioso", "ardiente", "helado", "sombrío", "dorado",
    "plateado", "ciego", "sangrante", "rojo", "negro", "blanco",
    "hueco", "rugiente", "primordial", "hambriento", "sagrado", "maldito",
]
_ANIMALES_BESTIA = [
    "oso", "lobo", "serpiente", "aguila", "ciervo", "jabali",
    "leon", "tigre", "cocodrilo", "cuervo", "toro", "cabra",
    "hiena", "lince", "zorro", "nutria", "castor", "alce",
]
_BESTIA_SPAWN_PROB   = 0.0005   # prob diaria de aparición de una bestia única
_BESTIA_MAX_ACTIVE   = 2        # máximo de bestias únicas simultáneas
_BESTIA_DURACION     = (90, 240)# días antes de desaparecer
_BESTIA_SYMBOLIC     = 0.55     # carga simbólica base

# Biomas "liminales": el mismo animal aquí genera carga simbólica ×2
_LIMINAL_BIOMES = frozenset({"cueva", "montana_alta", "pantano_costero"})

_ATTACK_RADIUS      = 2       # hexes (Manhattan) de radio de ataque depredador
_PREDATOR_KILL_PROB = 0.015   # 1.5% por agente en radio por día
_SCAVENGER_RADIUS   = 3       # radio en que carroñero detecta tumbas activas
_RARE_PROB_PER_DAY  = 0.004   # probabilidad diaria de fauna rara
_MAX_PER_TYPE       = 2       # máximo de entidades simultáneas por tipo

# Carga simbólica base que inyecta cada avistamiento en el ICL tribal
_SYMBOLIC_LOAD: dict[str, float] = {
    "depredador": 0.18,
    "migratorio": 0.08,
    "nocturno":   0.06,
    "carronero":  0.10,
    "raro":       0.30,
}

# Estaciones válidas para fauna migratoria
_MIGRATION_SEASONS = frozenset({"primavera", "otoño"})

_DURATION_RANGE: dict[str, tuple[int, int]] = {
    "depredador": (20, 60),
    "migratorio": (5,  15),
    "nocturno":   (15, 40),
    "carronero":  (3,  10),
    "raro":       (1,   3),
}

_SPAWN_PROB: dict[str, float] = {
    "depredador": 0.003,
    "migratorio": 0.008,
    "nocturno":   0.005,
    "raro":       _RARE_PROB_PER_DAY,
    "carronero":  0.0,   # condicional a tumbas activas
}

_NAMES_BY_TYPE: dict[str, list[str]] = {
    "depredador": ["lobo_gris", "oso_negro", "lince", "aguila_real"],
    "migratorio": ["ciervo_blanco", "manada_bisontes", "aves_migratorias"],
    "nocturno":   ["buho_grande", "zorro_oscuro", "serpiente_negra"],
    "carronero":  ["cuervo", "buitre", "hiena"],
    "raro":       ["tigre_blanco", "serpiente_blanca", "lobo_dorado", "aguila_bicefala"],
}


@dataclass
class FaunaEntity:
    id:          str
    tipo:        str
    nombre:      str
    coord:       tuple[int, int]
    radio:       int
    dias_activo: int  = 0
    activo:      bool = True
    duracion:    int  = 30   # días hasta desaparecer (asignado al crear)

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "tipo":        self.tipo,
            "nombre":      self.nombre,
            "coord":       list(self.coord),
            "radio":       self.radio,
            "dias_activo": self.dias_activo,
            "activo":      self.activo,
            "duracion":    self.duracion,
        }

    @classmethod
    def from_dict(cls, d: dict) -> FaunaEntity:
        return cls(
            id          = d["id"],
            tipo        = d["tipo"],
            nombre      = d["nombre"],
            coord       = tuple(d["coord"]),
            radio       = d["radio"],
            dias_activo = d.get("dias_activo", 0),
            activo      = d.get("activo", True),
            duracion    = d.get("duracion", 30),
        )


@dataclass
class PredatorKill:
    dia:      int
    coord:    tuple[int, int]
    tribe_id: str
    nombre:   str


class SymbolicFaunaSystem:
    """
    Entidades de fauna con comportamiento e impacto simbólico.
    Complementa a FaunaSystem (recursos de caza) sin reemplazarlo.
    Implementa: depredadores, migratorias, nocturnas, carroñeras, raras.
    """

    def __init__(self, seed: int = 0) -> None:
        self._rng:           random.Random                    = random.Random(seed)
        self.entities:       dict[str, FaunaEntity]           = {}
        self._kills:         list[PredatorKill]               = []
        # tribe_id → {nombre → n_avistamientos}
        self._tribe_obs:     dict[str, dict[str, int]]        = {}
        # nombre_migratoria → [(estacion, dia), ...]
        self._migration_log: dict[str, list[tuple[str, int]]] = {}
        self._next_id:       int                              = 0
        # R4-D: bestias únicas procedurales y su registro de "bestias olvidadas"
        self._bestia_names:  set[str]                         = set()
        self.bestias_olvidadas: list[dict]                    = []

    # ── Ciclo diario ──────────────────────────────────────────────────────────

    def on_day(
        self,
        dia:           int,
        estacion:      str,
        terrain,
        graves_active: list,   # [(coord, carga, arq_dominante)]
    ) -> list[dict]:
        """Avanza entidades; intenta generar nuevas. Retorna eventos del día."""
        events: list[dict] = []

        # Avanzar entidades activas
        for ent in self.entities.values():
            if not ent.activo:
                continue
            ent.dias_activo += 1
            if ent.dias_activo >= ent.duracion:
                ent.activo = False

        # Limpiar kills >7 días
        self._kills = [k for k in self._kills if dia - k.dia <= 7]

        explored = list(terrain.explored_coords()) if terrain is not None else []
        if not explored:
            return events

        # Generar nueva fauna por tipo
        for tipo, prob in _SPAWN_PROB.items():
            if tipo == "carronero":
                continue
            if tipo == "migratorio" and estacion not in _MIGRATION_SEASONS:
                continue
            count = sum(1 for e in self.entities.values() if e.tipo == tipo and e.activo)
            if count >= _MAX_PER_TYPE:
                continue
            if self._rng.random() < prob:
                coord = self._rng.choice(explored)
                ent   = self._spawn(tipo, coord)
                events.append({
                    "tipo":    "aparicion_fauna",
                    "subtipo": tipo,
                    "nombre":  ent.nombre,
                    "coord":   coord,
                })
                if tipo == "migratorio":
                    self._migration_log.setdefault(ent.nombre, []).append((estacion, dia))

        # Carroñeros: aparecen condicionalmente a tumbas activas
        if graves_active:
            n_sca = sum(1 for e in self.entities.values() if e.tipo == "carronero" and e.activo)
            if n_sca < _MAX_PER_TYPE and self._rng.random() < 0.10:
                gcoord, _, _ = self._rng.choice(graves_active)
                ent = self._spawn("carronero", gcoord)
                events.append({
                    "tipo":    "aparicion_fauna",
                    "subtipo": "carronero",
                    "nombre":  ent.nombre,
                    "coord":   gcoord,
                })

        # R4-D: Bestias procedurales únicas
        n_bestias_activas = sum(
            1 for e in self.entities.values()
            if e.tipo == "bestia_mitica" and e.activo
        )
        if n_bestias_activas < _BESTIA_MAX_ACTIVE and self._rng.random() < _BESTIA_SPAWN_PROB:
            coord  = self._rng.choice(explored)
            bestia = self._spawn_bestia(coord, dia)
            events.append({
                "tipo":    "aparicion_bestia_mitica",
                "subtipo": "bestia_mitica",
                "nombre":  bestia.nombre,
                "coord":   coord,
                "dia":     dia,
            })

        # Registrar bestias únicas que desaparecieron → bestias olvidadas
        for ent in self.entities.values():
            if ent.tipo == "bestia_mitica" and not ent.activo and ent.nombre in self._bestia_names:
                if not any(b["nombre"] == ent.nombre for b in self.bestias_olvidadas):
                    self.bestias_olvidadas.append({
                        "nombre":   ent.nombre,
                        "dia_fin":  dia,
                        "coord":    list(ent.coord),
                    })
                    self._bestia_names.discard(ent.nombre)
                    events.append({
                        "tipo":   "bestia_olvidada",
                        "nombre": ent.nombre,
                        "coord":  list(ent.coord),
                        "dia":    dia,
                    })

        return events

    def check_predator_attacks(
        self,
        dia:        int,
        agents_pos: list[tuple[str, tuple[int, int], str]],  # (agent_id, coord, tribe_id)
    ) -> list[dict]:
        """
        Retorna lista de {agent_id, coord, tribe_id, fauna_nombre} de ataques.
        Los ataques no matan directamente — AgentCore los procesa.
        """
        attacks: list[dict] = []
        predators = [e for e in self.entities.values() if e.tipo == "depredador" and e.activo]
        for pred in predators:
            for agent_id, coord, tribe_id in agents_pos:
                dist = abs(coord[0] - pred.coord[0]) + abs(coord[1] - pred.coord[1])
                if dist <= _ATTACK_RADIUS and self._rng.random() < _PREDATOR_KILL_PROB:
                    attacks.append({
                        "agent_id":   agent_id,
                        "coord":      coord,
                        "tribe_id":   tribe_id,
                        "fauna_nombre": pred.nombre,
                    })
                    self._kills.append(PredatorKill(
                        dia=dia, coord=coord, tribe_id=tribe_id, nombre=pred.nombre
                    ))
        return attacks

    # ── Consultas ─────────────────────────────────────────────────────────────

    def register_sighting(self, tribe_id: str, nombre: str) -> None:
        self._tribe_obs.setdefault(tribe_id, {})[nombre] = (
            self._tribe_obs.get(tribe_id, {}).get(nombre, 0) + 1
        )

    def symbolic_charge(self, nombre: str, tribe_id: str, biome: str = "") -> float:
        """
        Carga simbólica diferencial: tribus con más avistamientos acumulan más carga.
        Biomas liminales amplifican ×2.
        """
        tipo = next(
            (e.tipo for e in self.entities.values() if e.nombre == nombre),
            "raro",
        )
        base = _SYMBOLIC_LOAD.get(tipo, 0.10)
        obs  = self._tribe_obs.get(tribe_id, {}).get(nombre, 0)
        carga = min(1.0, base + obs * 0.04)
        if biome in _LIMINAL_BIOMES:
            carga = min(1.0, carga * 2.0)
        return carga

    def kills_last_7_days(self, tribe_id: str) -> int:
        return sum(1 for k in self._kills if k.tribe_id == tribe_id)

    def migration_recurrences(self, nombre: str) -> int:
        return len(self._migration_log.get(nombre, []))

    def active_entities(self) -> list[dict]:
        return [
            {"nombre": e.nombre, "tipo": e.tipo, "coord": list(e.coord)}
            for e in self.entities.values()
            if e.activo
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _spawn_bestia(self, coord: tuple[int, int], dia: int) -> FaunaEntity:
        """Genera una bestia única procedural con nombre compuesto irrepetible."""
        for _ in range(20):
            adj    = self._rng.choice(_ADJETIVOS_BESTIA)
            animal = self._rng.choice(_ANIMALES_BESTIA)
            nombre = f"{adj}_{animal}"
            if nombre not in self._bestia_names:
                break
        else:
            nombre = f"bestia_{dia}"

        self._bestia_names.add(nombre)
        duracion = self._rng.randint(*_BESTIA_DURACION)
        eid      = f"bestia_{self._next_id:04d}"
        self._next_id += 1
        ent = FaunaEntity(
            id       = eid,
            tipo     = "bestia_mitica",
            nombre   = nombre,
            coord    = coord,
            radio    = _ATTACK_RADIUS + 1,
            duracion = duracion,
        )
        self.entities[eid] = ent
        return ent

    def _spawn(self, tipo: str, coord: tuple[int, int]) -> FaunaEntity:
        dur_min, dur_max = _DURATION_RANGE.get(tipo, (10, 30))
        duracion = self._rng.randint(dur_min, dur_max)
        nombres  = _NAMES_BY_TYPE.get(tipo, ["animal_desconocido"])
        nombre   = self._rng.choice(nombres)
        eid      = f"fauna_{self._next_id:04d}"
        self._next_id += 1
        ent = FaunaEntity(
            id       = eid,
            tipo     = tipo,
            nombre   = nombre,
            coord    = coord,
            radio    = _ATTACK_RADIUS if tipo == "depredador" else 1,
            duracion = duracion,
        )
        self.entities[eid] = ent
        return ent

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "entities":          [e.to_dict() for e in self.entities.values()],
            "kills":             [{"dia": k.dia, "coord": list(k.coord),
                                   "tribe_id": k.tribe_id, "nombre": k.nombre}
                                  for k in self._kills],
            "tribe_obs":         self._tribe_obs,
            "migration_log":     {n: [list(v) for v in vs]
                                  for n, vs in self._migration_log.items()},
            "next_id":           self._next_id,
            "bestia_names":      list(self._bestia_names),
            "bestias_olvidadas": self.bestias_olvidadas,
        }

    @classmethod
    def from_dict(cls, data: dict, seed: int = 0) -> SymbolicFaunaSystem:
        sys_ = cls(seed=seed)
        for ed in data.get("entities", []):
            e = FaunaEntity.from_dict(ed)
            sys_.entities[e.id] = e
        for kd in data.get("kills", []):
            sys_._kills.append(PredatorKill(
                dia=kd["dia"], coord=tuple(kd["coord"]),
                tribe_id=kd["tribe_id"], nombre=kd.get("nombre", ""),
            ))
        sys_._tribe_obs     = data.get("tribe_obs", {})
        sys_._migration_log = {
            n: [tuple(v) for v in vs]
            for n, vs in data.get("migration_log", {}).items()
        }
        sys_._next_id           = data.get("next_id", 0)
        sys_._bestia_names      = set(data.get("bestia_names", []))
        sys_.bestias_olvidadas  = list(data.get("bestias_olvidadas", []))
        return sys_
