"""
Tests de la Fase 1 — InterpretiveFilter (Ecuación Personal, content-free).

Verifican el contrato filosófico además del funcional:
  - El filtro solo produce ESCALARES (Capa A).
  - Los slots simbólicos (Capa B) nacen vacíos y solo se rellenan por préstamo
    de un vocabulario que YA cristalizó en el campo — nunca por un enum.
  - El mismo estímulo diverge entre psiques distintas (emergencia de divergencia).
"""
import random

from core.interface.perceived_event import PerceivedEvent, Stimulus
from core.agents.psyche.interpretive_filter import InterpretiveFilter, _VOCAB_THRESHOLD
from core.agents.psyche.archetypes import ArchetypeVector
from core.agents.psyche.traits import TraitProfile
from core.agents.quantum.superposition import BehavioralState
from core.agents.quantum.collapse import collapse_state
from core.social.collective_field import CollectiveField
from core.agents import Agent


def _make_agent(**kw) -> Agent:
    return Agent(agent_id=kw.get("id", "a1"), nombre="Test",
                 posicion=(40, 30), seed=42)


# ── PerceivedEvent: contrato Capa B vacía + action_bias content-free ────────────

class TestPerceivedEvent:

    def test_capa_b_slots_nacen_vacios(self):
        pe = PerceivedEvent(
            stimulus_type="muerte", stimulus_id="x",
            valence=-0.5, arousal=0.5, relevance_to_self=0.5,
        )
        assert pe.attributed_cause is None
        assert pe.moral_judgment is None
        assert pe.narrative_frame is None

    def test_valence_positiva_impulsa_cooperacion(self):
        pe = PerceivedEvent("recurso", "x", valence=0.8, arousal=0.6, relevance_to_self=0.7)
        bias = pe.action_bias()
        assert bias["cooperacion"] > 0.0
        assert bias["competencia"] == 0.0
        assert bias["aislamiento"] == 0.0

    def test_manipulacion_nunca_se_induce_afectivamente(self):
        for v, a in [(0.9, 0.9), (-0.9, 0.9), (-0.9, 0.1), (0.0, 0.5)]:
            pe = PerceivedEvent("x", "x", valence=v, arousal=a, relevance_to_self=0.5)
            assert pe.action_bias()["manipulacion"] == 0.0

    def test_negativo_alto_arousal_es_lucha(self):
        pe = PerceivedEvent("amenaza", "x", valence=-0.8, arousal=0.9, relevance_to_self=0.8)
        bias = pe.action_bias()
        assert bias["competencia"] > bias["aislamiento"]

    def test_negativo_bajo_arousal_es_retirada(self):
        pe = PerceivedEvent("amenaza", "x", valence=-0.8, arousal=0.1, relevance_to_self=0.8)
        bias = pe.action_bias()
        assert bias["aislamiento"] > bias["competencia"]

    def test_relevancia_amplifica(self):
        bajo = PerceivedEvent("x", "x", valence=0.8, arousal=0.6, relevance_to_self=0.0)
        alto = PerceivedEvent("x", "x", valence=0.8, arousal=0.6, relevance_to_self=1.0)
        assert alto.action_bias()["cooperacion"] > bajo.action_bias()["cooperacion"]


# ── InterpretiveFilter: solo escalares, frame por préstamo ──────────────────────

