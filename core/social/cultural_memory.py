from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents import Agent

_MAX_RECORDS = 30

# Epítetos arquetípicos que el transmisor proyecta sobre el protagonista (identificación)
_EPITHETS: dict[str, list[str]] = {
    "heroe":        ["el valiente", "el guerrero", "el campeón de la tribu"],
    "sabio":        ["el anciano sabio", "el vidente", "el que conoce el camino"],
    "madre":        ["la gran madre", "la nutricia", "la que protege"],
    "padre":        ["el patriarca", "el guía", "el fundador"],
    "sombra":       ["el oscuro", "el temido", "quien vive en las sombras"],
    "trickster":    ["el astuto", "el engañador", "quien burla al destino"],
    "gobernante":   ["el señor", "el jefe", "quien ordena a todos"],
    "rebelde":      ["el indomable", "quien no se dobla", "el libre"],
    "anima_animus": ["el misterioso", "el ser del alma", "quien cambia de forma"],
    "nino_divino":  ["el niño sagrado", "el renacido", "el portador de esperanza"],
    "persona":      ["el respetado", "el de muchas caras", "a quien todos conocen"],
    "self_":        ["el completo", "quien se conoce a sí mismo", "el integrado"],
}

_AMP_SUFFIXES = [
    " Fue un momento que cambió el destino de los nuestros para siempre.",
    " Nadie que lo vivió lo olvidó en toda su vida.",
    " Las generaciones venideras sentirán aún su peso.",
    " El eco de aquel día resonó en sueños durante generaciones.",
    " Nada volvió a ser igual desde entonces.",
]

_MORAL_ADDENDA: dict[str, str] = {
    "muerte":         "Así supimos que la muerte llega sin pedir permiso.",
    "nacimiento":     "Así supimos que la vida siempre encuentra el camino.",
    "deshidratacion": "Así supimos que el agua es más sagrada que el oro.",
    "vejez":          "Así supimos que el tiempo devora incluso a los más grandes.",
    "inanicion":      "Así supimos que la tierra exige respeto o cobra su precio.",
    "orfandad":       "Así supimos que ningún niño debe caminar solo.",
    "default":        "Así supimos que el destino no puede ser evitado.",
}

_SIMP_PREFIXES = [
    "Se dice que ", "Los ancianos cuentan que ",
    "Es sabido entre nosotros que ", "La tradición recuerda que ",
    "Según los que vivieron, ",
]

_UPDATE_FRAMES = [
    "Como {agente} en los tiempos de los abuelos, ",
    "Recordando a {agente}, la tribu sabe que ",
    "Siguiendo los pasos de {agente}, aprendimos que ",
    "En honor a {agente}, todavía recordamos que ",
]


@dataclass
class TransmissionRecord:
    """Registro de un evento real que entra al sistema de memoria cultural tribal."""
    event_id:             str
    dia_origen:           int
    agente_origen:        str
    arquetipo_origen:     str
    tipo_evento:          str
    descripcion_original: str
    descripcion_actual:   str
    intensidad_emocional: float
    n_transmisiones:      int = 0
    transmisores:         list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event_id":             self.event_id,
            "dia_origen":           self.dia_origen,
            "agente_origen":        self.agente_origen,
            "arquetipo_origen":     self.arquetipo_origen,
            "tipo_evento":          self.tipo_evento,
            "descripcion_original": self.descripcion_original,
            "descripcion_actual":   self.descripcion_actual,
            "intensidad_emocional": self.intensidad_emocional,
            "n_transmisiones":      self.n_transmisiones,
            "transmisores":         list(self.transmisores),
        }

    @classmethod
    def from_dict(cls, d: dict) -> TransmissionRecord:
        return cls(
            event_id             = d["event_id"],
            dia_origen           = d["dia_origen"],
            agente_origen        = d["agente_origen"],
            arquetipo_origen     = d["arquetipo_origen"],
            tipo_evento          = d["tipo_evento"],
            descripcion_original = d["descripcion_original"],
            descripcion_actual   = d["descripcion_actual"],
            intensidad_emocional = float(d["intensidad_emocional"]),
            n_transmisiones      = d.get("n_transmisiones", 0),
            transmisores         = list(d.get("transmisores", [])),
        )


