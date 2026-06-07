"""
Tests del MentalVault (Ecuación Personal, Fase 2).

Cubren el contrato del roadmap v2: enlazado por la física de colapso (no por reglas),
resonancia arquetípica EMERGENTE (slots None salvo préstamo del campo), modulación por
fase de vida, feedback acotado, serialización, y el canal de ruido en el colapso.
"""
import random

import pytest

from core.agents.mental_vault import MentalVault, Neuron, neuron_id
from core.interface.perceived_event import PerceivedEvent
from core.social.collective_field import CollectiveField
from core.agents.quantum.collapse import collapse_state
from core.agents.quantum.superposition import BehavioralState, BEHAVIORAL_STATES


def _pe(kind, valence=0.5, arousal=0.8, relevance=0.8, activation=None):
    return PerceivedEvent(
        stimulus_type        = kind,
        stimulus_id          = f"{kind}@0,0",
        valence              = valence,
        arousal              = arousal,
        relevance_to_self    = relevance,
        archetype_activation = activation or {},
    )


# ── Creación y refuerzo ────────────────────────────────────────────────────────

def test_neurona_se_crea_y_refuerza():
    nid = neuron_id("recurso", 0.5)
    mv = MentalVault()
    mv.accumulate(_pe("recurso"))
    mv.consolidate(field=None, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    assert nid in mv.neurons
    energia_1 = mv.neurons[nid].estado_energetico

    # Re-activar la misma categoría sube la energía por encima del decay.
    mv.accumulate(_pe("recurso"))
    mv.consolidate(field=None, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    assert mv.neurons[nid].estado_energetico > energia_1 * 0.92


def test_consolidar_sin_eventos_es_solo_decay():
    nid = neuron_id("amenaza", 0.5)
    mv = MentalVault()
    mv.accumulate(_pe("amenaza"))
    mv.consolidate(field=None, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    e0 = mv.neurons[nid].estado_energetico
    # Día sin eventos: la energía solo decae, no crece.
    mv.consolidate(field=None, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    assert mv.neurons[nid].estado_energetico == pytest.approx(e0 * 0.92, rel=1e-6)


# ── Enlazado por umbral + azar (no por reglas) ─────────────────────────────────

def test_enlazado_es_estocastico_y_reproducible():
    def run(seed):
        mv = MentalVault()
        for k in ("recurso", "amenaza", "agente", "muerte"):
            mv.accumulate(_pe(k))
        mv.consolidate(field=None, fase_desarrollo="adulto", ansiedad=0.3, rng=random.Random(seed))
        return {nid: dict(n.enlaces) for nid, n in mv.neurons.items()}

    # Misma semilla → misma estructura de enlaces (reproducible).
    assert run(123) == run(123)


def test_ninez_genera_al_menos_tantos_enlaces_como_adulto():
    # La niñez sube la temperatura del colapso (factor 1.5): con la MISMA secuencia de
    # azar, todo enlace que ocurre en adulto ocurre también en niñez.
    def count_links(fase):
        mv = MentalVault()
        for k in ("recurso", "amenaza", "agente", "muerte", "clima_extremo"):
            mv.accumulate(_pe(k, arousal=0.6))
        mv.consolidate(field=None, fase_desarrollo=fase, ansiedad=0.3, rng=random.Random(7))
        return sum(len(n.enlaces) for n in mv.neurons.values())

    assert count_links("niñez") >= count_links("adulto")


# ── Resonancia arquetípica EMERGENTE (test filosófico Capa A/B) ────────────────

def test_arquetipo_resonante_nace_None_sin_vocabulario():
    nid = neuron_id("muerte", 0.5)
    mv = MentalVault()
    mv.accumulate(_pe("muerte", activation={"heroe": 0.5}))
    field = CollectiveField()  # campo vacío: símbolos en 0.0
    mv.consolidate(field=field, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    # El símbolo no cristalizó → el agente siente pero NO nombra.
    assert mv.neurons[nid].arquetipo_resonante is None


def test_arquetipo_resonante_emerge_si_el_simbolo_cristalizo():
    nid = neuron_id("muerte", 0.5)
    mv = MentalVault()
    mv.accumulate(_pe("muerte", activation={"heroe": 0.5}))
    field = CollectiveField()
    field.symbols["heroe"] = 0.60  # ya cristalizó (≥ umbral 0.55)
    mv.consolidate(field=field, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    # Solo ahora puede tomar prestado el nombre del campo.
    assert mv.neurons[nid].arquetipo_resonante == "heroe"


def test_resonancia_se_apaga_si_el_simbolo_decae_bajo_umbral():
    nid = neuron_id("muerte", 0.5)
    mv = MentalVault()
    mv.accumulate(_pe("muerte", activation={"heroe": 0.5}))
    field = CollectiveField()
    field.symbols["heroe"] = 0.60
    mv.consolidate(field=field, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    assert mv.neurons[nid].arquetipo_resonante == "heroe"
    # El símbolo colectivo se enfría por debajo del umbral → el nombre se pierde.
    field.symbols["heroe"] = 0.40
    mv.consolidate(field=field, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    assert mv.neurons[nid].arquetipo_resonante is None


# ── Decay + pruning ────────────────────────────────────────────────────────────

def test_pruning_respeta_el_cap():
    mv = MentalVault()
    for i in range(60):
        mv.accumulate(_pe(f"cat_{i}"))
    mv.consolidate(field=None, fase_desarrollo="adulto", ansiedad=0.2, rng=random.Random(0))
    assert len(mv.neurons) <= 50


# ── Feedback a la psique ───────────────────────────────────────────────────────

def test_feedback_deltas_acotados_y_ruido_en_rango():
    mv = MentalVault()
    field = CollectiveField()
    field.symbols["heroe"] = 0.70
    for _ in range(5):
        mv.accumulate(_pe("recurso", activation={"heroe": 0.5}))
    fb = mv.consolidate(field=field, fase_desarrollo="adulto", ansiedad=0.4, rng=random.Random(0))
    for delta in fb["archetype_deltas"].values():
        assert 0.0 <= delta <= 0.03
    assert 0.0 <= fb["ruido"] <= 0.5


def test_creencias_opuestas_se_enlazan_entre_dias_y_activan_neurosis():
    # Día 1: una percepción positiva ("recurso"). Día 2: una negativa ("amenaza").
    # La neurona del día 1 sigue caliente → se enlaza con la del día 2. Tonos opuestos
    # → incoherencia → ruido > 0 (el canal de neurosis, antes muerto, ahora emerge).
    pos = neuron_id("recurso", 0.7)
    neg = neuron_id("amenaza", -0.7)
    mv = MentalVault()
    mv.accumulate(_pe("recurso", valence=0.7))
    mv.consolidate(field=None, fase_desarrollo="niñez", ansiedad=0.5, rng=random.Random(3))
    mv.accumulate(_pe("amenaza", valence=-0.7))
    fb = mv.consolidate(field=None, fase_desarrollo="niñez", ansiedad=0.5, rng=random.Random(3))

    assert neg in mv.neurons[pos].enlaces  # el enlace cruzó el día
    assert mv.worldview_coherence() < 1.0              # creencias en tensión
    assert fb["ruido"] > 0.0                            # la neurosis modula el colapso


def test_worldview_coherence_baja_con_enlaces_contradictorios():
    mv = MentalVault()
    # Dos neuronas con tono afectivo OPUESTO, enlazadas a mano.
    a = Neuron(id="a", significante="a", carga_afectiva=0.8, enlaces={"b": 0.5})
    b = Neuron(id="b", significante="b", carga_afectiva=-0.8, enlaces={"a": 0.5})
    mv.neurons = {"a": a, "b": b}
    assert mv.worldview_coherence() < 1.0
    # Sin enlaces: no hay contradicción posible.
    assert MentalVault().worldview_coherence() == 1.0


# ── Serialización ──────────────────────────────────────────────────────────────

def test_round_trip_serializacion():
    mv = MentalVault()
    field = CollectiveField()
    field.symbols["heroe"] = 0.60
    for k in ("recurso", "amenaza", "muerte"):
        mv.accumulate(_pe(k, activation={"heroe": 0.4}))
    mv.consolidate(field=field, fase_desarrollo="adulto", ansiedad=0.3, rng=random.Random(1))

    restored = MentalVault.from_dict(mv.to_dict())
    assert set(restored.neurons) == set(mv.neurons)
    for nid, n in mv.neurons.items():
        r = restored.neurons[nid]
        assert r.estado_energetico == pytest.approx(n.estado_energetico)
        assert r.carga_afectiva == pytest.approx(n.carga_afectiva)
        assert r.enlaces == n.enlaces
        assert r.arquetipo_resonante == n.arquetipo_resonante


# ── Canal de ruido en el colapso ───────────────────────────────────────────────

def test_noise_cero_no_cambia_el_colapso():
    # noise=0.0 (default) debe dar el mismo resultado que no pasarlo.
    biases = {a: 0.0 for a in BEHAVIORAL_STATES}
    r1 = collapse_state(BehavioralState(), {}, biases, biases, biases, rng=random.Random(42))
    r2 = collapse_state(BehavioralState(), {}, biases, biases, biases, noise=0.0, rng=random.Random(42))
    assert r1 == r2


def test_noise_alto_aplana_hacia_uniforme():
    # Con un sesgo fuerte hacia 'cooperacion' pero noise=1.0, la decisión se aproxima a
    # la uniforme (la incoherencia interna mete entropía).
    strong = {"cooperacion": 5.0, "competencia": 0.0, "aislamiento": 0.0, "manipulacion": 0.0}
    zero   = {a: 0.0 for a in BEHAVIORAL_STATES}
    counts = {a: 0 for a in BEHAVIORAL_STATES}
    rng = random.Random(0)
    for _ in range(4000):
        accion = collapse_state(BehavioralState(), {}, strong, zero, zero, noise=1.0, rng=rng)
        counts[accion] += 1
    # Ninguna acción debería acaparar: con uniforme cada una ~25% (1000/4000).
    assert max(counts.values()) < 1500
