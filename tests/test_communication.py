"""
Tests de reinterpretación del receptor (core/social/communication.py).

Verifican:
  - Agent.perceive_social_event() reutiliza InterpretiveFilter con el mismo
    contrato Capa A que el resto de la Fase 1 (Ecuación Personal): off por
    defecto, escalares en rango.
  - build_encounter_stimulus() traduce el ROL que tuvo el receptor en un
    encuentro a un Stimulus físico — sin contenido simbólico.
  - El mismo encuentro objetivo da lugar a roles con física opuesta (víctima
    vs. explotador) — la base de por qué la reinterpretación puede divergir
    aunque el hecho resuelto por InteractionEngine sea el mismo.
  - reinterpret_encounter() diverge entre psiques distintas y puede activar
    complejos del receptor.
"""
from core.agents import Agent
from core.agents.psyche.interpretive_filter import InterpretiveFilter
from core.agents.psyche.traits import TraitProfile
from core.agents.psyche.complexes import ComplexProfile
from core.social.network import SocialNetwork
from core.social.collective_field import CollectiveField
from core.social import communication


def _make_agent(agent_id="a", seed=42) -> Agent:
    """Agente con el filtro interpretativo forzado ON, sin depender del env var
    _INTERPRETIVE_FILTER_ENABLED (mismo criterio white-box que test_interpretive_filter.py)."""
    agent = Agent(agent_id, f"Test-{agent_id}", (0, 0), seed=seed)
    agent._interpretive_filter = InterpretiveFilter()
    return agent


class TestPerceiveSocialEvent:

    def test_devuelve_none_si_filtro_desactivado(self):
        agent = Agent("a", "Test", (0, 0), seed=1)
        assert agent._interpretive_filter is None  # off por defecto
        stim = communication.build_encounter_stimulus(
            "cooperacion_mutua", agent, SocialNetwork(), agent.id
        )
        result = agent.perceive_social_event(stim)
        assert result is None
        assert agent.last_perceived_event is None

    def test_produce_solo_escalares_en_rango(self):
        a = _make_agent("a")
        b = _make_agent("b")
        stim = communication.build_encounter_stimulus(
            "cooperacion_mutua", b, SocialNetwork(), a.id
        )
        pe = a.perceive_social_event(stim)
        assert pe is not None
        assert -1.0 <= pe.valence <= 1.0
        assert 0.0 <= pe.arousal <= 1.0
        assert 0.0 <= pe.relevance_to_self <= 1.0

    def test_actualiza_last_perceived_event(self):
        a = _make_agent("a")
        b = _make_agent("b")
        stim = communication.build_encounter_stimulus(
            "choque_violento", b, SocialNetwork(), a.id
        )
        pe = a.perceive_social_event(stim)
        assert a.last_perceived_event is pe


class TestBuildEncounterStimulus:

    def test_roles_opuestos_del_mismo_encuentro_tienen_polaridad_opuesta(self):
        """
        conflicto_explotacion da lugar a dos roles: la víctima ('explotado')
        y quien explota ('explotador'). El mismo encuentro objetivo debe
        producir físicas con polaridad dominante opuesta.
        """
        net = SocialNetwork()
        other = _make_agent("b")
        stim_victima = communication.build_encounter_stimulus("explotado", other, net, "a")
        stim_explotador = communication.build_encounter_stimulus("explotador", other, net, "a")
        assert stim_victima.threat > stim_victima.benefit
        assert stim_explotador.benefit > stim_explotador.threat

    def test_vinculo_previo_modula_carga_social(self):
        net = SocialNetwork()
        other = _make_agent("b")
        net.set_bond("a", "b", 0.9)
        stim_vinculado = communication.build_encounter_stimulus("cooperacion_mutua", other, net, "a")
        net.set_bond("a", "b", 0.0)
        stim_neutral = communication.build_encounter_stimulus("cooperacion_mutua", other, net, "a")
        assert stim_vinculado.social > stim_neutral.social

    def test_stimulus_no_lleva_contenido_simbolico(self):
        """Contrato Capa A: Stimulus solo tiene categorías/magnitudes físicas."""
        net = SocialNetwork()
        other = _make_agent("b")
        stim = communication.build_encounter_stimulus("choque_violento", other, net, "a")
        assert isinstance(stim.kind, str)
        assert isinstance(stim.threat, float)
        assert isinstance(stim.benefit, float)


class TestReinterpretEncounter:

    def test_devuelve_none_si_receptor_no_tiene_filtro(self):
        a = Agent("a", "Test", (0, 0), seed=1)  # sin forzar el filtro ON
        b = _make_agent("b")
        net = SocialNetwork()
        field = CollectiveField()
        pe = communication.reinterpret_encounter(a, b, "cooperacion_mutua", net, field, None)
        assert pe is None

    def test_misma_situacion_diverge_entre_psiques_distintas(self):
        """
        El corazón de la Ecuación Personal aplicado al encuentro: dos agentes
        con rasgos opuestos reinterpretan el MISMO rol de forma distinta.
        """
        net = SocialNetwork()
        field = CollectiveField()
        other = _make_agent("other")

        paranoico = _make_agent("paranoico")
        paranoico.traits = TraitProfile(paranoia=0.95, neuroticismo=0.9, estabilidad_emocional=0.1)

        sereno = _make_agent("sereno")
        sereno.traits = TraitProfile(paranoia=0.05, neuroticismo=0.1, estabilidad_emocional=0.9)

        pe_paranoico = communication.reinterpret_encounter(
            paranoico, other, "manipulado_exitosamente", net, field, None
        )
        pe_sereno = communication.reinterpret_encounter(
            sereno, other, "manipulado_exitosamente", net, field, None
        )
        assert pe_paranoico.valence < pe_sereno.valence

    def test_activa_complejos_del_receptor(self):
        """
        Ser explotado (kind='traicion') puede activar el complejo de culpa del
        receptor si su peso supera el umbral — mismo mecanismo que ya usa
        ComplexProfile para cualquier otro evento (check_activation).
        """
        a = _make_agent("a")
        a.complexes = ComplexProfile(culpa=0.90)  # sobre el umbral de activación (0.65)
        b = _make_agent("b")
        net = SocialNetwork()
        field = CollectiveField()

        communication.reinterpret_encounter(a, b, "explotado", net, field, None)
        assert "culpa" in a.complexes.activos
