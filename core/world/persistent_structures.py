"""
R5-B2: Construcción y estructuras persistentes.

Las estructuras son conocimiento materializado: refugios, altares, marcadores.
Persisten tras la muerte de sus constructores y afectan a quienes las encuentran.
Cuando se abandonan, se convierten en ruinas con carga psíquica propia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

StructureEstado = Literal["activo", "abandonado", "ruina"]
StructureTipo   = Literal["refugio", "altar", "marcador", "deposito"]

_ABANDONMENT_DAYS = 60    # días sin uso → abandonado
_RUIN_DAYS        = 180   # días abandonado → ruina permanente
_SHELTER_ANSIEDAD = 0.008 # reducción de ansiedad por noche bajo refugio


@dataclass
class StructureRecord:
    """Registro de una estructura construida en un hex."""
    tipo:             StructureTipo
    coord:            tuple[int, int]
    tribu_origen:     str | None
    dia_construccion: int
    n_usos:           int    = 0
    dia_ultimo_uso:   int    = 0
    estado:           StructureEstado = "activo"
    dias_abandonado:  int    = 0


class PersistentStructureSystem:
    """
    Registra y gestiona el ciclo de vida de las estructuras construidas.

    Activo → Abandonado (sin uso en 60 días) → Ruina (otros 180 días).
    Las ruinas se reportan a PsychicGeography para generar marca psíquica.
    """

    def __init__(self) -> None:
        # coord → lista de estructuras (pueden coexistir varios tipos)
        self._structures: dict[tuple[int, int], list[StructureRecord]] = {}

    # ── API pública ───────────────────────────────────────────────────────────

    def register_build(
        self,
        coord: tuple[int, int],
        tipo:  StructureTipo,
        tribu: str | None,
        dia:   int,
    ) -> StructureRecord:
        """Registra una nueva construcción en el hex."""
        rec = StructureRecord(
            tipo             = tipo,
            coord            = coord,
            tribu_origen     = tribu,
            dia_construccion = dia,
            dia_ultimo_uso   = dia,
        )
        self._structures.setdefault(coord, []).append(rec)
        return rec

    def register_use(self, coord: tuple[int, int], tipo: StructureTipo, dia: int) -> None:
        """Actualiza el uso de una estructura activa en el hex."""
        for s in self._structures.get(coord, []):
            if s.tipo == tipo and s.estado == "activo":
                s.n_usos       += 1
                s.dia_ultimo_uso = dia
                s.dias_abandonado = 0
                return

    def get_structures(self, coord: tuple[int, int]) -> list[StructureRecord]:
        return [s for s in self._structures.get(coord, []) if s.estado != "ruina"]

    def has_active(self, coord: tuple[int, int], tipo: StructureTipo | None = None) -> bool:
        for s in self._structures.get(coord, []):
            if s.estado == "activo":
                if tipo is None or s.tipo == tipo:
                    return True
        return False

    def shelter_bonus(self, coord: tuple[int, int]) -> float:
        """Reducción de ansiedad por noche en hex con refugio activo."""
        if self.has_active(coord, "refugio"):
            return _SHELTER_ANSIEDAD
        return 0.0

    # ── Ciclo diario ──────────────────────────────────────────────────────────

    def on_day(
        self,
        dia: int,
        occupied_coords: set[tuple[int, int]],
        psychic_geography=None,
    ) -> list[StructureRecord]:
        """
        Avanza el ciclo de vida de las estructuras.
        Devuelve las que se convirtieron en ruina este día.
        """
        newly_ruined: list[StructureRecord] = []

        for coord, structs in self._structures.items():
            is_occupied = coord in occupied_coords
            for s in structs:
                if s.estado == "ruina":
                    continue

                if is_occupied:
                    # Coord ocupada: resetear abandono
                    s.dias_abandonado = 0
                    if s.estado == "abandonado":
                        s.estado = "activo"
                    continue

                s.dias_abandonado += 1

                if s.estado == "activo" and s.dias_abandonado >= _ABANDONMENT_DAYS:
                    s.estado = "abandonado"

                elif s.estado == "abandonado" and s.dias_abandonado >= _RUIN_DAYS:
                    s.estado = "ruina"
                    newly_ruined.append(s)
                    # Registrar en geografía psíquica
                    if psychic_geography is not None:
                        psychic_geography.register_ruin(
                            coord       = coord,
                            dia         = dia,
                            tribu_caida = s.tribu_origen,
                        )

        return newly_ruined

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        result = {}
        for (q, r), structs in self._structures.items():
            result[f"{q},{r}"] = [
                {
                    "tipo":             s.tipo,
                    "tribu_origen":     s.tribu_origen,
                    "dia_construccion": s.dia_construccion,
                    "n_usos":           s.n_usos,
                    "dia_ultimo_uso":   s.dia_ultimo_uso,
                    "estado":           s.estado,
                    "dias_abandonado":  s.dias_abandonado,
                }
                for s in structs
            ]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "PersistentStructureSystem":
        pss = cls()
        for key, structs_data in data.items():
            q, r = (int(x) for x in key.split(","))
            coord = (q, r)
            for sd in structs_data:
                rec = StructureRecord(
                    tipo             = sd["tipo"],
                    coord            = coord,
                    tribu_origen     = sd.get("tribu_origen"),
                    dia_construccion = int(sd["dia_construccion"]),
                    n_usos           = int(sd.get("n_usos", 0)),
                    dia_ultimo_uso   = int(sd.get("dia_ultimo_uso", 0)),
                    estado           = sd.get("estado", "activo"),
                    dias_abandonado  = int(sd.get("dias_abandonado", 0)),
                )
                pss._structures.setdefault(coord, []).append(rec)
        return pss
