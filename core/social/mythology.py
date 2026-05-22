"""
Motor de Mitología Emergente — N-Dimensional.

Reemplaza el sistema hardcodeado de 'heroe_vs_monstruo' con un proceso de
cristalización probabilístico inspirado en dos proyectos:

    - Saussure-Quantum (collapse.py): el mito como colapso semiótico.
      El campo colectivo es la Langue (potencial de todos los mitos posibles).
      La cristalización es la Parole (actualización de uno de esos potenciales).
      El ContextoEnunciativo (temperatura + intencionalidad + ruido) determina
      cuándo y cómo colapsa.

    - Laboratorio Cuántico-Junguiano (archetypes.py): los arquetipos como qubits.
      La tensión entre pares arquetípicos es la fuerza que empuja la cristalización.
      El mito resuelve la tensión irreconciliable (Lévi-Strauss).

Proceso en 3 etapas (medición débil de Saussure-Quantum):
    1. PRESIÓN: el campo acumula myth_pressure por traumas y confusión.
    2. PROTO-MITO: cuando el contexto supera un umbral, nace un proto-mito
       que gana coherencia con cada transmisión social entre agentes.
    3. CRISTALIZACIÓN: el proto-mito colapsa en MythCrystal cuando su
       coherencia supera el umbral de cristalización.

Tipos de mito (Campbell):
    cosmogonia   → evento: muerte_masiva, deshidratacion → símbolos: muerte + sombra
    teogonia     → evento: gobernante establecido        → símbolos: gobernante + padre
    antropogonia → evento: primer nacimiento en tribu    → símbolos: madre + nino_divino
    escatologia  → evento: extincion_inminente           → símbolos: muerte + sabio
    mito_moral   → evento: choque_violento, traicion     → símbolos: heroe + rebelde
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents import Agent
    from core.social.collective_field import CollectiveField

# Umbral de contexto para que nazca un proto-mito
_PROTO_MYTH_THRESHOLD: float = 0.35

# Transmisiones sociales necesarias para cristalizar un proto-mito
_COHERENCE_TO_CRYSTALLIZE: float = 5.0

# Ganancia de coherencia por cada transmisión social
_COHERENCE_PER_TRANSMISSION: float = 1.0

# Mapa: par de símbolos dominantes → tipo de mito probable
_PAIR_TO_MYTH_TYPE: dict[frozenset, str] = {
    frozenset({"muerte", "sombra"}):      "cosmogonia",
    frozenset({"muerte", "madre"}):       "cosmogonia",
    frozenset({"gobernante", "padre"}):   "teogonia",
    frozenset({"gobernante", "rebelde"}): "mito_moral",   # Tiranía y Liberación
    frozenset({"madre", "nino_divino"}):  "antropogonia", # Origen y Renacimiento
    frozenset({"muerte", "sabio"}):       "escatologia",
    frozenset({"heroe", "sombra"}):       "mito_moral",
    frozenset({"heroe", "rebelde"}):      "mito_moral",
    frozenset({"trickster", "sombra"}):   "mito_moral",
    frozenset({"sabio", "nino_divino"}):  "teogonia",
    frozenset({"sabio", "trickster"}):    "mito_moral",   # Verdad y Caos
}

# Efectos psicológicos por tipo de mito
# (arquetipo_protagonista, arquetipo_antagonista): efectos sobre agentes afines
_MYTH_EFFECTS: dict[str, dict] = {
    "cosmogonia": {
        "protagonista_arch": "madre",
        "antagonista_arch":  "muerte",
        "efecto_protagonista": {"humor": +0.06, "ansiedad": -0.06},
        "efecto_antagonista":  {"ansiedad": +0.05, "humor": -0.03},
    },
    "teogonia": {
        "protagonista_arch": "gobernante",
        "antagonista_arch":  "rebelde",
        "efecto_protagonista": {"humor": +0.04, "ansiedad": -0.04},
        "efecto_antagonista":  {"ansiedad": +0.06, "humor": -0.04},
    },
    "antropogonia": {
        "protagonista_arch": "madre",
        "antagonista_arch":  "sombra",
        "efecto_protagonista": {"humor": +0.08, "ansiedad": -0.08},
        "efecto_antagonista":  {"ansiedad": +0.03, "humor": -0.02},
    },
    "escatologia": {
        "protagonista_arch": "sabio",
        "antagonista_arch":  "muerte",
        "efecto_protagonista": {"humor": +0.05, "ansiedad": -0.10},
        "efecto_antagonista":  {"ansiedad": +0.08, "humor": -0.05},
    },
    "mito_moral": {
        "protagonista_arch": "heroe",
        "antagonista_arch":  "sombra",
        "efecto_protagonista": {"humor": +0.05, "ansiedad": -0.05},
        "efecto_antagonista":  {"ansiedad": +0.08, "humor": -0.05},
    },
}


@dataclass
class ProtoMito:
    """
    Estado intermedio antes de que un mito cristalice.

    Un proto-mito es una narrativa en formación: el campo tiene la presión,
    el par arquetípico está definido, pero aún no hay suficiente coherencia
    (transmisión social) para que se consolide como mito colectivo.

    Análogo a la 'medición débil' de Saussure-Quantum: el estado colapsa
    gradualmente en lugar de hacerlo de golpe.
    """
    tipo: str                    # Tipo de mito potencial
    par: tuple[str, str]         # Par de arquetipos en tensión
    coherencia: float = 0.0      # Contador de transmisiones (0 → _COHERENCE_TO_CRYSTALLIZE)
    dia_origen: int = 0          # Día en que nació el proto-mito
    intensidad_contexto: float = 0.0  # Probabilidad de cristalización en el momento de origen

    def transmitir(self, delta: float = _COHERENCE_PER_TRANSMISSION) -> None:
        """Registra una transmisión social que aumenta la coherencia del proto-mito."""
        self.coherencia += delta

    def listo_para_cristalizar(self) -> bool:
        return self.coherencia >= _COHERENCE_TO_CRYSTALLIZE


@dataclass
class MythCrystal:
    """
    Un mito cristalizado: narrativa colectiva consolidada.

    A diferencia del sistema anterior, el mito NO muere cuando muere el
    agente protagonista. Se convierte en Leyenda, que sigue irradiando
    efectos sobre la tribu aunque ya no haya un portador vivo.
    """
    name: str
    tipo: str
    par: tuple[str, str]
    active: bool = True
    day_crystallized: int = 0
    protagonista_id: str | None = None   # Agente que encarna el arquetipo positivo
    antagonista_id:  str | None = None   # Agente que encarna el arquetipo negativo
    # Cuando el protagonista muere, el mito se convierte en leyenda (active=False, es_leyenda=True)
    es_leyenda: bool = False
    day_became_legend: int | None = None
    intensidad: float = 1.0   # Decae con el tiempo


class MythologyEngine:
    """
    Motor de Mitología Emergente — N-Dimensional.

    Proceso:
        on_day():
            1. check_proto_myths(): ¿el contexto del campo genera proto-mitos?
            2. check_crystallization(): ¿algún proto-mito tiene suficiente coherencia?
            3. apply_myth_effects(): aplica efectos de mitos cristalizados a agentes.
            4. check_myth_persistence(): actualiza si protagonistas murieron → leyenda.

        on_social_transmission(): llamado por interaction.py cuando dos agentes
            comparten experiencia emocional significativa → aumenta coherencia
            del proto-mito activo.
    """

    def __init__(self) -> None:
        self.active_myths: list[MythCrystal] = []
        self.proto_myths:  list[ProtoMito]   = []
        self._rng = random.Random()

    # ── Ciclo principal ────────────────────────────────────────────────────────

    def on_day(
        self,
        field: CollectiveField,
        agents: dict[str, Agent],
        dia: int,
    ) -> None:
        self._check_proto_myths(field, dia)
        self._check_crystallization(field, agents, dia)
        self.apply_myth_effects(agents)
        self._check_myth_persistence(agents, dia)
        self._decay_myths()

    def on_social_transmission(self, field: CollectiveField) -> None:
        """
        Llamado cuando dos agentes comparten una experiencia emocional intensa.
        Aumenta la coherencia del proto-mito más avanzado.

        Análogo a la 'medición débil' de Saussure-Quantum: cada interacción
        empuja el proto-mito un paso hacia la cristalización.
        """
        if not self.proto_myths:
            return
        # El proto-mito más avanzado recibe la transmisión
        most_advanced = max(self.proto_myths, key=lambda p: p.coherencia)
        most_advanced.transmitir(_COHERENCE_PER_TRANSMISSION)

    # ── Proto-mitos ────────────────────────────────────────────────────────────

    def _check_proto_myths(self, field: CollectiveField, dia: int) -> None:
        """
        Verifica si el ContextoEnunciativo actual genera un proto-mito.

        Solo puede haber un proto-mito activo por tipo de mito a la vez.
        """
        ctx = field.contexto_enunciativo()
        prob = ctx.probabilidad_cristalizacion()

        if prob < _PROTO_MYTH_THRESHOLD:
            return

        par = field.dominant_archetype_pair()
        tipo = _PAIR_TO_MYTH_TYPE.get(frozenset(par), "mito_moral")

        # No crear proto-mito duplicado del mismo tipo
        tipos_activos = {p.tipo for p in self.proto_myths}
        if tipo in tipos_activos:
            return

        # No crear proto-mito si ya existe un mito cristalizado activo del mismo tipo
        tipos_cristalizados = {m.tipo for m in self.active_myths if m.active or m.es_leyenda}
        if tipo in tipos_cristalizados:
            return

        self.proto_myths.append(ProtoMito(
            tipo=tipo,
            par=par,
            dia_origen=dia,
            intensidad_contexto=prob,
        ))

    # ── Cristalización ─────────────────────────────────────────────────────────

    def _check_crystallization(
        self,
        field: CollectiveField,
        agents: dict[str, Agent],
        dia: int,
    ) -> None:
        """
        Cristaliza los proto-mitos que han alcanzado suficiente coherencia.
        """
        listos = [p for p in self.proto_myths if p.listo_para_cristalizar()]

        for proto in listos:
            self.proto_myths.remove(proto)
            crystal = self._crystallize(proto, field, agents, dia)
            if crystal:
                self.active_myths.append(crystal)
                # El mito cristalizado reduce la presión mítica del campo
                field.myth_pressure  = max(0.0, field.myth_pressure  - 0.40)
                field.confusion      = max(0.0, field.confusion      - 0.25)
                field.emotional_pressure = max(0.0, field.emotional_pressure - 0.15)

    def _crystallize(
        self,
        proto: ProtoMito,
        field: CollectiveField,
        agents: dict[str, Agent],
        dia: int,
    ) -> MythCrystal | None:
        """
        Crea un MythCrystal a partir de un ProtoMito, asignando protagonistas
        según el par arquetípico del mito.
        """
        effects = _MYTH_EFFECTS.get(proto.tipo, _MYTH_EFFECTS["mito_moral"])
        prot_arch = effects["protagonista_arch"]
        antag_arch = effects["antagonista_arch"]

        # Buscar agentes que encarnen los arquetipos del mito
        vivos = [a for a in agents.values() if a.is_alive]
        protagonistas = sorted(
            vivos,
            key=lambda a: getattr(a.archetypes, prot_arch if prot_arch != "muerte" else "sabio", 0.0),
            reverse=True,
        )
        antagonistas = sorted(
            vivos,
            key=lambda a: getattr(a.archetypes, antag_arch if antag_arch != "muerte" else "sombra", 0.0),
            reverse=True,
        )

        prot_id  = protagonistas[0].id if protagonistas else None
        antag_id = antagonistas[0].id  if antagonistas  else None

        name = f"{proto.tipo}_dia{dia}"
        return MythCrystal(
            name=name,
            tipo=proto.tipo,
            par=proto.par,
            active=True,
            day_crystallized=dia,
            protagonista_id=prot_id,
            antagonista_id=antag_id,
            intensidad=min(1.0, proto.intensidad_contexto + 0.2),
        )

    # ── Efectos y persistencia ─────────────────────────────────────────────────

    def apply_myth_effects(self, agents: dict[str, Agent]) -> None:
        """
        Aplica efectos psicológicos de los mitos activos y leyendas a los agentes.

        Los mitos activos afectan a sus protagonistas directos.
        Las leyendas irradian efectos sobre TODOS los agentes afines al arquetipo,
        con intensidad reducida (el impacto de los héroes muertos persiste en la
        cultura, no en los individuos concretos).
        """
        for myth in self.active_myths:
            effects = _MYTH_EFFECTS.get(myth.tipo, _MYTH_EFFECTS["mito_moral"])
            intensidad = myth.intensidad

            if myth.active:
                # Mito vivo: afecta a protagonista y antagonista concretos
                self._apply_to_agent(agents, myth.protagonista_id, effects["efecto_protagonista"], intensidad)
                self._apply_to_agent(agents, myth.antagonista_id,  effects["efecto_antagonista"],  intensidad)

            elif myth.es_leyenda:
                # Leyenda: irradia efectos débiles sobre agentes afines al arquetipo
                prot_arch = effects["protagonista_arch"]
                antag_arch = effects["antagonista_arch"]
                leyenda_scale = 0.3 * intensidad

                for agent in agents.values():
                    if not agent.is_alive:
                        continue
                    prot_val = getattr(agent.archetypes, prot_arch if prot_arch != "muerte" else "sabio", 0.0)
                    antag_val = getattr(agent.archetypes, antag_arch if antag_arch != "muerte" else "sombra", 0.0)

                    if prot_val > 0.60:
                        for attr, delta in effects["efecto_protagonista"].items():
                            current = getattr(agent, attr, 0.5)
                            setattr(agent, attr, max(0.0, min(1.0, current + delta * leyenda_scale)))

                    if antag_val > 0.60:
                        for attr, delta in effects["efecto_antagonista"].items():
                            current = getattr(agent, attr, 0.5)
                            setattr(agent, attr, max(0.0, min(1.0, current + delta * leyenda_scale * 0.5)))

    def _apply_to_agent(
        self,
        agents: dict[str, Agent],
        agent_id: str | None,
        efecto: dict[str, float],
        intensidad: float,
    ) -> None:
        if not agent_id or agent_id not in agents:
            return
        agent = agents[agent_id]
        if not agent.is_alive:
            return
        for attr, delta in efecto.items():
            current = getattr(agent, attr, 0.5)
            setattr(agent, attr, max(0.0, min(1.0, current + delta * intensidad)))

    def _check_myth_persistence(self, agents: dict[str, Agent], dia: int) -> None:
        """
        Verifica si los protagonistas de mitos activos han muerto.

        Si mueren → el mito NO se borra. Se convierte en Leyenda:
        sigue irradiando efectos débiles pero ya no tiene protagonistas vivos.
        Esto implementa el principio del ROADMAP2: 'si los agentes protagonistas
        del mito mueren, el mito NO debe caducar inmediatamente.'
        """
        for myth in self.active_myths:
            if not myth.active:
                continue

            prot_vivo  = myth.protagonista_id and myth.protagonista_id in agents and agents[myth.protagonista_id].is_alive
            antag_vivo = myth.antagonista_id  and myth.antagonista_id  in agents and agents[myth.antagonista_id].is_alive

            if not prot_vivo and not antag_vivo:
                myth.active = False
                myth.es_leyenda = True
                myth.day_became_legend = dia

    def _decay_myths(self) -> None:
        """La intensidad de las leyendas decae lentamente con el tiempo."""
        for myth in self.active_myths:
            if myth.es_leyenda:
                myth.intensidad = max(0.0, myth.intensidad * 0.998)

    # ── Consultas ──────────────────────────────────────────────────────────────

    def is_myth_active(self, myth_name: str) -> bool:
        return any(m.name == myth_name and m.active for m in self.active_myths)

    def get_active_myths(self) -> list[MythCrystal]:
        return [m for m in self.active_myths if m.active]

    def get_legends(self) -> list[MythCrystal]:
        return [m for m in self.active_myths if m.es_leyenda]

    def get_myth_hero_monster(self) -> tuple[str | None, str | None]:
        """Retrocompatibilidad con código que consulta el par héroe/monstruo."""
        for myth in self.active_myths:
            if myth.tipo == "mito_moral" and myth.active:
                return myth.protagonista_id, myth.antagonista_id
        return None, None

    # ── Serialización ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "active_myths": [
                {
                    "name":               m.name,
                    "tipo":               m.tipo,
                    "par":                list(m.par),
                    "active":             m.active,
                    "day_crystallized":   m.day_crystallized,
                    "protagonista_id":    m.protagonista_id,
                    "antagonista_id":     m.antagonista_id,
                    "es_leyenda":         m.es_leyenda,
                    "day_became_legend":  m.day_became_legend,
                    "intensidad":         m.intensidad,
                }
                for m in self.active_myths
            ],
            "proto_myths": [
                {
                    "tipo":               p.tipo,
                    "par":                list(p.par),
                    "coherencia":         p.coherencia,
                    "dia_origen":         p.dia_origen,
                    "intensidad_contexto": p.intensidad_contexto,
                }
                for p in self.proto_myths
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> MythologyEngine:
        engine = cls()

        for m in data.get("active_myths", []):
            crystal = MythCrystal(
                name=m.get("name", "unknown"),
                tipo=m.get("tipo", "mito_moral"),
                par=tuple(m.get("par", ["heroe", "sombra"])),
                active=m.get("active", False),
                day_crystallized=m.get("day_crystallized", 0),
                protagonista_id=m.get("protagonista_id"),
                antagonista_id=m.get("antagonista_id"),
                es_leyenda=m.get("es_leyenda", False),
                day_became_legend=m.get("day_became_legend"),
                intensidad=m.get("intensidad", 1.0),
            )
            engine.active_myths.append(crystal)

        for p in data.get("proto_myths", []):
            proto = ProtoMito(
                tipo=p.get("tipo", "mito_moral"),
                par=tuple(p.get("par", ["heroe", "sombra"])),
                coherencia=p.get("coherencia", 0.0),
                dia_origen=p.get("dia_origen", 0),
                intensidad_contexto=p.get("intensidad_contexto", 0.0),
            )
            engine.proto_myths.append(proto)

        return engine

    # ── Retrocompatibilidad con código que llama check_crystallization() ───────

    def check_crystallization(
        self,
        field: CollectiveField,
        agents: dict[str, Agent],
        dia: int,
    ) -> None:
        """Alias mantenido para retrocompatibilidad con agent_core.py."""
        self.on_day(field, agents, dia)
