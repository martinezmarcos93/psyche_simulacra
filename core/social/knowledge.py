from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KnowledgeUnit:
    nombre:      str
    tipo:        str    # "supervivencia", "ritual", "medicina", "construccion", "subsistencia"
    valor:       float  # 0-1: importancia para la supervivencia
    complejidad: float  # 0-1: dificultad de transmisión (afecta prob. de enseñanza exitosa)


_ALL_KNOWLEDGE: dict[str, KnowledgeUnit] = {
    "conservacion_agua":    KnowledgeUnit("conservacion_agua",    "supervivencia", 0.85, 0.40),
    "fuego_ritual":         KnowledgeUnit("fuego_ritual",         "ritual",        0.70, 0.55),
    "curacion":             KnowledgeUnit("curacion",             "medicina",      0.90, 0.60),
    "tecnica_constructiva": KnowledgeUnit("tecnica_constructiva", "construccion",  0.65, 0.50),
    "caza_avanzada":        KnowledgeUnit("caza_avanzada",        "subsistencia",  0.75, 0.45),
    "navegacion":           KnowledgeUnit("navegacion",           "exploracion",   0.60, 0.35),
    "alquimia_vegetal":     KnowledgeUnit("alquimia_vegetal",     "medicina",      0.80, 0.70),
}

# Condición → (nombre_conocimiento, probabilidad_base_diaria)
_DISCOVERY_TRIGGERS: list[tuple[str, str, float]] = [
    ("fuego_activo",       "fuego_ritual",         0.008),
    ("agua_escasa",        "conservacion_agua",    0.010),
    ("planta_cercana",     "alquimia_vegetal",     0.005),
    ("caza_exitosa",       "caza_avanzada",        0.008),
    ("exploracion_amplia", "navegacion",           0.006),
    ("sabio_dominante",    "tecnica_constructiva", 0.004),
    ("herida",             "curacion",             0.006),
]


class KnowledgeSystem:
    """
    Gestiona la distribución de conocimientos técnicos entre agentes.

    Propiedades emergentes:
    - Descubrimiento accidental ligado a condiciones contextuales, no a
      intención programada.
    - Transmisión imperfecta: la complejidad del conocimiento limita
      la probabilidad de enseñanza exitosa por día.
    - Extinción real: si el único portador muere sin transmitir, el
      conocimiento desaparece del mundo para siempre.
    - Asimetría de poder: el portador único de conocimientos valiosos
      recibe mayor bond_strength entrante de sus compañeros de tribu.
    """

    def __init__(self) -> None:
        self._agent_knowledge: dict[str, set[str]] = {}
        self.extinct_events:   list[dict]          = []  # [{nombre, dia}]

    # ── CRUD básico ────────────────────────────────────────────────────────────

    def give(self, agent_id: str, knowledge_name: str) -> None:
        self._agent_knowledge.setdefault(agent_id, set()).add(knowledge_name)

    def has(self, agent_id: str, knowledge_name: str) -> bool:
        return knowledge_name in self._agent_knowledge.get(agent_id, set())

    def get(self, agent_id: str) -> set[str]:
        return set(self._agent_knowledge.get(agent_id, set()))

    def knowledge_count(self, agent_id: str) -> int:
        return len(self._agent_knowledge.get(agent_id, set()))

    # ── Portadores y extinción ─────────────────────────────────────────────────

    def carriers(self, knowledge_name: str) -> list[str]:
        return [aid for aid, ks in self._agent_knowledge.items() if knowledge_name in ks]

    def remove_agent(self, agent_id: str, dia: int) -> list[str]:
        """
        Elimina al agente y comprueba si algún conocimiento se extingue.
        Devuelve la lista de conocimientos extintos (nadie más los posee).
        """
        lost = self._agent_knowledge.pop(agent_id, set())
        extinct: list[str] = []
        for kname in lost:
            if not self.carriers(kname):
                extinct.append(kname)
                self.extinct_events.append({"nombre": kname, "dia": dia})
        return extinct

    # ── Transmisión ────────────────────────────────────────────────────────────

    def teach(
        self,
        teacher_id:     str,
        student_id:     str,
        knowledge_name: str,
        rng,
    ) -> bool:
        """
        Intento de enseñanza: prob = (1 - complejidad) × 0.15.
        Devuelve True si la transmisión fue exitosa.
        """
        if not self.has(teacher_id, knowledge_name):
            return False
        if self.has(student_id, knowledge_name):
            return False
        ku = _ALL_KNOWLEDGE.get(knowledge_name)
        if ku is None:
            return False
        prob = (1.0 - ku.complejidad) * 0.15
        if rng.random() < prob:
            self.give(student_id, knowledge_name)
            return True
        return False

    # ── Análisis tribal ────────────────────────────────────────────────────────

    def tribe_tech_score(self, agent_ids: list[str]) -> float:
        """Suma de valores de conocimientos únicos poseídos por la tribu."""
        tribe_knowledge: set[str] = set()
        for aid in agent_ids:
            tribe_knowledge |= self._agent_knowledge.get(aid, set())
        return sum(
            _ALL_KNOWLEDGE[k].valor
            for k in tribe_knowledge
            if k in _ALL_KNOWLEDGE
        )

    def unique_carriers_in_tribe(self, agent_id: str, tribe_ids: list[str]) -> list[str]:
        """
        Conocimientos que solo este agente posee dentro de la tribu
        (nadie más en tribe_ids los tiene).
        """
        others: set[str] = set()
        for oid in tribe_ids:
            if oid != agent_id:
                others |= self._agent_knowledge.get(oid, set())
        mine = self._agent_knowledge.get(agent_id, set())
        return list(mine - others)

    # ── Serialización ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "agent_knowledge": {k: list(v) for k, v in self._agent_knowledge.items()},
            "extinct_events":  self.extinct_events,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeSystem:
        ks = cls()
        ks._agent_knowledge = {
            k: set(v) for k, v in data.get("agent_knowledge", {}).items()
        }
        ks.extinct_events = list(data.get("extinct_events", []))
        return ks