class DistortionEngine:
    """
    Aplica una de las 5 transformaciones narrativas en cada acto de transmisión.
    La distorsión es acumulativa e irreversible: el texto original nunca se restaura.

    Tipos:
      simplificacion — elimina detalle, deja el núcleo
      amplificacion  — exagera intensidad y consecuencias
      moralizacion   — agrega lección moral al evento
      identificacion — el transmisor proyecta su arquetipo sobre el protagonista
      actualizacion  — enmarca el pasado como modelo para el presente
    """

    def distort(
        self,
        record:               TransmissionRecord,
        transmisor_nombre:    str,
        transmisor_arquetipo: str,
        rng:                  random.Random,
    ) -> None:
        """Modifica record.descripcion_actual in-place y actualiza contadores."""
        n = record.n_transmisiones
        # Los primeros actos de transmisión tienden a simplificar/amplificar;
        # los tardíos, a moralizar e identificar
        if n < 3:
            weights = [0.40, 0.30, 0.10, 0.10, 0.10]
        elif n < 8:
            weights = [0.20, 0.25, 0.25, 0.20, 0.10]
        else:
            weights = [0.10, 0.15, 0.30, 0.35, 0.10]

        tipos = ["simplificacion", "amplificacion", "moralizacion", "identificacion", "actualizacion"]
        tipo = rng.choices(tipos, weights=weights, k=1)[0]

        desc  = record.descripcion_actual
        agente = record.agente_origen

        if tipo == "simplificacion":
            prefix = rng.choice(_SIMP_PREFIXES)
            words  = desc.split()
            core   = " ".join(words[:min(10, len(words))])
            if not core.endswith("."):
                core += "."
            desc = prefix + core[0].lower() + core[1:]

        elif tipo == "amplificacion":
            already = any(k in desc for k in ["para siempre", "generacion", "olvidó", "igual"])
            if not already:
                desc = desc.rstrip(".") + rng.choice(_AMP_SUFFIXES)

        elif tipo == "moralizacion":
            addendum = _MORAL_ADDENDA.get(record.tipo_evento, _MORAL_ADDENDA["default"])
            if addendum not in desc:
                desc = desc.rstrip(".") + ". " + addendum

        elif tipo == "identificacion":
            epithets = _EPITHETS.get(transmisor_arquetipo, [agente])
            epithet  = rng.choice(epithets)
            if agente in desc:
                desc = desc.replace(agente, epithet, 1)
            # El arquetipo del recuerdo también se distorsiona
            record.arquetipo_origen = transmisor_arquetipo

        elif tipo == "actualizacion":
            frame = rng.choice(_UPDATE_FRAMES).format(agente=agente)
            first_sentence = desc.split(".")[0].strip()
            desc  = frame + first_sentence[0].lower() + first_sentence[1:] + "."

        record.descripcion_actual = desc
        record.n_transmisiones   += 1
        if transmisor_nombre not in record.transmisores:
            record.transmisores.append(transmisor_nombre)

        # Amplificación sube intensidad emocional; simplificación la baja levemente
        if tipo == "amplificacion":
            record.intensidad_emocional = min(1.0, record.intensidad_emocional + 0.05)
        elif tipo == "simplificacion":
            record.intensidad_emocional = max(0.10, record.intensidad_emocional - 0.03)


class CulturalMemory:
    """
    Memoria cultural colectiva de una tribu.

    Acumula eventos históricos (muertes, nacimientos, hazañas) que se distorsionan
    con cada acto de transmisión oral. Los hijos heredan la versión actual distorsionada,
    no los hechos originales, y su perfil arquetípico inicial se ve influido por ella.
    """

    def __init__(self, tribe_id: str) -> None:
        self.tribe_id  = tribe_id
        self.records:  list[TransmissionRecord] = []
        self._distort  = DistortionEngine()
        self._rng      = random.Random()

    # ── Ingesta de eventos ────────────────────────────────────────────────────

    def record_event(
        self,
        dia:                 int,
        agente_nombre:       str,
        arquetipo_dominante: str,
        tipo_evento:         str,
        descripcion:         str,
        intensidad:          float,
    ) -> None:
        rec = TransmissionRecord(
            event_id             = str(uuid.uuid4())[:8],
            dia_origen           = dia,
            agente_origen        = agente_nombre,
            arquetipo_origen     = arquetipo_dominante,
            tipo_evento          = tipo_evento,
            descripcion_original = descripcion,
            descripcion_actual   = descripcion,
            intensidad_emocional = max(0.0, min(1.0, intensidad)),
        )
        self.records.append(rec)
        # Si se supera el límite, descartar los de menor intensidad emocional
        if len(self.records) > _MAX_RECORDS:
            self.records.sort(key=lambda r: r.intensidad_emocional)
            excess = len(self.records) - _MAX_RECORDS
            self.records = self.records[excess:]

    # ── Transmisión diaria ────────────────────────────────────────────────────

    def daily_transmission(self, tribe_agents: dict[str, Agent]) -> None:
        """
        Agentes con alta extroversión o arquetipo sabio transmiten y distorsionan
        uno o más registros cada día.
        """
        if not self.records:
            return

        for agent in tribe_agents.values():
            if not agent.is_alive or agent.es_infante:
                continue

            arch = agent.archetypes.dominant()
            es_sabio        = arch == "sabio" and agent.archetypes.sabio > 0.45
            es_extrovertido = agent.traits.extraversion > 0.60

            if es_sabio and es_extrovertido:
                prob = 0.25
            elif es_sabio or es_extrovertido:
                prob = 0.12
            else:
                prob = 0.04

            if self._rng.random() >= prob:
                continue

            weights = [r.intensidad_emocional for r in self.records]
            record  = self._rng.choices(self.records, weights=weights, k=1)[0]
            arch_norm = "self_" if arch == "self" else arch
            self._distort.distort(
                record               = record,
                transmisor_nombre    = agent.nombre,
                transmisor_arquetipo = arch_norm,
                rng                  = self._rng,
            )

    # ── Herencia ──────────────────────────────────────────────────────────────

    def get_inheritance_effects(self) -> dict[str, float]:
        """
        Calcula el empuje arquetípico neto que la memoria transmite al nacer.
        Devuelve {arch_attr: delta} para aplicar al vector arquetípico del recién nacido.
        """
        effects: dict[str, float] = {}
        for rec in self.records:
            if rec.intensidad_emocional < 0.5:
                continue
            attr = "self_" if rec.arquetipo_origen == "self" else rec.arquetipo_origen
            # Más transmisiones = más peso en la herencia cultural
            weight = rec.intensidad_emocional * min(1.0, rec.n_transmisiones * 0.05 + 0.10)
            effects[attr] = effects.get(attr, 0.0) + weight * 0.03
        # Acotar para no distorsionar el arquetipo del hijo demasiado
        return {k: min(v, 0.10) for k, v in effects.items()}

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "tribe_id": self.tribe_id,
            "records":  [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, data: dict) -> CulturalMemory:
        cm = cls(tribe_id=data.get("tribe_id", "unknown"))
        cm.records = [TransmissionRecord.from_dict(r) for r in data.get("records", [])]
        return cm
