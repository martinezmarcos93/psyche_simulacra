from __future__ import annotations

from dataclasses import dataclass, field
import random as _random


# ── Mutaciones léxicas para conocimiento muy degradado ────────────────────────
_MUTATION_PREFIXES = ["lo_", "el_", "proto_", "gran_", "viejo_"]
_MUTATION_SUFFIXES = ["_oscuro", "_sagrado", "_roto", "_perdido", "_olvidado"]


@dataclass
class KnowledgeUnit:
    nombre:      str
    tipo:        str    # "supervivencia", "ritual", "medicina", "construccion", "subsistencia"
    valor:       float  # 0-1: importancia para la supervivencia
    complejidad: float  # 0-1: dificultad de transmisión (afecta prob. de enseñanza exitosa)


@dataclass
class KnowledgeLineage:
    """
    Instancia de un conocimiento en posesión de un agente concreto.
    Registra la fidelidad epistémica acumulada y el historial de transmisiones.

    Fidelidad inicial = 1.0 (descubrimiento accidental o enseñanza directa del
    descubridor). Cada transmisión aplica:
        fidelidad *= (1 - complejidad × 0.15 × (1 - bond_strength))

    Efectos:
        fidelidad > 0.70  → efecto completo
        0.35 – 0.70       → efecto parcial (× fidelidad)
        < 0.35            → aplicación incorrecta (tabúes falsos, rituales ineficaces)
        < 0.20 y ≥ 5 tx.  → nombre mutado; registrado como "supersticion_tecnica"
    """
    nombre_original:  str
    nombre_actual:    str
    fidelidad:        float          = 1.0
    n_transmisiones:  int            = 0
    linaje_id:        str            = ""   # identificador de cadena de transmisión

    def aplicar_degradacion(self, complejidad: float, bond_strength: float) -> None:
        self.fidelidad *= (1.0 - complejidad * 0.15 * (1.0 - bond_strength))
        self.fidelidad  = max(0.0, self.fidelidad)
        self.n_transmisiones += 1
        self._check_mutation()

    def _check_mutation(self) -> None:
        if self.fidelidad < 0.15 and self.n_transmisiones >= 5:
            if self.nombre_actual == self.nombre_original:
                idx = hash(self.linaje_id) % len(_MUTATION_SUFFIXES)
                self.nombre_actual = self.nombre_original + _MUTATION_SUFFIXES[idx]

    @property
    def is_superstition(self) -> bool:
        return self.fidelidad < 0.20 and self.n_transmisiones >= 5

    @property
    def effect_multiplier(self) -> float:
        if self.fidelidad > 0.70:
            return 1.0
        if self.fidelidad > 0.35:
            return self.fidelidad
        return 0.0  # aplicación incorrecta → sin efecto útil

    def to_dict(self) -> dict:
        return {
            "nombre_original":  self.nombre_original,
            "nombre_actual":    self.nombre_actual,
            "fidelidad":        self.fidelidad,
            "n_transmisiones":  self.n_transmisiones,
            "linaje_id":        self.linaje_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> KnowledgeLineage:
        return cls(
            nombre_original  = d["nombre_original"],
            nombre_actual    = d["nombre_actual"],
            fidelidad        = float(d.get("fidelidad", 1.0)),
            n_transmisiones  = int(d.get("n_transmisiones", 0)),
            linaje_id        = d.get("linaje_id", ""),
        )


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
    - Transmisión imperfecta con degradación de fidelidad (Ext. A): cada
      transmisión erosiona la calidad epistémica en función de la complejidad
      del conocimiento y la fuerza del vínculo entre maestro y alumno.
    - Extinción real: si el único portador muere sin transmitir, el
      conocimiento desaparece del mundo para siempre.
    - Asimetría de poder: el portador único de conocimientos valiosos
      recibe mayor bond_strength entrante de sus compañeros de tribu.
    """

    def __init__(self) -> None:
        self._agent_knowledge: dict[str, set[str]]                    = {}
        self._agent_lineages:  dict[str, dict[str, KnowledgeLineage]] = {}
        self.extinct_events:   list[dict]                             = []
        self._next_linaje_id:  int                                    = 0

    def _new_linaje_id(self) -> str:
        lid = f"L{self._next_linaje_id:05d}"
        self._next_linaje_id += 1
        return lid

    # ── CRUD básico ────────────────────────────────────────────────────────────

    def give(self, agent_id: str, knowledge_name: str) -> None:
        """Descubrimiento directo: fidelidad inicial = 1.0."""
        self._agent_knowledge.setdefault(agent_id, set()).add(knowledge_name)
        agent_lin = self._agent_lineages.setdefault(agent_id, {})
        if knowledge_name not in agent_lin:
            agent_lin[knowledge_name] = KnowledgeLineage(
                nombre_original = knowledge_name,
                nombre_actual   = knowledge_name,
                fidelidad       = 1.0,
                linaje_id       = self._new_linaje_id(),
            )

    def has(self, agent_id: str, knowledge_name: str) -> bool:
        return knowledge_name in self._agent_knowledge.get(agent_id, set())

    def get(self, agent_id: str) -> set[str]:
        return set(self._agent_knowledge.get(agent_id, set()))

    def knowledge_count(self, agent_id: str) -> int:
        return len(self._agent_knowledge.get(agent_id, set()))

    def get_fidelity(self, agent_id: str, knowledge_name: str) -> float:
        """Retorna la fidelidad del agente para este conocimiento (1.0 si no hay registro)."""
        lin = self._agent_lineages.get(agent_id, {}).get(knowledge_name)
        return lin.fidelidad if lin is not None else 1.0

    def get_nombre_actual(self, agent_id: str, knowledge_name: str) -> str:
        """Nombre posiblemente mutado del conocimiento en este agente."""
        lin = self._agent_lineages.get(agent_id, {}).get(knowledge_name)
        return lin.nombre_actual if lin is not None else knowledge_name

    def get_effect_multiplier(self, agent_id: str, knowledge_name: str) -> float:
        """Multiplicador de efecto según fidelidad (0.0, parcial, o 1.0)."""
        lin = self._agent_lineages.get(agent_id, {}).get(knowledge_name)
        return lin.effect_multiplier if lin is not None else 1.0

    # ── Portadores y extinción ─────────────────────────────────────────────────

    def carriers(self, knowledge_name: str) -> list[str]:
        return [aid for aid, ks in self._agent_knowledge.items() if knowledge_name in ks]

    def remove_agent(self, agent_id: str, dia: int) -> list[str]:
        """
        Elimina al agente y comprueba si algún conocimiento se extingue.
        Devuelve la lista de conocimientos extintos (nadie más los posee).
        """
        lost = self._agent_knowledge.pop(agent_id, set())
        self._agent_lineages.pop(agent_id, None)
        extinct: list[str] = []
        for kname in lost:
            if not self.carriers(kname):
                extinct.append(kname)
                self.extinct_events.append({"nombre": kname, "dia": dia})
        return extinct

    # ── Transmisión con degradación de fidelidad ───────────────────────────────

    def teach(
        self,
        teacher_id:     str,
        student_id:     str,
        knowledge_name: str,
        rng,
        bond_strength:  float = 0.50,
    ) -> tuple[bool, float]:
        """
        Intento de enseñanza: prob = (1 - complejidad) × 0.15.
        Si tiene éxito, el alumno hereda la fidelidad del maestro con degradación.

        Retorna (éxito: bool, fidelidad_resultante: float).
        Retorna (False, 0.0) si la transmisión falla.
        """
        if not self.has(teacher_id, knowledge_name):
            return False, 0.0
        if self.has(student_id, knowledge_name):
            return False, 0.0
        ku = _ALL_KNOWLEDGE.get(knowledge_name)
        if ku is None:
            return False, 0.0
        prob = (1.0 - ku.complejidad) * 0.15
        if rng.random() < prob:
            # Copiar linaje del maestro y aplicar degradación
            teacher_lin = self._agent_lineages.get(teacher_id, {}).get(knowledge_name)
            if teacher_lin is not None:
                import copy
                student_lin = copy.copy(teacher_lin)
            else:
                student_lin = KnowledgeLineage(
                    nombre_original = knowledge_name,
                    nombre_actual   = knowledge_name,
                    fidelidad       = 1.0,
                    linaje_id       = self._new_linaje_id(),
                )
            student_lin.aplicar_degradacion(ku.complejidad, bond_strength)

            self._agent_knowledge.setdefault(student_id, set()).add(knowledge_name)
            self._agent_lineages.setdefault(student_id, {})[knowledge_name] = student_lin
            return True, student_lin.fidelidad
        return False, 0.0

    # ── Análisis tribal ────────────────────────────────────────────────────────

    def tribe_tech_score(self, agent_ids: list[str]) -> float:
        """
        Suma ponderada por fidelidad de los conocimientos únicos de la tribu.
        Un conocimiento superstición cuenta como 0.
        """
        # Mejor fidelidad por conocimiento en la tribu
        best_fidelity: dict[str, float] = {}
        for aid in agent_ids:
            for kname in self._agent_knowledge.get(aid, set()):
                f = self.get_fidelity(aid, kname)
                if f > best_fidelity.get(kname, 0.0):
                    best_fidelity[kname] = f
        return sum(
            _ALL_KNOWLEDGE[k].valor * lin.effect_multiplier
            for k, lin in (
                (kn, type("_", (), {"effect_multiplier": _fidelity_multiplier(bf)})())
                for kn, bf in best_fidelity.items()
                if kn in _ALL_KNOWLEDGE
            )
        )

    def unique_carriers_in_tribe(self, agent_id: str, tribe_ids: list[str]) -> list[str]:
        """
        Conocimientos que solo este agente posee dentro de la tribu
        (nadie más en tribe_ids los tiene) y con fidelidad suficiente para ser útil.
        """
        others: set[str] = set()
        for oid in tribe_ids:
            if oid != agent_id:
                others |= self._agent_knowledge.get(oid, set())
        mine = self._agent_knowledge.get(agent_id, set())
        return [
            k for k in mine - others
            if self.get_fidelity(agent_id, k) > 0.35
        ]

    # ── Serialización ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "agent_knowledge":  {k: list(v) for k, v in self._agent_knowledge.items()},
            "agent_lineages":   {
                aid: {kn: lin.to_dict() for kn, lin in lins.items()}
                for aid, lins in self._agent_lineages.items()
            },
            "extinct_events":   self.extinct_events,
            "next_linaje_id":   self._next_linaje_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeSystem:
        ks = cls()
        ks._agent_knowledge = {
            k: set(v) for k, v in data.get("agent_knowledge", {}).items()
        }
        ks._agent_lineages = {
            aid: {kn: KnowledgeLineage.from_dict(ld) for kn, ld in lins.items()}
            for aid, lins in data.get("agent_lineages", {}).items()
        }
        ks.extinct_events   = list(data.get("extinct_events", []))
        ks._next_linaje_id  = int(data.get("next_linaje_id", 0))
        return ks


def _fidelity_multiplier(fidelidad: float) -> float:
    if fidelidad > 0.70:
        return 1.0
    if fidelidad > 0.35:
        return fidelidad
    return 0.0


# ── R5-B1: Artefactos de conocimiento ────────────────────────────────────────

_ARTIFACT_DECAY_RATE       = 0.0008  # pérdida de integridad diaria
_ARTIFACT_MIN_INTEGRIDAD   = 0.08    # por debajo se desintegra el artefacto
_ARTIFACT_LEARN_PROB       = 0.006   # prob/día de que un agente aprenda del artefacto
_ARTIFACT_FIDELIDAD_FACTOR = 0.65    # aprender del objeto es menos fiel que de un maestro
_ARTIFACT_MIN_FIDELIDAD    = 0.60    # fidelidad mínima para que un agente deje artefacto


@dataclass
class KnowledgeArtifact:
    """Objeto físico que materializa un conocimiento técnico."""
    knowledge_name: str
    fidelidad_base: float          # fidelidad del conocimiento en el momento de creación
    coord:          tuple[int, int]
    tribu_origen:   str | None
    dia_creacion:   int
    integridad:     float = 1.0    # degradación física (0 → desaparece)
    n_learners:     int   = 0      # cuántos agentes han aprendido de él


class ArtifactSystem:
    """
    R5-B1: Herramientas como conocimiento materializado.

    Los agentes con alta fidelidad en conocimientos de construcción/subsistencia
    dejan artefactos físicos al construir. Esos artefactos persisten en el hex
    y pueden transmitir conocimiento a futuros visitantes con fidelidad reducida.

    Fenómenos emergentes:
    - Un agente que llega a hex desconocido encuentra herramientas extrañas → curiosidad.
    - El conocimiento viaja en el espacio aunque no haya enseñanza directa.
    - Artefactos degradados enseñan versiones erróneas → superstición técnica.
    """

    def __init__(self) -> None:
        self._artifacts: dict[tuple[int, int], list[KnowledgeArtifact]] = {}

    def deposit(
        self,
        coord:          tuple[int, int],
        knowledge_name: str,
        fidelidad:      float,
        tribu:          str | None,
        dia:            int,
    ) -> KnowledgeArtifact | None:
        """Deposita un artefacto si la fidelidad del creador es suficiente."""
        if fidelidad < _ARTIFACT_MIN_FIDELIDAD:
            return None
        art = KnowledgeArtifact(
            knowledge_name = knowledge_name,
            fidelidad_base = fidelidad,
            coord          = coord,
            tribu_origen   = tribu,
            dia_creacion   = dia,
        )
        self._artifacts.setdefault(coord, []).append(art)
        return art

    def try_learn(
        self,
        coord:      tuple[int, int],
        agent_id:   str,
        knowledge:  "KnowledgeSystem",
        rng,
    ) -> list[str]:
        """
        Intenta que un agente aprenda de los artefactos en el hex.
        Devuelve lista de nombres de conocimiento aprendidos.
        """
        arts = self._artifacts.get(coord, [])
        learned: list[str] = []
        for art in arts:
            if art.integridad < _ARTIFACT_MIN_INTEGRIDAD:
                continue
            if knowledge.has(agent_id, art.knowledge_name):
                continue
            if rng.random() >= _ARTIFACT_LEARN_PROB * art.integridad:
                continue
            fidelidad_efectiva = art.fidelidad_base * _ARTIFACT_FIDELIDAD_FACTOR
            import copy
            lin = KnowledgeLineage(
                nombre_original = art.knowledge_name,
                nombre_actual   = art.knowledge_name,
                fidelidad       = fidelidad_efectiva,
                linaje_id       = knowledge._new_linaje_id(),
            )
            ku = _ALL_KNOWLEDGE.get(art.knowledge_name)
            if ku is not None:
                lin.aplicar_degradacion(ku.complejidad, 0.0)
            knowledge._agent_knowledge.setdefault(agent_id, set()).add(art.knowledge_name)
            knowledge._agent_lineages.setdefault(agent_id, {})[art.knowledge_name] = lin
            art.n_learners += 1
            learned.append(art.knowledge_name)
        return learned

    def get_artifacts(self, coord: tuple[int, int]) -> list[KnowledgeArtifact]:
        return [a for a in self._artifacts.get(coord, []) if a.integridad >= _ARTIFACT_MIN_INTEGRIDAD]

    def on_day(self) -> None:
        """Degradación diaria. Elimina artefactos desintegrados."""
        to_clean: list[tuple[int, int]] = []
        for coord, arts in self._artifacts.items():
            alive = []
            for a in arts:
                a.integridad = max(0.0, a.integridad - _ARTIFACT_DECAY_RATE)
                if a.integridad >= _ARTIFACT_MIN_INTEGRIDAD:
                    alive.append(a)
            if alive:
                self._artifacts[coord] = alive
            else:
                to_clean.append(coord)
        for c in to_clean:
            del self._artifacts[c]

    def to_dict(self) -> dict:
        return {
            f"{q},{r}": [
                {
                    "knowledge_name": a.knowledge_name,
                    "fidelidad_base": a.fidelidad_base,
                    "tribu_origen":   a.tribu_origen,
                    "dia_creacion":   a.dia_creacion,
                    "integridad":     a.integridad,
                    "n_learners":     a.n_learners,
                }
                for a in arts
            ]
            for (q, r), arts in self._artifacts.items()
            if arts
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactSystem":
        as_ = cls()
        for key, arts_data in data.items():
            q, r = (int(x) for x in key.split(","))
            coord = (q, r)
            for ad in arts_data:
                art = KnowledgeArtifact(
                    knowledge_name = ad["knowledge_name"],
                    fidelidad_base = float(ad["fidelidad_base"]),
                    coord          = coord,
                    tribu_origen   = ad.get("tribu_origen"),
                    dia_creacion   = int(ad["dia_creacion"]),
                    integridad     = float(ad.get("integridad", 1.0)),
                    n_learners     = int(ad.get("n_learners", 0)),
                )
                as_._artifacts.setdefault(coord, []).append(art)
        return as_