class TestInterpretiveFilter:

    def test_produce_solo_escalares_en_rango(self):
        f = InterpretiveFilter()
        agent = _make_agent()
        stim = Stimulus(kind="recurso", benefit=0.6, proximity=1.0)
        agent.needs.hambre = 0.7
        pe = f.interpret(stim, agent)
        assert -1.0 <= pe.valence <= 1.0
        assert 0.0 <= pe.arousal <= 1.0
        assert 0.0 <= pe.relevance_to_self <= 1.0
        assert all(isinstance(v, float) for v in pe.archetype_activation.values())

    def test_sin_campo_no_hay_frame(self):
        f = InterpretiveFilter()
        agent = _make_agent()
        stim = Stimulus(kind="muerte", threat=0.3, proximity=1.0)
        pe = f.interpret(stim, agent, field=None)
        assert pe.narrative_frame is None

    def test_frame_solo_si_simbolo_cristalizo(self):
        f = InterpretiveFilter()
        agent = _make_agent()
        stim = Stimulus(kind="muerte", threat=0.4, proximity=1.0)

        # Determinar qué arquetipo resuena más para este agente/estímulo.
        pe0 = f.interpret(stim, agent, field=None)
        assert pe0.archetype_activation, "kind 'muerte' debería activar resonancia"
        top = max(pe0.archetype_activation, key=pe0.archetype_activation.get)

        # Por debajo del umbral → el vocabulario aún no existe → None.
        field = CollectiveField()
        field.symbols[top] = _VOCAB_THRESHOLD - 0.1
        assert f.interpret(stim, agent, field=field).narrative_frame is None

        # Al cristalizar (carga ≥ umbral) → el agente toma prestado ese nombre.
        field.symbols[top] = _VOCAB_THRESHOLD + 0.1
        assert f.interpret(stim, agent, field=field).narrative_frame == top

    def test_misma_situacion_diverge_entre_psiques(self):
        """El corazón filosófico: dos psiques distintas interpretan distinto."""
        f = InterpretiveFilter()
        stim = Stimulus(kind="agente", social=1.0, proximity=1.0)

        amable = _make_agent(id="amable")
        amable.traits = TraitProfile(amabilidad=0.95, extraversion=0.9, empatia=0.9)

        hostil = _make_agent(id="hostil")
        hostil.traits = TraitProfile(amabilidad=0.05, extraversion=0.2, paranoia=0.8)

        # Para aislar el efecto de los rasgos, ambos en el mismo estado (sin ansiedad).
        amable.ansiedad = hostil.ansiedad = 0.0
        pe_amable = f.interpret(stim, amable)
        pe_hostil = f.interpret(stim, hostil)

        # Mismo estímulo físico, valence subjetiva distinta.
        assert pe_amable.valence > pe_hostil.valence

    def test_ansiedad_tine_la_valencia_negativamente(self):
        # Apraisal dependiente de estado: el MISMO estímulo se aprecia peor cuando el
        # agente ya está ansioso. Es lo que permite que la misma categoría se sienta a
        # veces bien y a veces mal → ambivalencia → neurosis emergente.
        f = InterpretiveFilter()
        stim = Stimulus(kind="neutro", proximity=1.0)
        sereno = _make_agent(id="sereno"); sereno.ansiedad = 0.0
        ansioso = _make_agent(id="ansioso"); ansioso.ansiedad = 0.9
        v_sereno = f.interpret(stim, sereno).valence
        v_ansioso = f.interpret(stim, ansioso).valence
        assert v_ansioso < v_sereno
        assert v_ansioso < 0.0


# ── collapse_state: el canal interpretativo modula el colapso ───────────────────

class TestCollapseIntegration:

    def _frequencies(self, interp, n=4000):
        rng = random.Random(7)
        state = BehavioralState()
        counts = {"cooperacion": 0, "competencia": 0, "aislamiento": 0, "manipulacion": 0}
        for _ in range(n):
            r = collapse_state(
                state=state, context={},
                archetype_biases={}, complex_biases={}, trait_biases={},
                interpretive_influence=interp, rng=rng,
            )
            counts[r] += 1
        return counts

    def test_interpretive_influence_desplaza_distribucion(self):
        base = self._frequencies(None)
        push_comp = self._frequencies({"competencia": 1.0})
        assert push_comp["competencia"] > base["competencia"]

    def test_sin_influencia_es_inocuo(self):
        # interpretive_influence=None no debe romper ni alterar el contrato.
        rng = random.Random(1)
        r = collapse_state(
            state=BehavioralState(), context={},
            archetype_biases={}, complex_biases={}, trait_biases={},
            interpretive_influence=None, rng=rng,
        )
        assert r in ("cooperacion", "competencia", "aislamiento", "manipulacion")


# ── Agent: cableado y flag ──────────────────────────────────────────────────────

class TestAgentWiring:

    def test_filtro_desactivado_por_defecto(self):
        # Sin el flag de entorno, el agente no instancia filtro (reproducibilidad intacta).
        a = _make_agent()
        assert a._interpretive_filter is None
        assert a.last_perceived_event is None

    def test_build_stimulus_es_fisico(self):
        a = _make_agent()

        class _Snap:
            survival_risk = 0.0
            catastrofe_activa = None
            evento_climatico = None
            dia = 3
            recursos_por_hex = {(40, 30): {"frutos": 0.5}}
            fauna_visible = {}
            graves_activos = []

        stim = a._build_stimulus(_Snap(), hay_aliados=False)
        assert stim.kind in ("recurso", "neutro", "agente", "amenaza", "muerte", "clima_extremo")
        assert 0.0 <= stim.threat <= 1.0
        assert 0.0 <= stim.benefit <= 1.0
