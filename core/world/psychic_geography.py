"""
PsychicGeography — R5-B3: Historia Irreversible, Geografía Psicológica del Mundo.

El mapa deja de ser neutral. Cada hex acumula una historia que afecta
físicamente a quienes lo habitan, aunque esa historia tenga miles de días
de antigüedad y ningún agente vivo la recuerde directamente.

Los efectos son inexplicables para los agentes → superstición automática.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

MarkType = Literal[
    "zona_traumatica",  # lugar donde ocurrió una catástrofe/masacre → ansiedad
    "cicatriz_ecologica",  # daño ecológico irreversible → recursos reducidos
    "lugar_sagrado",    # alta carga simbólica → myth_pressure elevada
    "zona_maldita",     # muertes inexplicables → tabú espacial emergente
    "ruina",            # estructura de tribu anterior → curiosidad + incertidumbre
]

_DECAY_RATE  = 0.0003   # decaimiento diario de carga (muy lento — la historia persiste)
_MIN_CARGA   = 0.05     # carga mínima antes de que la marca desaparezca
_SACRED_THRESHOLD = 0.70  # por encima de aquí, zona_traumatica se convierte en lugar_sagrado


@dataclass
class PsychicMark:
    """Marca psicológica permanente en un hex del mapa."""
    tipo:          MarkType
    coord:         tuple[int, int]
    carga_simbolica: float          # 0.0–1.0: intensidad del efecto
    dia_origen:    int
    tribu_origen:  str | None = None
    descripcion:   str        = ""
    n_muertes:     int        = 0   # muertes acumuladas (solo zona_maldita)


class PsychicGeography:
    """
    Sistema de geografía psicológica: marcas permanentes en el terreno.

    Las marcas son invisibles para los agentes — solo perciben sus efectos.
    Eso genera tabúes, supersticiones y mitos espaciales sin programación directa.
    """

    def __init__(self) -> None:
        # coord → lista de marcas (puede haber múltiples tipos en el mismo hex)
        self._marks: dict[tuple[int, int], list[PsychicMark]] = {}

    # ── API pública ───────────────────────────────────────────────────────────

    def register_mark(
        self,
        coord:         tuple[int, int],
        tipo:          MarkType,
        carga:         float,
        dia:           int,
        tribu:         str | None = None,
        descripcion:   str        = "",
    ) -> PsychicMark:
        """Añade o refuerza una marca en el hex."""
        existing = self._get_mark_of_type(coord, tipo)
        if existing is not None:
            existing.carga_simbolica = min(1.0, existing.carga_simbolica + carga * 0.5)
            return existing

        mark = PsychicMark(
            tipo             = tipo,
            coord            = coord,
            carga_simbolica  = min(1.0, carga),
            dia_origen       = dia,
            tribu_origen     = tribu,
            descripcion      = descripcion,
        )
        self._marks.setdefault(coord, []).append(mark)
        return mark

    def register_death(self, coord: tuple[int, int], dia: int, tribu: str | None = None) -> None:
        """Registra una muerte en el hex — puede elevar la carga o crear zona_maldita."""
        existing_maldita = self._get_mark_of_type(coord, "zona_maldita")
        if existing_maldita is not None:
            existing_maldita.carga_simbolica = min(1.0, existing_maldita.carga_simbolica + 0.08)
            existing_maldita.n_muertes += 1
        else:
            # Primera muerte: crea una carga baja en zona_traumatica
            self.register_mark(coord, "zona_traumatica", carga=0.15, dia=dia, tribu=tribu,
                               descripcion=f"Muerte registrada el día {dia}.")

        # Si la zona_traumatica acumula suficiente carga, puede convertirse en lugar_sagrado
        tm = self._get_mark_of_type(coord, "zona_traumatica")
        if tm is not None and tm.carga_simbolica >= _SACRED_THRESHOLD:
            # Promover a lugar_sagrado
            self._marks[coord] = [m for m in self._marks.get(coord, []) if m.tipo != "zona_traumatica"]
            self.register_mark(coord, "lugar_sagrado", carga=tm.carga_simbolica,
                               dia=dia, tribu=tribu,
                               descripcion=f"El sufrimiento acumulado sacraliza este lugar.")

    def register_catastrophe(
        self,
        coord:  tuple[int, int],
        tipo:   str,
        sev:    float,
        dia:    int,
        tribu:  str | None = None,
    ) -> None:
        """Registra el impacto permanente de una catástrofe en el hex."""
        if tipo in ("incendio", "sequia_prolongada"):
            self.register_mark(coord, "cicatriz_ecologica",
                               carga=sev * 0.8, dia=dia, tribu=tribu,
                               descripcion=f"El {tipo.replace('_', ' ')} dejó marca el día {dia}.")
        self.register_mark(coord, "zona_traumatica",
                           carga=sev * 0.6, dia=dia, tribu=tribu,
                           descripcion=f"Catástrofe '{tipo}' (sev {sev:.2f}) el día {dia}.")

    def register_ruin(
        self,
        coord:       tuple[int, int],
        dia:         int,
        tribu_caida: str | None = None,
    ) -> None:
        """Cuando una tribu colapsa, sus hexes se marcan como ruinas."""
        self.register_mark(coord, "ruina", carga=0.55, dia=dia, tribu=tribu_caida,
                           descripcion=f"Ruinas de la tribu {tribu_caida or 'desconocida'}.")

    def boost(self, coord: tuple[int, int], tipo: MarkType, delta: float) -> None:
        """Incrementa la carga de una marca existente."""
        m = self._get_mark_of_type(coord, tipo)
        if m is not None:
            m.carga_simbolica = min(1.0, m.carga_simbolica + delta)

    def get_marks(self, coord: tuple[int, int]) -> list[PsychicMark]:
        return self._marks.get(coord, [])

    def get_nearby_marks(
        self,
        coord:  tuple[int, int],
        radius: int = 2,
    ) -> list[PsychicMark]:
        q, r = coord
        result = []
        for c, marks in self._marks.items():
            if abs(c[0] - q) + abs(c[1] - r) <= radius:
                result.extend(marks)
        return result

    def get_effect(self, coord: tuple[int, int]) -> dict:
        """
        Retorna los efectos agregados para un agente en este hex.
        Keys: ansiedad_delta, myth_pressure_delta, confusion_delta, recurso_factor, es_maldita
        """
        marks = self.get_marks(coord)
        if not marks:
            return {}

        ansiedad   = 0.0
        myth_p     = 0.0
        confusion  = 0.0
        recurso_f  = 1.0
        maldita    = False

        for m in marks:
            c = m.carga_simbolica
            if m.tipo == "zona_traumatica":
                ansiedad  += c * 0.04
                confusion += c * 0.02
            elif m.tipo == "cicatriz_ecologica":
                recurso_f *= max(0.30, 1.0 - c * 0.50)
            elif m.tipo == "lugar_sagrado":
                myth_p    += c * 0.08
                ansiedad  += c * 0.01  # lo sagrado también inquieta
            elif m.tipo == "zona_maldita":
                ansiedad  += c * 0.06
                confusion += c * 0.04
                myth_p    += c * 0.05
                maldita    = True
            elif m.tipo == "ruina":
                confusion += c * 0.03
                myth_p    += c * 0.04

        return {
            "ansiedad_delta":       min(0.20, ansiedad),
            "myth_pressure_delta":  min(0.20, myth_p),
            "confusion_delta":      min(0.15, confusion),
            "recurso_factor":       recurso_f,
            "es_maldita":           maldita,
        }

    # ── Ciclo diario ──────────────────────────────────────────────────────────

    def on_day(self) -> None:
        """Decaimiento lento de todas las marcas. Las marcas se hacen permanentes."""
        to_clean: list[tuple[int, int]] = []
        for coord, marks in self._marks.items():
            alive = []
            for m in marks:
                m.carga_simbolica = max(0.0, m.carga_simbolica - _DECAY_RATE)
                if m.carga_simbolica >= _MIN_CARGA:
                    alive.append(m)
            if alive:
                self._marks[coord] = alive
            else:
                to_clean.append(coord)
        for c in to_clean:
            del self._marks[c]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_mark_of_type(
        self,
        coord: tuple[int, int],
        tipo:  MarkType,
    ) -> PsychicMark | None:
        for m in self._marks.get(coord, []):
            if m.tipo == tipo:
                return m
        return None

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            f"{q},{r}": [
                {
                    "tipo":           m.tipo,
                    "carga":          m.carga_simbolica,
                    "dia_origen":     m.dia_origen,
                    "tribu_origen":   m.tribu_origen,
                    "descripcion":    m.descripcion,
                    "n_muertes":      m.n_muertes,
                }
                for m in marks
            ]
            for (q, r), marks in self._marks.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PsychicGeography":
        pg = cls()
        for key, marks_data in data.items():
            q, r = (int(x) for x in key.split(","))
            coord = (q, r)
            for md in marks_data:
                m = PsychicMark(
                    tipo            = md["tipo"],
                    coord           = coord,
                    carga_simbolica = float(md["carga"]),
                    dia_origen      = int(md["dia_origen"]),
                    tribu_origen    = md.get("tribu_origen"),
                    descripcion     = md.get("descripcion", ""),
                    n_muertes       = int(md.get("n_muertes", 0)),
                )
                pg._marks.setdefault(coord, []).append(m)
        return pg
