from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LineageRecord:
    agent_id:   str
    parent_a:   str | None
    parent_b:   str | None
    dia_nac:    int
    tribe_orig: str


class LineageGraph:
    """
    Árbol genealógico trazable de toda la simulación.

    Permite detectar consanguinidad entre reproductores y calcular
    generación de cada agente.  Los fundadores tienen generación 0.
    No conoce psicología: solo almacena filiación y fechas.
    """

    def __init__(self) -> None:
        self.records: dict[str, LineageRecord] = {}

    def register(
        self,
        agent_id:   str,
        parent_a:   str | None,
        parent_b:   str | None,
        dia:        int,
        tribe_orig: str,
    ) -> None:
        self.records[agent_id] = LineageRecord(
            agent_id   = agent_id,
            parent_a   = parent_a,
            parent_b   = parent_b,
            dia_nac    = dia,
            tribe_orig = tribe_orig,
        )

    def get_ancestors(self, agent_id: str, depth: int = 3) -> set[str]:
        """IDs de ancestros hasta `depth` generaciones (no incluye al propio agente)."""
        result:   set[str] = set()
        frontier: set[str] = {agent_id}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for aid in frontier:
                rec = self.records.get(aid)
                if rec is None:
                    continue
                for parent in (rec.parent_a, rec.parent_b):
                    if parent and parent not in result:
                        result.add(parent)
                        next_frontier.add(parent)
            frontier = next_frontier
            if not frontier:
                break
        return result

    def are_related(self, id_a: str, id_b: str, max_depth: int = 3) -> bool:
        """True si comparten al menos un ancestro en las últimas `max_depth` generaciones."""
        anc_a = self.get_ancestors(id_a, max_depth) | {id_a}
        anc_b = self.get_ancestors(id_b, max_depth) | {id_b}
        return bool((anc_a & anc_b) - {id_a, id_b})

    def consanguinity_score(self, id_a: str, id_b: str) -> float:
        """
        Índice de consanguinidad entre dos agentes.
        0.0 = sin parentesco; 0.50 = hermanos; 0.25 = primos; 0.12 = primos segundos.
        """
        rec_a = self.records.get(id_a)
        rec_b = self.records.get(id_b)
        if rec_a is None or rec_b is None:
            return 0.0

        # Padre/madre directa
        if id_a in (rec_b.parent_a, rec_b.parent_b):
            return 1.0
        if id_b in (rec_a.parent_a, rec_a.parent_b):
            return 1.0

        parents_a = {rec_a.parent_a, rec_a.parent_b} - {None}
        parents_b = {rec_b.parent_a, rec_b.parent_b} - {None}

        # Hermanos (al menos un padre en común)
        if parents_a & parents_b:
            return 0.50

        # Primos (al menos un abuelo en común)
        gp_a: set[str] = set()
        for p in parents_a:
            rp = self.records.get(p)
            if rp:
                gp_a |= {rp.parent_a, rp.parent_b} - {None}
        gp_b: set[str] = set()
        for p in parents_b:
            rp = self.records.get(p)
            if rp:
                gp_b |= {rp.parent_a, rp.parent_b} - {None}
        if gp_a & gp_b:
            return 0.25

        # Primos segundos (bisabuelos en común)
        ggp_a: set[str] = set()
        for g in gp_a:
            rg = self.records.get(g)
            if rg:
                ggp_a |= {rg.parent_a, rg.parent_b} - {None}
        ggp_b: set[str] = set()
        for g in gp_b:
            rg = self.records.get(g)
            if rg:
                ggp_b |= {rg.parent_a, rg.parent_b} - {None}
        if ggp_a & ggp_b:
            return 0.12

        return 0.0

    def get_generation(self, agent_id: str, _seen: frozenset[str] | None = None) -> int:
        """Generación del agente (fundadores = 0). Evita ciclos via _seen."""
        seen = _seen or frozenset()
        if agent_id in seen:
            return 0
        rec = self.records.get(agent_id)
        if rec is None or (rec.parent_a is None and rec.parent_b is None):
            return 0
        parent = rec.parent_a or rec.parent_b
        return 1 + self.get_generation(parent, seen | {agent_id})

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            aid: {
                "parent_a":   r.parent_a,
                "parent_b":   r.parent_b,
                "dia_nac":    r.dia_nac,
                "tribe_orig": r.tribe_orig,
            }
            for aid, r in self.records.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> LineageGraph:
        g = cls()
        for aid, d in data.items():
            g.records[aid] = LineageRecord(
                agent_id   = aid,
                parent_a   = d.get("parent_a"),
                parent_b   = d.get("parent_b"),
                dia_nac    = d.get("dia_nac", 0),
                tribe_orig = d.get("tribe_orig", ""),
            )
        return g
