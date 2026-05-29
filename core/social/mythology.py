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

import os
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING


# ── Hito E: Deidades procedurales ─────────────────────────────────────────────

# Epítetos por arquetipo: hash(tribe_id) % len → nombre único por tribu
_DEITY_EPITHETS: dict[str, list[str]] = {
    "heroe":       ["El Gran Guerrero", "Ares Primordial", "El Glorioso Eterno"],
    "sombra":      ["La Oscuridad Eterna", "Nyxos el Oculto", "El Devorador de Luz"],
    "madre":       ["La Gran Madre", "Gaia Primordial", "La Nutricia Eterna"],
    "padre":       ["El Padre del Cielo", "El Patriarca Eterno", "El Fundador Divino"],
    "sabio":       ["El Omnisciente", "Logos Eterno", "El que Todo Conoce"],
    "gobernante":  ["El Señor Supremo", "El Ordenador del Cosmos", "El Rey Eterno"],
    "trickster":   ["El Embaucador Eterno", "Hermes el Oscuro", "El Caos Primordial"],
    "rebelde":     ["El Indomable", "Prometeo el Libre", "El que Rompe Cadenas"],
    "muerte":      ["Thanatos Eterno", "El Fin de Todo", "El Umbral Primordial"],
    "nino_divino": ["El Renacido Eterno", "El Elegido Celestial", "El Niño Sagrado"],
    "anima_animus":["El Ser del Alma", "El Misterio Interior", "La Dualidad Eterna"],
    "persona":     ["El Maestro de Rostros", "El Guardián de Formas", "El Cambiante"],
    "self_":       ["El Ser Completo", "El Integrado Eterno", "El Uno"],
}

_ARCH_TO_SPHERE: dict[str, str] = {
    "heroe":       "valor_y_sacrificio",
    "sombra":      "muerte_y_oscuridad",
    "madre":       "fertilidad_y_cuidado",
    "padre":       "orden_y_legado",
    "sabio":       "conocimiento_y_tiempo",
    "gobernante":  "poder_y_justicia",
    "trickster":   "cambio_y_engaño",
    "rebelde":     "libertad_y_caos",
    "muerte":      "transición_y_umbral",
    "nino_divino": "renacimiento_y_esperanza",
    "anima_animus":"amor_y_dualidad",
    "persona":     "comunidad_e_identidad",
    "self_":       "totalidad_e_integración",
}


def _deity_name(arquetipo: str, tribe_id: str) -> str:
    epithets = _DEITY_EPITHETS.get(arquetipo, [f"El Gran {arquetipo.capitalize()}"])
    idx = abs(hash(tribe_id)) % len(epithets)
    return epithets[idx]


