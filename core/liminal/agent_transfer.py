"""
core/liminal/agent_transfer.py — Manejo de transferencia de agentes al liminal.

Detecta agentes sobre el portal, los marca como in_liminal=True y
dispara el envío al servidor. También procesa los eventos entrantes del servidor.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.time import TimePoint

if TYPE_CHECKING:
    from core.agents.agent import Agent
    from core.agents.agent_core import AgentCore
    from core.liminal.liminal_client import LiminalClient
    from core.liminal.portal_hex import PortalHex

logger = logging.getLogger("liminal.transfer")

# Ticks de cooldown post-retorno: previene reentrada inmediata al portal
_RETURN_COOLDOWN_TICKS = 48
# Máximo de ticks esperando confirmación del servidor; tras este límite el agente se restaura
_IN_TRANSIT_TIMEOUT = 480  # 20 días simulados

# Símbolo de resonancia onírica según el arquetipo dominante del ser encontrado
_ARCH_RESONANCE: dict[str, str] = {
    "sabio":        "libro_en_lengua_muerta",
    "trickster":    "puerta_entre_mundos",
    "heroe":        "arquetipo_extraño",
    "sombra":       "ser_sin_nombre_conocido",
    "madre":        "nido_que_asfixia",
    "padre":        "ley_grabada_en_carne",
    "gobernante":   "trono_vacío",
    "rebelde":      "cadena_rota_en_mano",
    "nino_divino":  "luz_primera",
    "anima_animus": "voz_sin_cuerpo",
    "persona":      "máscara_cosida_a_cara",
    "self":         "mandala_incompleto",
}
_DEFAULT_RESONANCE = "eco_de_otro_mundo"


class AgentTransferHandler:
    """
    Registrado en SimulationClock a priority=25 (entre AgentCore y persistencia).
    En cada tick:
      1. Detecta agentes que pisaron el portal → los transfiere.
      2. Procesa eventos entrantes del servidor (agent_arrived, etc.).
    """

    def __init__(
        self,
        agent_core: AgentCore,
        portal:     PortalHex,
        client:     LiminalClient,
    ) -> None:
        self._agents = agent_core
        self._portal = portal
        self._client = client
        self._in_transit: set[str] = set()      # IDs enviados pero aún sin confirmación
        self._transit_ticks: dict[str, int] = {}  # agent_id → ticks acumulados en tránsito
        self._liminal_agents: dict[str, dict] = {}  # agent_id → datos del liminal
        self._return_cooldown: dict[str, int] = {}  # agent_id → ticks restantes post-retorno

    # ── SimulationClock handler ───────────────────────────────────────────────

    def on_tick(self, tp: TimePoint) -> None:
        # Decrementar cooldowns post-retorno; eliminar los expirados
        self._return_cooldown = {aid: t - 1 for aid, t in self._return_cooldown.items() if t > 1}
        # Incrementar contadores de tránsito y recuperar agentes atascados
        self._transit_ticks = {aid: t + 1 for aid, t in self._transit_ticks.items()}
        self._recover_stuck_agents()
        self._check_portal_crossings()
        self._process_server_events()

    def on_day(self, tp: TimePoint) -> None:
        pass   # Reservado para futuras mecánicas (ej: retorno al mundo)

    # ── Recuperación de agentes atascados ────────────────────────────────────

    def _recover_stuck_agents(self) -> None:
        """Restaura agentes que llevan demasiado tiempo sin recibir agent_placed."""
        stuck = [aid for aid, t in self._transit_ticks.items() if t > _IN_TRANSIT_TIMEOUT]
        for aid in stuck:
            agent = self._agents.agents.get(aid)
            if agent is not None:
                agent.in_liminal = False
                agent.posicion = self._portal.pos
                self._return_cooldown[aid] = _RETURN_COOLDOWN_TICKS
                logger.warning(
                    f"Agente {aid[:12]}… recuperado del tránsito liminal por timeout "
                    f"({_IN_TRANSIT_TIMEOUT} ticks sin agent_placed)"
                )
            self._in_transit.discard(aid)
            self._transit_ticks.pop(aid, None)

    # ── Detección de cruces ───────────────────────────────────────────────────

    def _check_portal_crossings(self) -> None:
        if not self._client.is_connected:
            return

        for agent in list(self._agents.agents.values()):
            if agent.id in self._in_transit:
                continue
            if agent.id in self._return_cooldown:
                continue   # recién regresó del liminal, no puede re-entrar aún
            if self._portal.agent_at_portal(agent):
                self._transfer_agent(agent)

    def _transfer_agent(self, agent: Agent) -> None:
        logger.info(f"Agente '{agent.nombre}' cruzó el portal → enviando al liminal")

        # Marcar como in_liminal — lo excluye del AgentCore desde el próximo tick
        agent.in_liminal = True
        self._in_transit.add(agent.id)
        self._transit_ticks[agent.id] = 0

        # Serializar arquetipos y rasgos para el protocolo
        archetypes = {k: round(v, 4) for k, v in agent.archetypes.to_dict().items()}
        traits = {k: round(v, 3) for k, v in agent.traits.to_dict().items()}

        # Obtener tribu si existe
        tribe_id = None
        tm = getattr(self._agents, "tribe_manager", None)
        if tm is not None:
            tribe_id = getattr(tm, "get_tribe_id", lambda x: None)(agent.id)

        self._client.send_agent_enter(
            agent_id=agent.id,
            nombre=agent.nombre,
            archetypes=archetypes,
            traits=traits,
            tribe_id=tribe_id,
        )

    # ── Procesamiento de eventos del servidor ─────────────────────────────────

    def _process_server_events(self) -> None:
        for event in self._client.drain_incoming():
            msg_type = event.get("type")

            if msg_type == "agent_placed":
                agent_id    = event.get("agent_id", "")
                liminal_pos = event.get("liminal_pos", [0, 0])
                self._in_transit.discard(agent_id)
                self._transit_ticks.pop(agent_id, None)
                self._liminal_agents[agent_id] = {
                    "pos":                tuple(liminal_pos),
                    "liminal_tick":       event.get("liminal_tick", 0),
                    "return_after_ticks": event.get("return_after_ticks", 60),
                }
                logger.info(f"Agente {agent_id[:12]}… confirmado en liminal en {tuple(liminal_pos)}")

            elif msg_type == "agent_return":
                self._handle_agent_return(event)

            elif msg_type == "agents_meet":
                self._handle_agents_meet(event)

            elif msg_type == "agent_arrived":
                nombre   = event.get("nombre", "?")
                from_sim = event.get("from_sim", "?")
                logger.info(f"[LIMINAL] Agente externo '{nombre}' llegó desde {from_sim}")

            elif msg_type == "agent_departed":
                nombre = event.get("nombre", "?")
                logger.info(f"[LIMINAL] Agente '{nombre}' partió de la zona liminal")

            elif msg_type == "sim_registered":
                logger.info(
                    f"[LIMINAL] Registrado en servidor. "
                    f"Sims activas: {event.get('active_sims', [])}, "
                    f"Agentes en liminal: {event.get('agents_in_liminal', 0)}"
                )

            elif msg_type == "sim_joined":
                logger.info(f"[LIMINAL] Nueva simulación conectada: {event.get('sim_id')}")

    def _handle_agent_return(self, event: dict) -> None:
        """El servidor devuelve un agente a esta simulación con los datos de sus encuentros."""
        agent_id  = event.get("agent_id", "")
        encounters = event.get("encounters", [])
        agent     = self._agents.agents.get(agent_id)
        if agent is None:
            logger.warning(f"Retorno de agente desconocido: {agent_id}")
            return

        agent.in_liminal = False
        self._liminal_agents.pop(agent_id, None)

        # El agente vuelve al portal; cooldown evita reentrada inmediata
        agent.posicion = self._portal.pos
        self._return_cooldown[agent_id] = _RETURN_COOLDOWN_TICKS

        logger.info(
            f"Agente '{agent.nombre}' regresó de la Zona Liminal → {agent.posicion} "
            f"| encuentros: {len(encounters)}"
        )

        if encounters:
            self._apply_encounter_effects(agent, encounters)
        else:
            if hasattr(agent, "episodic_log"):
                agent.episodic_log.append(
                    "[LIMINAL] Regresé de la Zona Liminal. No encontré a nadie del otro mundo."
                )

    def _apply_encounter_effects(self, agent, encounters: list) -> None:
        """Aplica sobre el agente los efectos de cada encuentro cross-sim vivido en el liminal."""
        for enc in encounters:
            nombre_enc = enc.get("nombre", "desconocido")
            dom_arch   = enc.get("dominant_archetype", "sombra")

            # 1. Nudge arquetípico: el arquetipo del ser encontrado deja huella
            arch_attr = "self_" if dom_arch == "self" else dom_arch
            if hasattr(agent.archetypes, arch_attr):
                current = getattr(agent.archetypes, arch_attr)
                setattr(agent.archetypes, arch_attr, min(1.0, current + 0.015))

            # 2. Registro en memoria episódica
            if hasattr(agent, "episodic_log"):
                agent.episodic_log.append(
                    f"[LIMINAL_ENCUENTRO] Crucé el portal y encontré a {nombre_enc} "
                    f"de otra civilización. Su espíritu portaba el arquetipo {dom_arch}."
                )

            # 3. Semilla onírica: el primer encuentro tiñe el próximo sueño (peso 6.0)
            if getattr(agent, "_pending_liminal_encounter", None) is None:
                agent._pending_liminal_encounter = {
                    "resonancia":          _ARCH_RESONANCE.get(dom_arch, _DEFAULT_RESONANCE),
                    "dominant_archetype":  dom_arch,
                    "nombre":              nombre_enc,
                }

        # 4. Campo colectivo: la visión de otro mundo genera presión mítica
        intensity = min(1.0, 0.5 * len(encounters))
        self._agents.collective_field.absorb_event("vision_liminal", intensity=intensity)

    def _handle_agents_meet(self, event: dict) -> None:
        """Dos agentes de distintas sims se encontraron en el liminal."""
        agent_a = event.get("agent_a", {})
        agent_b = event.get("agent_b", {})
        pos     = event.get("pos", [0, 0])
        tick    = event.get("liminal_tick", 0)

        logger.info(
            f"[ENCUENTRO LIMINAL] tick={tick} en {tuple(pos)}: "
            f"'{agent_a.get('nombre')}' ({agent_a.get('sim')}) ↔ "
            f"'{agent_b.get('nombre')}' ({agent_b.get('sim')})"
        )

        # Registrar en el episodic_log del agente local si participa
        for entry in (agent_a, agent_b):
            local_agent = self._agents.agents.get(entry.get("id", ""))
            if local_agent and hasattr(local_agent, "episodic_log"):
                other = agent_b if entry == agent_a else agent_a
                local_agent.episodic_log.append(
                    f"[LIMINAL] Me encontré con '{other.get('nombre')}' "
                    f"de otra civilización en la Zona Liminal (tick {tick})."
                )

    # ── Estado público ────────────────────────────────────────────────────────

    @property
    def agents_in_liminal(self) -> int:
        return sum(1 for a in self._agents.agents.values() if a.in_liminal)

    def get_liminal_pos(self, agent_id: str) -> tuple[int, int] | None:
        data = self._liminal_agents.get(agent_id)
        return data["pos"] if data else None
