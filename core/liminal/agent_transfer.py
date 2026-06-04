"""
core/liminal/agent_transfer.py — Manejo de transferencia de agentes al liminal.

Detecta agentes sobre el portal, los marca como in_liminal=True y
dispara el envío al servidor. También procesa los eventos entrantes del servidor.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from core.time import TimePoint

if TYPE_CHECKING:
    from core.agents.agent import Agent
    from core.agents.agent_core import AgentCore
    from core.liminal.liminal_client import LiminalClient
    from core.liminal.portal_hex import PortalHex
    from core.liminal.dialogue_writer import DialogueWriter

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


def _fallback_turn(agent_name: str, local: dict, other: dict, turn: int) -> str:
    """Turno de fallback cuando Ollama no está disponible."""
    tribe = local.get("tribe_name") or "mi pueblo"
    other_tribe = other.get("tribe_name") or "vuestra civilización"
    if turn == 0:
        return (
            f"Yo, {agent_name}, del pueblo {tribe}, te encuentro aquí "
            f"donde los mundos se tocan. ¿Qué fuerzas te guiaron a este umbral?"
        )
    return (
        f"Las palabras de {other_tribe} resuenan en mi espíritu. "
        f"Mi pueblo conoce un camino diferente, pero reconozco en ti "
        f"la misma sed de lo sagrado que nos mueve a todos."
    )


class AgentTransferHandler:
    """
    Registrado en SimulationClock a priority=25 (entre AgentCore y persistencia).
    En cada tick:
      1. Detecta agentes que pisaron el portal → los transfiere.
      2. Procesa eventos entrantes del servidor (agent_arrived, diálogos, etc.).
    """

    def __init__(
        self,
        agent_core:      "AgentCore",
        portal:          "PortalHex",
        client:          "LiminalClient",
        dialogue_writer: "DialogueWriter | None" = None,
    ) -> None:
        self._agents = agent_core
        self._portal = portal
        self._client = client
        self._dialogue_writer = dialogue_writer

        self._in_transit: set[str] = set()
        self._transit_ticks: dict[str, int] = {}
        self._liminal_agents: dict[str, dict] = {}
        self._return_cooldown: dict[str, int] = {}
        self._broadcast_myths: set[str] = set()

        # Diálogos activos: dialogue_id → metadata
        self._active_dialogues: dict[str, dict] = {}

        # OllamaClient instanciado bajo demanda (lazy) para generación de diálogo
        self._ollama: object | None = None
        self._ollama_checked: bool = False

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
        if not self._client.is_connected:
            return
        self._broadcast_new_myths(tp.dia_simulado)

    # ── Transmisión de mitos cristalizados ───────────────────────────────────

    def _broadcast_new_myths(self, dia: int) -> None:
        """Envía al servidor los mitos que cristalizaron hoy y aún no fueron transmitidos."""
        mythology = getattr(self._agents, "mythology_engine", None)
        if mythology is None:
            return
        for myth in mythology.active_myths:
            if myth.name in self._broadcast_myths:
                continue
            self._broadcast_myths.add(myth.name)
            self._client.send_myth_event(
                myth_name = myth.name,
                myth_type = myth.tipo,
                par       = myth.par,
                intensity = myth.intensidad,
                day       = dia,
            )
            logger.info(
                f"[MITO→LIMINAL] '{myth.name}' (tipo={myth.tipo}) "
                f"transmitido al servidor con intensidad={myth.intensidad:.2f}"
            )

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

    def _transfer_agent(self, agent: "Agent") -> None:
        logger.info(f"Agente '{agent.nombre}' cruzó el portal → enviando al liminal")

        agent.in_liminal = True
        self._in_transit.add(agent.id)
        self._transit_ticks[agent.id] = 0

        archetypes = {k: round(v, 4) for k, v in agent.archetypes.to_dict().items()}
        traits = {k: round(v, 3) for k, v in agent.traits.to_dict().items()}

        tm = getattr(self._agents, "tribe_manager", None)
        tribe_id = None
        if tm is not None:
            tribe_id = getattr(tm, "get_tribe_id", lambda x: None)(agent.id)

        cultural_payload = self._build_cultural_payload(agent, tribe_id)

        self._client.send_agent_enter(
            agent_id=agent.id,
            nombre=agent.nombre,
            archetypes=archetypes,
            traits=traits,
            tribe_id=tribe_id,
            cultural_payload=cultural_payload,
        )

    def _build_cultural_payload(self, agent: "Agent", tribe_id: str | None) -> dict:
        """Recolecta el contexto cultural del agente y su tribu para el payload liminal."""
        payload: dict = {
            "tribe_name":       "",
            "bioma":            "",
            "civilization_age": 0,
            "myths":            [],
            "symbols":          {},
            "lexicon":          [],
            "memories":         [],
        }

        tm = getattr(self._agents, "tribe_manager", None)
        if tm is not None and tribe_id:
            payload["tribe_name"] = getattr(tm, "get_tribe_display_name",
                                            lambda t, a: t)(tribe_id, self._agents.agents)
            lf = tm.local_fields.get(tribe_id)
            if lf:
                top = sorted(lf.symbols.items(), key=lambda x: x[1], reverse=True)[:3]
                payload["symbols"] = {k: round(v, 3) for k, v in top if v > 0.05}

            me = tm.local_myths.get(tribe_id)
            if me:
                payload["myths"] = [
                    {"name": m.name, "tipo": m.tipo, "intensity": round(m.intensidad, 2)}
                    for m in sorted(me.active_myths, key=lambda m: m.intensidad, reverse=True)[:3]
                ]

        lex_sys = getattr(self._agents, "emergent_lexicon", None)
        if lex_sys is not None and tribe_id:
            lex = lex_sys.get(tribe_id)
            if lex:
                payload["lexicon"] = list(lex.words.values())[:5]

        if hasattr(agent, "episodic_log") and agent.episodic_log:
            # Filtra entradas interesantes: sueños, encuentros, mitos
            notable = [e for e in agent.episodic_log if any(
                kw in e for kw in ("SUEÑO", "LIMINAL", "MITO", "COMPLEJO", "RITUAL")
            )][-3:] or agent.episodic_log[-3:]
            payload["memories"] = notable

        clock = getattr(self._agents, "_clock", None) or getattr(self._agents, "clock", None)
        if clock is not None:
            payload["civilization_age"] = getattr(clock, "dia_simulado", 0)

        return payload

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

            elif msg_type == "myth_broadcast":
                self._handle_myth_broadcast(event)

            elif msg_type == "dialogue_start":
                self._handle_dialogue_start(event)

            elif msg_type == "dialogue_turn_request":
                self._handle_dialogue_turn_request(event)

            elif msg_type == "dialogue_complete":
                self._handle_dialogue_complete(event)

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

    # ── Diálogo liminal ───────────────────────────────────────────────────────

    def _get_ollama(self):
        if self._ollama_checked:
            return self._ollama
        self._ollama_checked = True
        try:
            from core.narrative.ollama_client import OllamaClient
            client = OllamaClient()
            if client.is_available():
                self._ollama = client
                logger.info("[DIÁLOGO] OllamaClient listo (modelo: %s)", client.model)
            else:
                logger.warning("[DIÁLOGO] Ollama no disponible — los turnos usarán fallback")
        except Exception as exc:
            logger.warning("[DIÁLOGO] No se pudo inicializar OllamaClient: %s", exc)
        return self._ollama

    def _handle_dialogue_start(self, event: dict) -> None:
        dlg_id   = event.get("dialogue_id", "?")
        name_a   = event.get("agent_a_name", "?")
        name_b   = event.get("agent_b_name", "?")
        self._active_dialogues[dlg_id] = event
        logger.info(f"[DIÁLOGO] Iniciado '{dlg_id}': {name_a} ↔ {name_b}")

    def _handle_dialogue_turn_request(self, event: dict) -> None:
        """El servidor pide que esta sim genere el próximo turno del diálogo."""
        dlg_id   = event.get("dialogue_id", "")
        agent_id = event.get("agent_id", "")
        logger.info(f"[DIÁLOGO] Turno solicitado para agente {agent_id[:12]}… (diálogo {dlg_id})")

        # Obtener el agente local (puede estar in_liminal=True, lo cual es correcto)
        agent = self._agents.agents.get(agent_id)
        agent_name = agent.nombre if agent else event.get("agent_name", "desconocido")

        # Lanzar generación en hilo separado para no bloquear el tick loop
        t = threading.Thread(
            target=self._generate_and_send_turn,
            args=(event, agent_name),
            daemon=True,
            name=f"DialogueTurn-{dlg_id[:8]}",
        )
        t.start()

    def _generate_and_send_turn(self, event: dict, agent_name: str) -> None:
        """Corre en hilo de fondo: genera texto con LLM y envía la respuesta."""
        from core.narrative.prompts import prompt_dialogo

        dlg_id         = event.get("dialogue_id", "")
        agent_id       = event.get("agent_id", "")
        local_payload  = event.get("local_payload", {})
        other_payload  = event.get("other_payload", {})
        previous_turns = event.get("previous_turns", [])
        turn_number    = event.get("turn_number", 0)

        text = None
        ollama = self._get_ollama()
        if ollama is not None:
            try:
                p = prompt_dialogo(
                    agent_name     = agent_name,
                    tribe_name     = local_payload.get("tribe_name", ""),
                    bioma          = local_payload.get("bioma", ""),
                    local_myths    = local_payload.get("myths", []),
                    local_symbols  = local_payload.get("symbols", {}),
                    local_lexicon  = local_payload.get("lexicon", []),
                    local_memories = local_payload.get("memories", []),
                    other_name     = event.get("other_agent_name", "el Desconocido"),
                    other_tribe    = other_payload.get("tribe_name", ""),
                    other_myths    = other_payload.get("myths", []),
                    other_symbols  = other_payload.get("symbols", {}),
                    previous_turns = previous_turns,
                    turn_number    = turn_number,
                )
                text = ollama.generate(p, max_tokens=120)
                logger.info(f"[DIÁLOGO] Turno generado para '{agent_name}': {len(text or '')} chars")
            except Exception as exc:
                logger.warning(f"[DIÁLOGO] Error generando turno: {exc}")

        if not text:
            text = _fallback_turn(agent_name, local_payload, other_payload, turn_number)

        self._client.send_dialogue_turn(
            dialogue_id=dlg_id,
            agent_id=agent_id,
            text=text,
        )

    def _handle_dialogue_complete(self, event: dict) -> None:
        """El diálogo terminó — registrar en memoria, vault y campo colectivo."""
        dlg_id  = event.get("dialogue_id", "")
        turns   = event.get("turns", [])
        a_name  = event.get("agent_a_name", "?")
        b_name  = event.get("agent_b_name", "?")
        sim_a   = event.get("sim_a", "?")
        sim_b   = event.get("sim_b", "?")

        self._active_dialogues.pop(dlg_id, None)

        logger.info(
            f"[DIÁLOGO] Completo '{dlg_id}': {len(turns)} turnos entre "
            f"'{a_name}' y '{b_name}'"
        )

        # Registrar en episodic_log del agente local que participó
        for entry in (event.get("agent_a_id", ""), event.get("agent_b_id", "")):
            agent = self._agents.agents.get(entry)
            if agent and hasattr(agent, "episodic_log"):
                other = b_name if agent.nombre == a_name else a_name
                snippet = turns[-1]["text"][:80] if turns else ""
                agent.episodic_log.append(
                    f"[DIÁLOGO_LIMINAL] Crucé palabras con {other} de otra civilización. "
                    f"Sus últimas palabras: «{snippet}»"
                )

        # Presión mítica: un diálogo inter-civilizacional es un evento mayor
        intensity = min(1.0, 0.3 * len(turns))
        self._agents.collective_field.absorb_event("dialogo_liminal", intensity=intensity)

        # Escribir al vault
        if self._dialogue_writer is not None:
            local_p = event.get("local_payload", {})
            other_p = event.get("other_payload", {})
            # Calcular el día actual
            dia = local_p.get("civilization_age", 0) or other_p.get("civilization_age", 0)
            try:
                self._dialogue_writer.write(
                    dialogue_id   = dlg_id,
                    agent_a_name  = a_name,
                    sim_a         = sim_a,
                    tribe_a       = local_p.get("tribe_name", "") if sim_a == self._client.sim_id else other_p.get("tribe_name", ""),
                    agent_b_name  = b_name,
                    sim_b         = sim_b,
                    tribe_b       = other_p.get("tribe_name", "") if sim_a == self._client.sim_id else local_p.get("tribe_name", ""),
                    local_payload = local_p,
                    other_payload = other_p,
                    turns         = turns,
                    dia           = dia,
                )
            except Exception as exc:
                logger.warning(f"[DIÁLOGO] Error escribiendo transcripción: {exc}")

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

    def _handle_myth_broadcast(self, event: dict) -> None:
        """Eco de un mito cristalizado en otra simulación — altera el campo colectivo local."""
        origin_sim = event.get("origin_sim", "?")
        myth_name  = event.get("myth_name", "desconocido")
        myth_type  = event.get("myth_type", "mito_moral")
        par        = event.get("par", [])
        intensity  = event.get("intensity", 1.0)

        logger.info(
            f"[ECO MÍTICO] Mito '{myth_name}' de {origin_sim} "
            f"resonando en campo colectivo local (intensidad={intensity:.2f})"
        )

        # Presionar el campo colectivo (eco atenuado al 40%)
        self._agents.collective_field.absorb_myth_broadcast(
            myth_type  = myth_type,
            par        = par,
            intensity  = intensity,
            origin_sim = origin_sim,
        )

        # Inyectar símbolo onírico en agentes con arquetipo resonante
        # Los agentes cuyo arquetipo dominante coincide con el par del mito
        # tendrán sus sueños perturbados por el eco
        eco_symbol = _ARCH_RESONANCE.get(par[0] if par else "sombra", _DEFAULT_RESONANCE)
        for agent in self._agents.agents.values():
            if not agent.is_alive or agent.in_liminal:
                continue
            # Sólo si el agente tiene afinidad arquetípica con el mito
            dominant = agent.archetypes.dominant()
            if dominant in par:
                if getattr(agent, "_pending_liminal_encounter", None) is None:
                    agent._pending_liminal_encounter = {
                        "resonancia":         eco_symbol,
                        "dominant_archetype": par[0] if par else "sombra",
                        "nombre":             f"Eco de {origin_sim}",
                    }
                if hasattr(agent, "episodic_log"):
                    agent.episodic_log.append(
                        f"[ECO_MITICO] Algo distante resuena. "
                        f"Un espíritu de otra civilización crystallizó el arquetipo {myth_type}."
                    )

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