@dataclass
class DeityRecord:
    """
    Entidad emergente del inconsciente colectivo.
    Cristaliza cuando un arquetipo domina el ICL ≥ 30 días consecutivos,
    o cuando el mismo par mítico cristaliza por 3ª vez.
    Persiste en CulturalMemory independientemente del decaimiento del campo.
    """
    nombre:                str
    arquetipo_fundacional: str
    esfera_de_influencia:  str
    intensidad:            float
    dia_cristalizacion:    int
    tribu_origen:          str
    causa:                 str       # "icl_streak" | "myth_repeat"
    is_active:             bool = True

    def to_dict(self) -> dict:
        return {
            "nombre":                self.nombre,
            "arquetipo_fundacional": self.arquetipo_fundacional,
            "esfera_de_influencia":  self.esfera_de_influencia,
            "intensidad":            self.intensidad,
            "dia_cristalizacion":    self.dia_cristalizacion,
            "tribu_origen":          self.tribu_origen,
            "causa":                 self.causa,
            "is_active":             self.is_active,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DeityRecord:
        return cls(
            nombre                = d["nombre"],
            arquetipo_fundacional = d["arquetipo_fundacional"],
            esfera_de_influencia  = d["esfera_de_influencia"],
            intensidad            = float(d.get("intensidad", 1.0)),
            dia_cristalizacion    = int(d["dia_cristalizacion"]),
            tribu_origen          = d["tribu_origen"],
            causa                 = d.get("causa", "icl_streak"),
            is_active             = bool(d.get("is_active", True)),
        )

if TYPE_CHECKING:
    from core.agents import Agent
    from core.social.collective_field import CollectiveField

# Umbral de contexto para que nazca un proto-mito (D1 — configurable via env)
_PROTO_MYTH_THRESHOLD: float = float(os.getenv("MYTH_CONTEXT_THRESHOLD", "0.25"))

# Transmisiones sociales necesarias para cristalizar un proto-mito (D1)
_COHERENCE_TO_CRYSTALLIZE: float = 3.0

# Ganancia de coherencia por cada transmisión social
_COHERENCE_PER_TRANSMISSION: float = 1.0

# Mapa: par de símbolos dominantes → tipo de mito probable
_PAIR_TO_MYTH_TYPE: dict[frozenset, str] = {
    # Cosmogonía — origen del mundo desde la muerte y el caos
    frozenset({"muerte", "sombra"}):      "cosmogonia",
    frozenset({"muerte", "madre"}):       "cosmogonia",
    frozenset({"muerte", "heroe"}):       "cosmogonia",   # héroe sacrificado → origen
    frozenset({"muerte", "padre"}):       "cosmogonia",   # legado del anciano
    # Teogonía — emergencia de lo sagrado y el orden
    frozenset({"gobernante", "padre"}):   "teogonia",
    frozenset({"gobernante", "sabio"}):   "teogonia",     # sabiduría del poder
    frozenset({"sabio", "nino_divino"}):  "teogonia",
    frozenset({"padre", "nino_divino"}):  "teogonia",     # linaje divino
    # Antropogonía — origen del ser humano y el renacimiento
    frozenset({"madre", "nino_divino"}):  "antropogonia",
    frozenset({"madre", "heroe"}):        "antropogonia", # madre del héroe
    frozenset({"heroe", "nino_divino"}):  "antropogonia", # el niño elegido
    # Escatología — fin de los tiempos y sabiduría última
    frozenset({"muerte", "sabio"}):       "escatologia",
    frozenset({"muerte", "gobernante"}):  "escatologia",  # el rey que cae
    frozenset({"sombra", "sabio"}):       "escatologia",  # el conocimiento oscuro
    # Mito moral — conflicto entre fuerzas opuestas
    frozenset({"gobernante", "rebelde"}): "mito_moral",
    frozenset({"heroe", "sombra"}):       "mito_moral",
    frozenset({"heroe", "rebelde"}):      "mito_moral",
    frozenset({"trickster", "sombra"}):   "mito_moral",
    frozenset({"sabio", "trickster"}):    "mito_moral",
    frozenset({"padre", "rebelde"}):      "mito_moral",   # rebelión contra el orden
    frozenset({"gobernante", "sombra"}):  "mito_moral",   # tiranía
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

# R5-A1 — Plantillas de relato inicial y sufijos de distorsión por tipo de mito
_RELATO_INICIAL: dict[str, str] = {
    "cosmogonia":   "Al principio, {par0} y {par1} lucharon y de esa lucha nació el mundo.",
    "teogonia":     "Los ancestros vieron cómo {par0} recibió el don de {par1} y estableció el orden.",
    "antropogonia": "Se dice que {par0} trajo a los primeros de nuestra sangre desde el lugar de {par1}.",
    "escatologia":  "Cuando llegue el fin, {par0} y {par1} volverán a encontrarse y juzgarán a los vivos.",
    "mito_moral":   "Hubo un tiempo en que {par0} y {par1} se enfrentaron, y cada uno recibió lo que merecía.",
}

_DISTORSION_SUFIJOS: dict[str, list[str]] = {
    "heroe":      [
        " Fue el más grande guerrero que jamás vivió entre los nuestros.",
        " Ninguno antes ni después igualó su valor.",
        " Los dioses mismos temblaron ante su presencia.",
    ],
    "sabio":      [
        " Esto lo sabemos porque los ancianos lo vieron y lo transmitieron.",
        " Quien no lo crea no ha comprendido la naturaleza del tiempo.",
        " Esta verdad es más antigua que el nombre que le damos.",
    ],
    "sombra":     [
        " Pero había oscuridad en aquello que no se nombra.",
        " Lo que no se cuenta es más terrible que lo que se recuerda.",
        " Algunos morirán sin saber lo que realmente ocurrió en ese día.",
    ],
    "madre":      [
        " Y de aquella unión nació todo lo que somos.",
        " El mundo era más suave entonces, antes de que olvidáramos.",
        " La tierra lo recuerda aunque nosotros hayamos olvidado.",
    ],
    "trickster":  [
        " Pero nadie sabe si lo que se cuenta es verdad o ilusión.",
        " El que ríe en las sombras conoce la versión real.",
        " No confíes en el que dice saber todo de este mito.",
    ],
    "gobernante": [
        " Y por eso obedecemos las leyes que de aquello surgieron.",
        " El poder que vino de ese momento aún perdura entre nosotros.",
        " Quien olvide esta historia perderá el derecho de mandar.",
    ],
    "default":    [
        " Así fue, y así será siempre que alguien lo recuerde.",
        " Los que vivieron aquello nunca fueron los mismos.",
        " El tiempo ha borrado los detalles, pero la verdad permanece.",
    ],
}

_DISTORSION_RATE_BASE = 0.00015    # deriva diaria mínima (muy lenta)
_DISTORSION_THRESHOLDS = [0.25, 0.50, 0.75, 0.92]  # puntos donde el relato muta


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

    R5-A1: Los mitos se distorsionan con el tiempo. `distorsion_acumulada`
    registra cuánto ha derivado el relato del evento original. `relato_actual`
    es la versión viva (la que heredan los hijos); `name` es el nombre original.
    """
    name: str
    tipo: str
    par: tuple[str, str]
    active: bool = True
    day_crystallized: int = 0
    protagonista_id: str | None = None
    antagonista_id:  str | None = None
    es_leyenda: bool = False
    day_became_legend: int | None = None
    intensidad: float = 1.0
    tribe_id: str = ""           # D3 — tribu de origen del mito
    # R5-A1 — Distorsión transgeneracional
    distorsion_acumulada: float = 0.0   # 0.0 → 1.0 (irreconocible)
    relato_actual:        str   = ""    # Versión viva del mito (distorsionada)


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

    def __init__(self, seed: int = 0) -> None:
        self.active_myths: list[MythCrystal]       = []
        self.proto_myths:  list[ProtoMito]          = []
        self.deities:      list[DeityRecord]        = []   # Hito E
        self._pair_counts: dict[str, int]           = {}   # "arch1|arch2" → n cristalizaciones
        self._rng = random.Random(seed)

    # ── Ciclo principal ────────────────────────────────────────────────────────

    def on_day(
        self,
        field: CollectiveField,
        agents: dict[str, Agent],
        dia: int,
        local_fields: dict | None = None,
    ) -> None:
        self._check_proto_myths(field, dia)
        self._check_crystallization(field, agents, dia, local_fields)
        self.apply_myth_effects(agents)
        self._check_myth_persistence(agents, dia)
        self._distort_myths(field, agents, dia)
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
        pair_key = "|".join(sorted(par))

        # No crear proto-mito duplicado del mismo (tipo, par)
        if any(p.tipo == tipo and "|".join(sorted(p.par)) == pair_key for p in self.proto_myths):
            return

        # No duplicar si ya existe mito cristalizado con el mismo (tipo, par)
        if any(
            m.tipo == tipo and "|".join(sorted(m.par)) == pair_key
            for m in self.active_myths if m.active or m.es_leyenda
        ):
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
        local_fields: dict | None = None,
    ) -> None:
        """
        Cristaliza los proto-mitos que han alcanzado suficiente coherencia.
        """
        listos = [p for p in self.proto_myths if p.listo_para_cristalizar()]

        for proto in listos:
            self.proto_myths.remove(proto)
            crystal = self._crystallize(proto, field, agents, dia, local_fields)
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
        local_fields: dict | None = None,
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
        tmpl = _RELATO_INICIAL.get(proto.tipo, _RELATO_INICIAL["mito_moral"])
        relato = tmpl.format(
            par0=proto.par[0] if proto.par else "lo desconocido",
            par1=proto.par[1] if len(proto.par) > 1 else "el misterio",
        )
        # D3 — determinar tribu de origen: la de mayor myth_pressure local
        origin_tribe = ""
        if local_fields:
            origin_tribe = max(local_fields, key=lambda tid: local_fields[tid].myth_pressure, default="")

        crystal = MythCrystal(
            name=name,
            tipo=proto.tipo,
            par=proto.par,
            active=True,
            day_crystallized=dia,
            protagonista_id=prot_id,
            antagonista_id=antag_id,
            intensidad=min(1.0, proto.intensidad_contexto + 0.2),
            tribe_id=origin_tribe,
            relato_actual=relato,
        )
        # Hito E: registrar pares para detección de deidad por repetición
        pair_key = "|".join(sorted(proto.par))
        self._pair_counts[pair_key] = self._pair_counts.get(pair_key, 0) + 1
        return crystal

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

    def _distort_myths(
        self,
        field:  "CollectiveField",
        agents: dict[str, "Agent"],
        dia:    int,
    ) -> None:
        """
        R5-A1 — Distorsión transgeneracional de mitos.

        Cada día los mitos cristalizados acumulan distorsión proporcional a:
        - La presión mítica del campo (transmisión activa = más distorsión)
        - El arquetipo dominante del campo (sesga el tipo de sufijo añadido)

        Los umbrales de distorsión (_DISTORSION_THRESHOLDS) disparan mutaciones
        del relato_actual: el mito vivo diverge del nombre original.
        A distorsion_acumulada ≥ 0.92 el relato es irreconocible.
        """
        if not self.active_myths:
            return

        # Contadores del campo para calcular la tasa de distorsión
        n_sabios = sum(
            1 for a in agents.values()
            if a.is_alive and a.archetypes.sabio > 0.55
        )
        pressure   = field.myth_pressure
        arch_dom   = field.dominant_archetype_pair()[0] if self.active_myths else "default"

        for myth in self.active_myths:
            # Las leyendas se distorsionan más rápido (sin protagonista que "ancle" el relato)
            leyenda_factor = 1.5 if myth.es_leyenda else 1.0
            # La presión mítica y los sabios activos aceleran la transmisión oral
            rate = (_DISTORSION_RATE_BASE
                    + pressure * 0.0004
                    + n_sabios * 0.00008) * leyenda_factor

            prev  = myth.distorsion_acumulada
            myth.distorsion_acumulada = min(1.0, prev + rate)

            # Inicializar relato_actual si está vacío
            if not myth.relato_actual:
                tmpl = _RELATO_INICIAL.get(myth.tipo, _RELATO_INICIAL["mito_moral"])
                myth.relato_actual = tmpl.format(
                    par0 = myth.par[0] if myth.par else "lo desconocido",
                    par1 = myth.par[1] if len(myth.par) > 1 else "el misterio",
                )

            # Disparar mutación del relato al cruzar cada umbral
            for threshold in _DISTORSION_THRESHOLDS:
                if prev < threshold <= myth.distorsion_acumulada:
                    sufijos = _DISTORSION_SUFIJOS.get(arch_dom, _DISTORSION_SUFIJOS["default"])
                    sufijo  = self._rng.choice(sufijos)
                    myth.relato_actual = myth.relato_actual.rstrip(".") + sufijo

    def _decay_myths(self) -> None:
        """La intensidad de las leyendas decae lentamente con el tiempo."""
        for myth in self.active_myths:
            if myth.es_leyenda:
                myth.intensidad = max(0.0, myth.intensidad * 0.998)

    # ── Consultas ──────────────────────────────────────────────────────────────

    def pair_crystallization_count(self, arch1: str, arch2: str) -> int:
        """Retorna cuántas veces ha cristalizado el par de arquetipos dado."""
        key = "|".join(sorted([arch1, arch2]))
        return self._pair_counts.get(key, 0)

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
                    "name":                 m.name,
                    "tipo":                 m.tipo,
                    "par":                  list(m.par),
                    "active":               m.active,
                    "day_crystallized":     m.day_crystallized,
                    "protagonista_id":      m.protagonista_id,
                    "antagonista_id":       m.antagonista_id,
                    "es_leyenda":           m.es_leyenda,
                    "day_became_legend":    m.day_became_legend,
                    "intensidad":           m.intensidad,
                    "tribe_id":             m.tribe_id,
                    "distorsion_acumulada": m.distorsion_acumulada,
                    "relato_actual":        m.relato_actual,
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
            "deities":      [d.to_dict() for d in self.deities],
            "pair_counts":  dict(self._pair_counts),
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
                tribe_id=m.get("tribe_id", ""),
                distorsion_acumulada=m.get("distorsion_acumulada", 0.0),
                relato_actual=m.get("relato_actual", ""),
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

        for d in data.get("deities", []):
            engine.deities.append(DeityRecord.from_dict(d))

        engine._pair_counts = {
            k: int(v) for k, v in data.get("pair_counts", {}).items()
        }

        return engine

    # ── Retrocompatibilidad con código que llama check_crystallization() ───────

    def check_crystallization(
        self,
        field: CollectiveField,
        agents: dict[str, Agent],
        dia: int,
        local_fields: dict | None = None,
    ) -> None:
        """Alias mantenido para retrocompatibilidad con agent_core.py."""
        self.on_day(field, agents, dia, local_fields)
