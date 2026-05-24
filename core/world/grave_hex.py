from __future__ import annotations

from dataclasses import dataclass, field

_SYMBOLIC_CHARGE_PER_DEATH = 0.30   # carga que añade cada muerte al hex
_DAILY_DECAY               = 0.001  # la carga decae muy lentamente
_PILGRIMAGE_THRESHOLD      = 0.50   # umbral para activar peregrinaciones


@dataclass
class GraveRecord:
    """Registro de una muerte ocurrida en un hexágono concreto."""
    agente_nombre: str
    arquetipo:     str
    dia_muerte:    int
    intensidad:    float  # promedio de bond_strength de los testigos presentes

    def to_dict(self) -> dict:
        return {
            "agente_nombre": self.agente_nombre,
            "arquetipo":     self.arquetipo,
            "dia_muerte":    self.dia_muerte,
            "intensidad":    self.intensidad,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GraveRecord:
        return cls(
            agente_nombre = d["agente_nombre"],
            arquetipo     = d["arquetipo"],
            dia_muerte    = d["dia_muerte"],
            intensidad    = float(d["intensidad"]),
        )


@dataclass
class GraveHex:
    """Hexágono que acumula carga simbólica por muertes ocurridas en él."""
    coord:           tuple[int, int]
    carga_simbolica: float             = 0.0
    muertes:         list[GraveRecord] = field(default_factory=list)

    def absorb_death(self, record: GraveRecord) -> None:
        self.muertes.append(record)
        self.carga_simbolica = min(1.0, self.carga_simbolica + record.intensidad * _SYMBOLIC_CHARGE_PER_DEATH)

    def daily_decay(self) -> None:
        self.carga_simbolica = max(0.0, self.carga_simbolica - _DAILY_DECAY)

    @property
    def arquetipo_dominante(self) -> str:
        """El arquetipo que más veces ha muerto en este hex."""
        counts: dict[str, int] = {}
        for m in self.muertes:
            counts[m.arquetipo] = counts.get(m.arquetipo, 0) + 1
        return max(counts, key=counts.__getitem__) if counts else "heroe"

    @property
    def is_active(self) -> bool:
        return self.carga_simbolica >= _PILGRIMAGE_THRESHOLD

    def to_dict(self) -> dict:
        return {
            "coord":           list(self.coord),
            "carga_simbolica": self.carga_simbolica,
            "muertes":         [m.to_dict() for m in self.muertes],
        }

    @classmethod
    def from_dict(cls, d: dict) -> GraveHex:
        g = cls(
            coord           = tuple(d["coord"]),
            carga_simbolica = float(d.get("carga_simbolica", 0.0)),
        )
        g.muertes = [GraveRecord.from_dict(m) for m in d.get("muertes", [])]
        return g


class GraveSystem:
    """
    Gestiona todos los GraveHex del mundo.
    Se actualiza en WorldCore.on_day y expone los sitios activos al snapshot
    para que los agentes puedan navegar hacia ellos (peregrinaciones emergentes).
    """

    def __init__(self) -> None:
        self.graves: dict[tuple[int, int], GraveHex] = {}

    def register_death(
        self,
        coord:         tuple[int, int],
        agente_nombre: str,
        arquetipo:     str,
        dia:           int,
        bond_medio:    float,
    ) -> None:
        if coord not in self.graves:
            self.graves[coord] = GraveHex(coord=coord)
        record = GraveRecord(
            agente_nombre = agente_nombre,
            arquetipo     = arquetipo,
            dia_muerte    = dia,
            intensidad    = max(0.10, bond_medio),
        )
        self.graves[coord].absorb_death(record)

    def daily_update(self) -> None:
        for grave in self.graves.values():
            grave.daily_decay()

    def boost_at(self, coord: tuple[int, int], delta: float) -> None:
        """Incrementa carga simbólica del hex (sobrevivir a catástrofe lo sacraliza más)."""
        if coord in self.graves:
            self.graves[coord].carga_simbolica = min(
                1.0, self.graves[coord].carga_simbolica + delta
            )

    def active_sites(self) -> list[tuple[tuple[int, int], float, str]]:
        """
        Retorna [(coord, carga, arquetipo_dominante)] para graves activos
        (carga ≥ PILGRIMAGE_THRESHOLD). El snapshot lo expone a los agentes.
        """
        return [
            (coord, g.carga_simbolica, g.arquetipo_dominante)
            for coord, g in self.graves.items()
            if g.is_active
        ]

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            f"{q},{r}": g.to_dict()
            for (q, r), g in self.graves.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> GraveSystem:
        gs = cls()
        for key, gdata in data.items():
            q, r = (int(x) for x in key.split(","))
            gs.graves[(q, r)] = GraveHex.from_dict(gdata)
        return gs
