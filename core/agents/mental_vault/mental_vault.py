"""
MentalVault — el mini cerebro por agente (Ecuación Personal, Fase 2).

El insight del roadmap v2: no se construye un motor distinto para el individuo. Se
**recursa el mismo motor de emergencia hacia abajo**. Las neuronas se enlazan por la
MISMA física de cristalización que usa el CollectiveField (ContextoEnunciativo →
probabilidad_cristalizacion), pero a escala individual y una vez por día.

NO hay árbol de reglas psicodinámicas (MiniEllo/MiniSuperyo/MiniYo), ni clasificador
que *asigne* arquetipos. Solo: fluctuación → resonancia → umbral → colapso. El
arquetipo de una neurona EMERGE de a qué símbolo colectivo —ya cristalizado— resuena;
si el campo aún no tiene ese símbolo, queda None.

Las etapas del desarrollo (niñez/adolescencia/adulto) NO son compuertas: modulan la
temperatura del colapso (ruido/umbral), reutilizando la fase de vida que el agente ya
tiene. Capa A legítima: estructura que modula, no contenido inyectado.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from core.social.collective_field import ContextoEnunciativo

if TYPE_CHECKING:
    import random
    from core.interface.perceived_event import PerceivedEvent
    from core.social.collective_field import CollectiveField

from .neuron import Neuron


def neuron_id(significante: str, valence: float) -> str:
    """
    Clave de neurona = categoría física + signo de la valencia. Separar por signo es lo
    que permite la AMBIVALENCIA: la misma categoría sentida a veces bien (+) y a veces
    mal (−) crea dos neuronas que pueden coexistir y entrar en tensión. Sin esto, la
    carga se promedia a ~0 y la incoherencia (neurosis) nunca emerge. Content-free: solo
    el signo de un escalar de Capa A, ningún símbolo del diseñador.
    """
    return f"{significante}:{'p' if valence >= 0.0 else 'n'}"

# Umbral de vocabulario: un símbolo del campo cuenta como "cristalizado" (disponible
# para que una neurona lo tome como arquetipo_resonante) a partir de esta carga.
# Mismo criterio que el préstamo de frame del InterpretiveFilter (Fase 1).
_VOCAB_THRESHOLD = 0.55

_CAP_NEURONAS    = 50      # techo de neuronas; se podan las de menor energía
_DECAY_FACTOR    = 0.92    # decaimiento diario de energía
_MIN_ENERGY      = 0.02    # por debajo de esto la neurona se olvida
_LINK_WEIGHT     = 0.10    # incremento de peso por enlace exitoso
# Una neurona sigue "caliente" (candidata a enlazarse con lo nuevo) mientras su energía
# supere esto. Enlazar lo percibido hoy con lo latente —no solo con lo del mismo día—
# permite que creencias de signo opuesto entren en tensión: la incoherencia EMERGE.
_LINK_ACTIVE_THRESHOLD = 0.20
_MAX_ARCH_DELTA  = 0.03    # tope de feedback diario a un arquetipo (como sueños/sustancias)

# Moduladores de la temperatura del colapso por fase de vida (ruido/plasticidad).
# Niñez: símbolos inestables (más enlaces efímeros). Adulto: worldview más coherente.
_FASE_FACTOR = {
    "niñez":        1.5,   # ruido alto, umbral bajo → más enlaces
    "adolescencia": 1.0,
    "adulto":       0.7,   # ruido bajo, energía estable → menos enlaces
}


class MentalVault:
    """Sustrato mental de un agente. Instanciado por agente; ≤ _CAP_NEURONAS neuronas."""

    def __init__(self) -> None:
        self.neurons: dict[str, Neuron] = {}
        # Registros livianos acumulados del día (se vacían al consolidar).
        self._day_records: list[dict] = []

    # ── Acumulación por tick (barata, O(1)) ───────────────────────────────────

    def accumulate(self, pe: "PerceivedEvent") -> None:
        """
        Guarda la carga escalar de un PerceivedEvent para consolidar al fin del día.
        Content-free: solo escalares de Capa A. No crea enlaces aquí.
        """
        self._day_records.append({
            "significante": pe.stimulus_type,
            "valence":      pe.valence,
            "arousal":      pe.arousal,
            "intensity":    pe.intensity(),
            "activation":   dict(pe.archetype_activation),
        })

    # ── Consolidación diaria (el colapso, no el arbitraje) ────────────────────

    def consolidate(
        self,
        field:           "CollectiveField | None",
        fase_desarrollo: str,
        ansiedad:        float,
        rng:             "random.Random",
    ) -> dict:
        """
        Corre una vez por día simulado. Devuelve feedback para la psique:
            {"archetype_deltas": {arq: delta acotado}, "ruido": float}

        Pasos (los del roadmap v2):
          1. Crear/reforzar neuronas con los eventos del día.
          2. Enlazado por resonancia (física de CollectiveField, local).
          3. Resonancia arquetípica emergente (préstamo del campo, gated por umbral).
          4. Decay + pruning.
        """
        records = self._day_records
        self._day_records = []

        # ── 1. Crear/reforzar ─────────────────────────────────────────────────
        touched: list[Neuron] = []
        for rec in records:
            nid = neuron_id(rec["significante"], rec["valence"])
            neuron = self.neurons.get(nid)
            if neuron is None:
                neuron = Neuron(id=nid, significante=rec["significante"])
                self.neurons[nid] = neuron
            # Energía sube con la intensidad del evento.
            neuron.estado_energetico = min(1.0, neuron.estado_energetico + rec["intensity"])
            # Tono afectivo: media móvil exponencial hacia la valence del evento.
            neuron.carga_afectiva = max(-1.0, min(1.0,
                0.7 * neuron.carga_afectiva + 0.3 * rec["valence"]))
            # Acumular activación arquetípica (insumo para la resonancia emergente).
            for arch, delta in rec["activation"].items():
                neuron.resonance_accum[arch] = neuron.resonance_accum.get(arch, 0.0) + delta
            if neuron not in touched:
                touched.append(neuron)

        # ── 2. Enlazado por resonancia (la misma física, a escala individual) ──
        # Candidatos = lo percibido hoy ∪ lo que sigue "caliente" en la mente. Enlazar lo
        # nuevo con lo latente (no solo con lo del mismo día) es lo que permite que
        # creencias de signo opuesto se conecten y entren en tensión → la incoherencia
        # (neurosis) emerge. Sigue siendo umbral + azar, igual que un mito. Sin reglas.
        if touched and records:
            cand_map = {n.id: n for n in self.neurons.values()
                        if n.estado_energetico >= _LINK_ACTIVE_THRESHOLD}
            for n in touched:
                cand_map[n.id] = n
            candidates = cand_map

            if len(candidates) >= 2:
                arousal_dia = sum(r["arousal"] for r in records) / len(records)
                energia_cand = sum(n.estado_energetico for n in candidates.values()) / len(candidates)
                fase_factor = _FASE_FACTOR.get(fase_desarrollo, 1.0)

                ctx = ContextoEnunciativo(
                    temperatura_semantica = min(1.0, arousal_dia),
                    intencionalidad       = min(1.0, energia_cand),
                    # La niñez sube el ruido (umbral efectivo más bajo); el adulto lo baja.
                    ruido_ambiental       = min(1.0, ansiedad * fase_factor),
                )
                prob = min(1.0, ctx.probabilidad_cristalizacion() * fase_factor)

                # Pares no ordenados: cada neurona nueva con cada candidato. Orden
                # determinista (sorted) → reproducible con la misma semilla.
                touched_ids = [n.id for n in touched]
                pairs: set = set()
                for a_id in touched_ids:
                    for b_id in candidates:
                        if a_id != b_id:
                            pairs.add(tuple(sorted((a_id, b_id))))

                for id_a, id_b in sorted(pairs):
                    if rng.random() < prob:
                        na, nb = candidates[id_a], candidates[id_b]
                        na.enlaces[id_b] = min(1.0, na.enlaces.get(id_b, 0.0) + _LINK_WEIGHT)
                        nb.enlaces[id_a] = min(1.0, nb.enlaces.get(id_a, 0.0) + _LINK_WEIGHT)

        # ── 3. Resonancia arquetípica emergente (préstamo, gated por umbral) ───
        if field is not None:
            for neuron in self.neurons.values():
                if not neuron.resonance_accum:
                    continue
                top_arch = max(neuron.resonance_accum, key=neuron.resonance_accum.get)
                charge = field.symbols.get(top_arch, 0.0)
                # Solo nombra si el símbolo YA cristalizó en el campo. Si no, None.
                neuron.arquetipo_resonante = top_arch if charge >= _VOCAB_THRESHOLD else None

        # ── 4. Decay + pruning ─────────────────────────────────────────────────
        for neuron in self.neurons.values():
            neuron.estado_energetico *= _DECAY_FACTOR
        # Olvido: neuronas casi apagadas (y sin enlaces que las sostengan).
        self.neurons = {
            nid: n for nid, n in self.neurons.items()
            if n.estado_energetico >= _MIN_ENERGY or n.enlaces
        }
        # Poda por techo: descartar las de menor energía.
        if len(self.neurons) > _CAP_NEURONAS:
            keep = sorted(self.neurons.values(),
                          key=lambda n: n.estado_energetico, reverse=True)[:_CAP_NEURONAS]
            self.neurons = {n.id: n for n in keep}

        return {
            "archetype_deltas": self._compute_archetype_feedback(),
            "ruido":            self._compute_ruido(),
        }

    # ── Feedback a la psique ───────────────────────────────────────────────────

    def _compute_archetype_feedback(self) -> dict[str, float]:
        """
        Las neuronas de alta energía con arquetipo_resonante refuerzan *levemente*
        ese arquetipo. Deltas acotados (mismo patrón que sueños/sustancias).
        """
        deltas: dict[str, float] = {}
        for neuron in self.neurons.values():
            arch = neuron.arquetipo_resonante
            if arch is None:
                continue
            deltas[arch] = deltas.get(arch, 0.0) + 0.01 * neuron.estado_energetico
        # Tope por arquetipo.
        return {a: min(_MAX_ARCH_DELTA, d) for a, d in deltas.items()}

    def _compute_ruido(self) -> float:
        """
        Incoherencia interna → más entropía en el colapso conductual (la "neurosis"
        emerge, no se programa). Mide la fracción de enlaces que unen neuronas con
        tono afectivo OPUESTO (creencias en tensión sin resolver).
        """
        return max(0.0, min(0.5, (1.0 - self.worldview_coherence()) * 0.5))

    def worldview_coherence(self) -> float:
        """
        1.0 = enlaces consistentes (dogmatismo); baja = fragmentación/neurosis.
        Sin enlaces → 1.0 (no hay contradicciones todavía).
        """
        total = 0
        contradictorios = 0
        for neuron in self.neurons.values():
            for other_id, peso in neuron.enlaces.items():
                other = self.neurons.get(other_id)
                if other is None or peso <= 0.0:
                    continue
                total += 1
                if neuron.carga_afectiva * other.carga_afectiva < 0:
                    contradictorios += 1
        if total == 0:
            return 1.0
        return 1.0 - contradictorios / total

    # ── Serialización ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {"neurons": [n.to_dict() for n in self.neurons.values()]}

    @classmethod
    def from_dict(cls, data: dict) -> "MentalVault":
        mv = cls()
        for nd in data.get("neurons", []):
            n = Neuron.from_dict(nd)
            mv.neurons[n.id] = n
        return mv
