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
        self._in_transit: set[str] = set()   # IDs enviados pero aún sin confirmación
        self._liminal_agents: dict[str, dict] = {}  # agent_id → datos del liminal

    # ── SimulationClock handler ───────────────────────────────────────────────

    def on_tick(self, tp: TimePoint) -> None:
        self._check_portal_crossings()
        self._process_server_events()

    def on_day(self, tp: TimePoint) -> None:
        pass   # Reservado para futuras mecánicas (ej: retorno al mundo)

    # ── Detección de cruces ───────────────────────────────────────────────────

    def _check_portal_crossings(self) -> None:
        if not self._client.is_connected:
            return

        for agent in list(self._agents.agents.values()):
            if agent.id in self._in_transit:
                continue
            if self._portal.agent_at_portal(agent):
                self._transfer_agent(agent)

    def _transfer_agent(self, agent: Agent) -> None:
        logger.info(f"Agente '{agent.nombre}' cruzó el portal → enviando al liminal")

        # Marcar como in_liminal — lo excluye del AgentCore desde el próximo tick
        agent.in_liminal = True
        self._in_transit.add(agent.id)

        # Serializar arquetipos y rasgos para el protocolo
        archetypes = {k: round(v, 4) for k, v in agent.archetypes.weights.items()}
        traits = {
            "openness":          round(agent.traits.openness, 3),
            "conscientiousness": round(agent.traits.conscientiousness, 3),
            "extraversion":      round(agent.traits.extraversion, 3),
            "agreeableness":     round(agent.traits.agreeableness, 3),
            "neuroticism":       round(agent.traits.neuroticism, 3),
        }

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
        """El servidor devuelve un agente a esta simulación."""
        agent_id = event.get("agent_id", "")
        agent    = self._agents.agents.get(agent_id)
        if agent is None:
            logger.warning(f"Retorno de agente desconocido: {agent_id}")
            return

        agent.in_liminal = False
        self._liminal_agents.pop(agent_id, None)

        # El agente vuelve al portal para que no aparezca en el vacío
        agent.posicion = self._portal.pos

        logger.info(f"Agente '{agent.nombre}' regresó de la Zona Liminal → {agent.posicion}")

        # Opcionalmente: dejar registro en el episodic_log del agente
        if hasattr(agent, "episodic_log"):
            agent.episodic_log.append("[LIMINAL] Regresé de la Zona Liminal.")

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
