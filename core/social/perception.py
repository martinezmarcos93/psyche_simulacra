from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecentEvent:
    dia:       int
    tipo:      str
    coord:     tuple[int, int] | None
    intensidad: float


@dataclass
class Rumor:
    tipo:       str
    intensidad: float
    hops:       int
    dia:        int


@dataclass
class CausalAssociation:
    precursor: str
    outcome:   str
    fuerza:    float   # 0.0 – 1.0


# Eventos que "activan" la atención selectiva de cada arquetipo (amplificación ×1.5)
ARCHETYPE_ATTENTION: dict[str, frozenset] = {
    "heroe":        frozenset({"conflicto", "depredador", "choque_violento", "caza_exitosa"}),
    "madre":        frozenset({"nacimiento", "muerte", "hambruna", "deshidratacion"}),
    "sabio":        frozenset({"clima_extremo", "fenomeno_inexplicable", "vision", "sustancia"}),
    "sombra":       frozenset({"muerte", "traicion", "deshidratacion", "veneno"}),
    "trickster":    frozenset({"engano", "sorpresa", "sustancia", "fracaso"}),
    "gobernante":   frozenset({"migracion", "conflicto", "clima_extremo", "muerte_masiva"}),
    "rebelde":      frozenset({"restriccion", "norma_nueva", "castigo"}),
    "anima_animus": frozenset({"vision", "sustancia", "fenomeno_inexplicable", "nacimiento"}),
    "padre":        frozenset({"decision_tribal", "muerte", "migracion", "vejez"}),
    "nino_divino":  frozenset({"nacimiento", "vision", "fenomeno_inexplicable"}),
    "persona":      frozenset({"conflicto", "decision_tribal", "migracion"}),
    "self_":        frozenset({"vision", "nacimiento", "muerte", "fenomeno_inexplicable"}),
}

_CAUSAL_WINDOW_DIAS  = 3     # eventos en esta ventana temporal se asocian causalmente
_RUMOR_DECAY_PER_HOP = 0.20  # pérdida de intensidad por cada salto social


class PerceptionSystem:
    """
    Sistema de percepción limitada por agente.

    Separa lo presenciado directamente (dentro del radio de percepción) de
    lo recibido como rumor (distorsión acumulada por saltos sociales).
    La atención selectiva amplifica eventos resonantes con el arquetipo dominante.
    El sesgo de causalidad forma tabúes emergentes a partir de co-ocurrencias.
    """

    PERCEPTION_RADIUS: int = 3  # hexes

    def __init__(self) -> None:
        self._recent_events:  list[RecentEvent]       = []
        self._rumors:         list[Rumor]             = []
        self._causal_assocs:  list[CausalAssociation] = []

    # ── Percepción directa ────────────────────────────────────────────────────

    def witness(
        self,
        tipo:        str,
        coord:       tuple[int, int] | None,
        intensidad:  float,
        dia:         int,
        agent_coord: tuple[int, int],
    ) -> float:
        """
        Registra un evento si está dentro del radio de percepción.
        coord=None indica evento global (clima, etc.): siempre percibido.
        Devuelve la intensidad percibida (0.0 si fuera del radio).
        """
        if coord is not None:
            dist = abs(coord[0] - agent_coord[0]) + abs(coord[1] - agent_coord[1])
            if dist > self.PERCEPTION_RADIUS:
                return 0.0

        self._recent_events.append(
            RecentEvent(dia=dia, tipo=tipo, coord=coord, intensidad=intensidad)
        )
        if len(self._recent_events) > 30:
            self._recent_events = self._recent_events[-30:]
        return intensidad

    # ── Rumores ───────────────────────────────────────────────────────────────

    def generate_rumors(self) -> list[Rumor]:
        """Convierte los eventos directos recientes en rumores propagables (hop=0)."""
        return [
            Rumor(tipo=e.tipo, intensidad=e.intensidad, hops=0, dia=e.dia)
            for e in self._recent_events[-5:]
        ]

    def receive_rumor(self, rumor: Rumor) -> None:
        """Recibe un rumor con distorsión acumulada por hop; descarta si demasiado débil."""
        intensidad_distorsionada = rumor.intensidad * (1.0 - _RUMOR_DECAY_PER_HOP)
        if intensidad_distorsionada < 0.05:
            return
        self._rumors.append(Rumor(
            tipo       = rumor.tipo,
            intensidad = intensidad_distorsionada,
            hops       = rumor.hops + 1,
            dia        = rumor.dia,
        ))
        if len(self._rumors) > 20:
            self._rumors = self._rumors[-20:]

    # ── Atención selectiva ────────────────────────────────────────────────────

    def perceived_intensity(
        self,
        tipo:      str,
        intensidad: float,
        archetype:  str,
    ) -> float:
        """Amplifica ×1.5 si el tipo de evento coincide con la atención arquetípica."""
        relevant = ARCHETYPE_ATTENTION.get(archetype, frozenset())
        if tipo in relevant:
            return min(1.0, intensidad * 1.5)
        return intensidad

    # ── Sesgo causal → tabúes ─────────────────────────────────────────────────

    def check_causal_bias(self, dia: int) -> list[CausalAssociation]:
        """
        Forma asociaciones causales entre eventos que co-ocurrieron en la ventana temporal.
        El sesgo cognitivo transforma co-ocurrencias en causalidad percibida → tabúes.
        Devuelve las nuevas asociaciones formadas en esta llamada.
        """
        nuevas: list[CausalAssociation] = []
        recientes = [e for e in self._recent_events if dia - e.dia <= _CAUSAL_WINDOW_DIAS]

        for i in range(len(recientes)):
            for j in range(i + 1, len(recientes)):
                e_a = recientes[i]
                e_b = recientes[j]
                if e_a.tipo == e_b.tipo:
                    continue
                already = any(
                    c.precursor == e_a.tipo and c.outcome == e_b.tipo
                    for c in self._causal_assocs
                )
                if already:
                    continue
                fuerza = min(1.0, e_a.intensidad * e_b.intensidad * 2.0)
                if fuerza < 0.15:
                    continue
                assoc = CausalAssociation(
                    precursor = e_a.tipo,
                    outcome   = e_b.tipo,
                    fuerza    = fuerza,
                )
                self._causal_assocs.append(assoc)
                nuevas.append(assoc)

        if len(self._causal_assocs) > 15:
            self._causal_assocs = self._causal_assocs[-15:]
        return nuevas

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "recent_events": [
                {"dia": e.dia, "tipo": e.tipo,
                 "coord": list(e.coord) if e.coord else None,
                 "intensidad": e.intensidad}
                for e in self._recent_events
            ],
            "rumors": [
                {"tipo": r.tipo, "intensidad": r.intensidad,
                 "hops": r.hops, "dia": r.dia}
                for r in self._rumors
            ],
            "causal_assocs": [
                {"precursor": c.precursor, "outcome": c.outcome, "fuerza": c.fuerza}
                for c in self._causal_assocs
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> PerceptionSystem:
        ps = cls()
        for e in data.get("recent_events", []):
            coord_raw = e.get("coord")
            ps._recent_events.append(RecentEvent(
                dia        = e["dia"],
                tipo       = e["tipo"],
                coord      = tuple(coord_raw) if coord_raw else None,
                intensidad = e["intensidad"],
            ))
        for r in data.get("rumors", []):
            ps._rumors.append(Rumor(
                tipo       = r["tipo"],
                intensidad = r["intensidad"],
                hops       = r["hops"],
                dia        = r["dia"],
            ))
        for c in data.get("causal_assocs", []):
            ps._causal_assocs.append(CausalAssociation(
                precursor = c["precursor"],
                outcome   = c["outcome"],
                fuerza    = c["fuerza"],
            ))
        return ps
