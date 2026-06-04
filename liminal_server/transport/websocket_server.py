"""
transport/websocket_server.py — Servidor WebSocket de la Zona Liminal.

Una conexión por simulación. Maneja:
  - sim_connect:  registra la simulación
  - agent_enter:  recibe un agente, le asigna posición, hace broadcast
  - ping:         responde pong con el tick liminal actual
  - desconexión:  limpia el registro y notifica a las demás sims

El método tick() debe llamarse desde el loop principal (main.py) en cada
avance del reloj liminal. Ejecuta retornos y detección de encuentros.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Set

import websockets
from websockets.server import ServerConnection

from core.simulation_registry import SimulationRegistry
from core.agent_registry import AgentRegistry
from core.liminal_world import LiminalWorld
from core.liminal_clock import LiminalClock
from protocol.schemas import MsgType, PROTOCOL_VERSION
import config as cfg

logger = logging.getLogger("liminal.server")

# Configuración del diálogo
_DIALOGUE_MAX_TURNS   = int(getattr(cfg, "DIALOGUE_MAX_TURNS",   4))   # turnos totales (2 por agente)
_DIALOGUE_TIMEOUT_SEC = float(getattr(cfg, "DIALOGUE_TIMEOUT_SEC", 180.0))  # seg por turno


@dataclass
class DialogueState:
    dialogue_id:        str
    agent_a_id:         str
    agent_a_name:       str
    agent_a_sim:        str
    agent_b_id:         str
    agent_b_name:       str
    agent_b_sim:        str
    local_payload_a:    dict
    local_payload_b:    dict
    turns:              list = field(default_factory=list)
    turns_completed:    int  = 0
    current_speaker:    str  = ""   # sim_id que debe hablar ahora
    pending_future:     object = None  # asyncio.Future esperando turno response


class LiminalServer:
    def __init__(
        self,
        world:          LiminalWorld,
        clock:          LiminalClock,
        sim_registry:   SimulationRegistry,
        agent_registry: AgentRegistry,
        host:           str = "0.0.0.0",
        port:           int = 8765,
    ) -> None:
        self.world          = world
        self.clock          = clock
        self.sim_registry   = sim_registry
        self.agent_registry = agent_registry
        self.host           = host
        self.port           = port
        self._connections:  Set[ServerConnection] = set()
        self.on_event_cb = None
        self._notified_meetings: set[frozenset] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

        # Diálogos activos: dialogue_id → DialogueState
        self._dialogues: dict[str, DialogueState] = {}
        # Futures pendientes: dialogue_id → asyncio.Future (resuelto al llegar turn_response)
        self._dialogue_futures: dict[str, "asyncio.Future[dict]"] = {}
        # Directorio de transcripciones del servidor
        self._dialogues_dir = getattr(cfg, "DIALOGUES_DIR", "dialogues")

    # ── Handler principal ────────────────────────────────────────────────────

    async def handler(self, ws: ServerConnection) -> None:
        sim_id = None
        self._connections.add(ws)
        remote = getattr(ws, "remote_address", "?")
        logger.info(f"Nueva conexión desde {remote}")

        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await self._send(ws, {"type": MsgType.ERROR, "detail": "invalid json"})
                    continue

                sim_id_in_msg = await self._dispatch(msg, ws)
                if sim_id_in_msg and sim_id is None:
                    sim_id = sim_id_in_msg

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._connections.discard(ws)
            if sim_id and self.sim_registry.is_connected(sim_id):
                self.sim_registry.unregister(sim_id)
                logger.info(f"Simulación desconectada: {sim_id} | activas: {self.sim_registry.count()}")
                await self._broadcast(
                    {"type": MsgType.SIM_DISCONNECTED, "sim_id": sim_id},
                    exclude=ws,
                )
                if self.on_event_cb:
                    self.on_event_cb("sim_disconnected", {"sim_id": sim_id})

    # ── Dispatcher de mensajes ───────────────────────────────────────────────

    async def _dispatch(self, msg: dict, ws: ServerConnection) -> str | None:
        """Procesa un mensaje. Retorna sim_id si es un sim_connect, None si no."""
        msg_type = msg.get("type")

        if msg_type == MsgType.PING:
            await self._send(ws, {"type": MsgType.PONG, "liminal_tick": self.clock.tick})
            return None

        if msg_type == MsgType.SIM_CONNECT:
            return await self._handle_sim_connect(msg, ws)

        if msg_type == MsgType.AGENT_ENTER:
            await self._handle_agent_enter(msg, ws)
            return None

        if msg_type == MsgType.MYTH_CRYSTALLIZED:
            await self._handle_myth_crystallized(msg, ws)
            return None

        if msg_type == MsgType.DIALOGUE_TURN_RESPONSE:
            self._handle_dialogue_turn_response(msg)
            return None

        logger.warning(f"Tipo de mensaje desconocido: {msg_type!r}")
        await self._send(ws, {"type": MsgType.ERROR, "detail": f"unknown type: {msg_type}"})
        return None

    # ── Handlers específicos ─────────────────────────────────────────────────

    async def _handle_sim_connect(self, msg: dict, ws: ServerConnection) -> str:
        sim_id  = msg.get("sim_id", "SIM_DESCONOCIDA")
        seed    = msg.get("seed", 0)
        version = msg.get("version", "?")

        # Validar versión de protocolo
        if version != PROTOCOL_VERSION:
            await self._send(ws, {
                "type":     MsgType.ERROR,
                "detail":   f"protocol_version mismatch: server={PROTOCOL_VERSION} client={version}",
            })
            logger.warning(f"Versión incompatible desde {sim_id}: {version}")
            return sim_id

        self.sim_registry.register(sim_id=sim_id, seed=seed, version=version, ws=ws)
        logger.info(f"Simulación registrada: {sim_id} | sims activas: {self.sim_registry.count()}")

        await self._send(ws, {
            "type":              MsgType.SIM_REGISTERED,
            "sim_id":            sim_id,
            "liminal_tick":      self.clock.tick,
            "protocol_version":  PROTOCOL_VERSION,
            "agents_in_liminal": self.agent_registry.count(),
            "active_sims":       self.sim_registry.sim_ids(),
        })

        # Notificar a las demás sims
        await self._broadcast(
            {"type": MsgType.SIM_JOINED, "sim_id": sim_id},
            exclude=ws,
        )

        if self.on_event_cb:
            self.on_event_cb("sim_connected", {"sim_id": sim_id})

        return sim_id

    async def _handle_agent_enter(self, msg: dict, ws: ServerConnection) -> None:
        agent_id         = msg.get("agent_id", "")
        nombre           = msg.get("nombre", "Desconocido")
        from_sim         = msg.get("sim_id", "?")
        archetypes       = msg.get("archetypes", {})
        traits           = msg.get("traits", {})
        cultural_payload = msg.get("cultural_payload", {})

        pos = self.world.spawn_position(agent_id)
        self.agent_registry.register(
            agent_id=agent_id,
            nombre=nombre,
            from_sim=from_sim,
            pos=pos,
            archetypes=archetypes,
            traits=traits,
            arrived_at_tick=self.clock.tick,
            cultural_payload=cultural_payload,
        )

        logger.info(f"Agente '{nombre}' ({agent_id[:12]}…) llegó desde {from_sim} → {pos}")

        # Confirmar a la sim de origen
        await self._send(ws, {
            "type":                   MsgType.AGENT_PLACED,
            "agent_id":               agent_id,
            "liminal_pos":            list(pos),
            "liminal_tick":           self.clock.tick,
            "return_after_ticks":     cfg.LIMINAL_RETURN_AFTER_TICKS,
        })

        # Broadcast a todas las sims
        await self._broadcast({
            "type":       MsgType.AGENT_ARRIVED,
            "from_sim":   from_sim,
            "agent_id":   agent_id,
            "nombre":     nombre,
            "pos":        list(pos),
            "archetypes": archetypes,
        })

        if self.on_event_cb:
            self.on_event_cb("agent_arrived", {
                "agent_id": agent_id, "nombre": nombre, "from_sim": from_sim, "pos": pos,
            })

        # Detectar encuentros inmediatos (este agente comparte hex con otro)
        await self._check_meeting_at(pos, agent_id, nombre, from_sim)

    async def _handle_myth_crystallized(self, msg: dict, ws: ServerConnection) -> None:
        origin_sim = msg.get("sim_id", "?")
        myth_name  = msg.get("myth_name", "desconocido")
        myth_type  = msg.get("myth_type", "mito_moral")
        par        = msg.get("par", [])
        intensity  = msg.get("intensity", 1.0)
        day        = msg.get("day", 0)

        logger.info(
            f"[MITO] '{myth_name}' cristalizó en {origin_sim} "
            f"(tipo={myth_type}, intensidad={intensity:.2f})"
        )

        # Propagar como eco a todas las otras sims (no a la de origen)
        broadcast = {
            "type":        MsgType.MYTH_BROADCAST,
            "origin_sim":  origin_sim,
            "myth_name":   myth_name,
            "myth_type":   myth_type,
            "par":         par,
            "intensity":   intensity,
            "day":         day,
        }
        await self._broadcast(broadcast, exclude=ws)

        if self.on_event_cb:
            self.on_event_cb("myth_crystallized", {
                "origin_sim": origin_sim, "myth_name": myth_name,
                "myth_type": myth_type, "intensity": intensity,
            })

    # ── Lógica de tick liminal ────────────────────────────────────────────────

    def tick(self) -> None:
        """
        Llamado desde main.py cuando avanza el reloj liminal.
        Programa los chequeos asincrónicos en el event loop del servidor.
        """
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._on_liminal_tick(), self._loop)

    async def _on_liminal_tick(self) -> None:
        await self._check_returns()

    async def _check_returns(self) -> None:
        """Devuelve agentes que superaron LIMINAL_RETURN_AFTER_TICKS, salvo los en diálogo."""
        now_tick = self.clock.tick
        in_dialogue = self._agents_in_dialogue()
        to_return = [
            a for a in self.agent_registry.all()
            if (now_tick - a.arrived_at_tick) >= cfg.LIMINAL_RETURN_AFTER_TICKS
            and a.agent_id not in in_dialogue
        ]
        for agent in to_return:
            await self._return_agent(agent)

    def _agents_in_dialogue(self) -> set[str]:
        ids: set[str] = set()
        for state in self._dialogues.values():
            ids.add(state.agent_a_id)
            ids.add(state.agent_b_id)
        return ids

    async def _return_agent(self, agent) -> None:
        """Envía al agente de vuelta a su simulación de origen."""
        self.agent_registry.remove(agent.agent_id)

        # Limpiar pares de encuentros de este agente para que futuras visitas puedan re-encontrarse
        self._notified_meetings = {
            pair for pair in self._notified_meetings if agent.agent_id not in pair
        }

        entry = self.sim_registry.get(agent.from_sim)
        if entry and entry.websocket:
            await self._send(entry.websocket, {
                "type":         MsgType.AGENT_RETURN,
                "agent_id":     agent.agent_id,
                "liminal_tick": self.clock.tick,
                "encounters":   agent.encounters,
            })
            logger.info(
                f"Agente '{agent.nombre}' retornó a {agent.from_sim} "
                f"con {len(agent.encounters)} encuentro(s)"
            )
        else:
            logger.warning(
                f"Agente '{agent.nombre}' debería retornar pero {agent.from_sim} no está conectada"
            )

        # Notificar a todas las demás sims
        await self._broadcast({
            "type":       "agent_departed",
            "agent_id":   agent.agent_id,
            "nombre":     agent.nombre,
            "to_sim":     agent.from_sim,
        })

        if self.on_event_cb:
            self.on_event_cb("agent_returned", {"agent_id": agent.agent_id, "nombre": agent.nombre})

    async def _check_meeting_at(self, pos: tuple, new_agent_id: str,
                                 new_nombre: str, new_sim: str) -> None:
        """Detecta si el agente recién llegado comparte hex con otro de distinta sim.
        Si hay encuentro: registra metadatos y arranca el diálogo entre IAs."""
        new_agent_rec = self.agent_registry.get(new_agent_id)

        for existing in self.agent_registry.all():
            if existing.agent_id == new_agent_id:
                continue
            if existing.pos != pos:
                continue
            if existing.from_sim == new_sim:
                continue

            pair = frozenset([new_agent_id, existing.agent_id])
            if pair in self._notified_meetings:
                continue

            self._notified_meetings.add(pair)

            if new_agent_rec:
                new_agent_rec.encounters.append({
                    "nombre":             existing.nombre,
                    "dominant_archetype": existing.dominant_archetype,
                    "from_sim":           existing.from_sim,
                })
                existing.encounters.append({
                    "nombre":             new_nombre,
                    "dominant_archetype": new_agent_rec.dominant_archetype if new_agent_rec else "sombra",
                    "from_sim":           new_sim,
                })

            await self._broadcast_meeting(
                agent_a_id=new_agent_id, agent_a_nombre=new_nombre, sim_a=new_sim,
                agent_b_id=existing.agent_id, agent_b_nombre=existing.nombre,
                sim_b=existing.from_sim, pos=pos,
            )

            # Iniciar diálogo entre las dos IAs si ambas sims están conectadas
            if (self.sim_registry.is_connected(new_sim)
                    and self.sim_registry.is_connected(existing.from_sim)):
                asyncio.create_task(
                    self._run_dialogue(
                        agent_a_id   = new_agent_id,
                        agent_a_name = new_nombre,
                        sim_a        = new_sim,
                        payload_a    = new_agent_rec.cultural_payload if new_agent_rec else {},
                        agent_b_id   = existing.agent_id,
                        agent_b_name = existing.nombre,
                        sim_b        = existing.from_sim,
                        payload_b    = existing.cultural_payload,
                    )
                )

    # ── Orquestación del diálogo liminal ────────────────────────────────────────

    async def _run_dialogue(
        self,
        agent_a_id:   str,
        agent_a_name: str,
        sim_a:        str,
        payload_a:    dict,
        agent_b_id:   str,
        agent_b_name: str,
        sim_b:        str,
        payload_b:    dict,
    ) -> None:
        """Coordina un diálogo completo entre dos agentes de distintas sims."""
        dlg_id = f"dlg_{uuid.uuid4().hex[:12]}"

        state = DialogueState(
            dialogue_id     = dlg_id,
            agent_a_id      = agent_a_id,
            agent_a_name    = agent_a_name,
            agent_a_sim     = sim_a,
            agent_b_id      = agent_b_id,
            agent_b_name    = agent_b_name,
            agent_b_sim     = sim_b,
            local_payload_a = payload_a,
            local_payload_b = payload_b,
        )
        self._dialogues[dlg_id] = state

        logger.info(f"[DIÁLOGO] Iniciando {dlg_id}: '{agent_a_name}' ({sim_a}) ↔ '{agent_b_name}' ({sim_b})")

        # Notificar inicio a ambas sims
        start_msg = {
            "type":          MsgType.DIALOGUE_START,
            "dialogue_id":   dlg_id,
            "agent_a_id":    agent_a_id,
            "agent_a_name":  agent_a_name,
            "agent_b_id":    agent_b_id,
            "agent_b_name":  agent_b_name,
        }
        await self._broadcast(start_msg)

        # Alternar turnos: A, B, A, B... hasta _DIALOGUE_MAX_TURNS
        speakers = [
            (sim_a, agent_a_id, agent_a_name, payload_a, payload_b, agent_b_name),
            (sim_b, agent_b_id, agent_b_name, payload_b, payload_a, agent_a_name),
        ]

        for turn_idx in range(_DIALOGUE_MAX_TURNS):
            (speaker_sim, speaker_id, speaker_name,
             local_p, other_p, other_name) = speakers[turn_idx % 2]

            state.current_speaker = speaker_sim

            future: "asyncio.Future[dict]" = asyncio.get_event_loop().create_future()
            self._dialogue_futures[dlg_id] = future

            turn_req = {
                "type":             MsgType.DIALOGUE_TURN_REQUEST,
                "dialogue_id":      dlg_id,
                "agent_id":         speaker_id,
                "agent_name":       speaker_name,
                "other_agent_name": other_name,
                "local_payload":    local_p,
                "other_payload":    other_p,
                "previous_turns":   state.turns.copy(),
                "turn_number":      turn_idx,
            }

            entry = self.sim_registry.get(speaker_sim)
            if entry and entry.websocket:
                await self._send(entry.websocket, turn_req)
            else:
                logger.warning(f"[DIÁLOGO] Sim {speaker_sim} desconectada durante diálogo {dlg_id}")
                break

            # Esperar respuesta con timeout
            try:
                response = await asyncio.wait_for(future, timeout=_DIALOGUE_TIMEOUT_SEC)
                text = response.get("text", "…")
            except asyncio.TimeoutError:
                logger.warning(f"[DIÁLOGO] Timeout en turno {turn_idx} de {dlg_id}")
                text = "…el silencio lo dice todo…"
            finally:
                self._dialogue_futures.pop(dlg_id, None)

            state.turns.append({
                "speaker_name": speaker_name,
                "speaker_sim":  speaker_sim,
                "text":         text,
            })
            state.turns_completed += 1
            logger.info(f"[DIÁLOGO] Turno {turn_idx + 1}/{_DIALOGUE_MAX_TURNS} "
                        f"({speaker_name}): {text[:60]}…")

        # Diálogo completo — enviar transcripción a ambas sims
        complete_msg = {
            "type":          MsgType.DIALOGUE_COMPLETE,
            "dialogue_id":   dlg_id,
            "agent_a_id":    agent_a_id,
            "agent_a_name":  agent_a_name,
            "sim_a":         sim_a,
            "agent_b_id":    agent_b_id,
            "agent_b_name":  agent_b_name,
            "sim_b":         sim_b,
            "local_payload": payload_a,
            "other_payload": payload_b,
            "turns":         state.turns,
        }
        await self._broadcast(complete_msg)

        self._save_dialogue_transcript(state)
        self._dialogues.pop(dlg_id, None)

        if self.on_event_cb:
            self.on_event_cb("dialogue_complete", {
                "dialogue_id": dlg_id,
                "agent_a": agent_a_name,
                "agent_b": agent_b_name,
                "turns":   len(state.turns),
            })

        logger.info(f"[DIÁLOGO] Finalizado {dlg_id} con {len(state.turns)} turnos")

    def _handle_dialogue_turn_response(self, msg: dict) -> None:
        """Recibe un turno generado por una sim y resuelve el future correspondiente."""
        dlg_id = msg.get("dialogue_id", "")
        future = self._dialogue_futures.get(dlg_id)
        if future and not future.done():
            future.set_result(msg)
        else:
            logger.warning(f"[DIÁLOGO] Respuesta tardía o sin future para diálogo {dlg_id}")

    def _save_dialogue_transcript(self, state: DialogueState) -> None:
        """Guarda la transcripción del diálogo en el directorio del servidor."""
        import pathlib
        out_dir = pathlib.Path(self._dialogues_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{state.dialogue_id}_{_safe(state.agent_a_name)}_vs_{_safe(state.agent_b_name)}.json"
        import json as _json
        data = {
            "dialogue_id":   state.dialogue_id,
            "agent_a":       {"id": state.agent_a_id, "name": state.agent_a_name, "sim": state.agent_a_sim},
            "agent_b":       {"id": state.agent_b_id, "name": state.agent_b_name, "sim": state.agent_b_sim},
            "payload_a":     state.local_payload_a,
            "payload_b":     state.local_payload_b,
            "turns":         state.turns,
            "timestamp":     time.time(),
        }
        try:
            (out_dir / filename).write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"[DIÁLOGO] Transcripción guardada: {filename}")
        except Exception as exc:
            logger.warning(f"[DIÁLOGO] Error guardando transcripción: {exc}")

    async def _broadcast_meeting(self, agent_a_id, agent_a_nombre, sim_a,
                                  agent_b_id, agent_b_nombre, sim_b, pos) -> None:
        logger.info(
            f"ENCUENTRO: '{agent_a_nombre}' ({sim_a}) ↔ '{agent_b_nombre}' ({sim_b}) en {pos}"
        )
        msg = {
            "type":           MsgType.AGENTS_MEET,
            "pos":            list(pos),
            "agent_a":        {"id": agent_a_id, "nombre": agent_a_nombre, "sim": sim_a},
            "agent_b":        {"id": agent_b_id, "nombre": agent_b_nombre, "sim": sim_b},
            "liminal_tick":   self.clock.tick,
        }
        await self._broadcast(msg)

        if self.on_event_cb:
            self.on_event_cb("agents_meet", {
                "agent_a": agent_a_nombre, "sim_a": sim_a,
                "agent_b": agent_b_nombre, "sim_b": sim_b,
            })

    # ── Helpers de red ───────────────────────────────────────────────────────

    async def _send(self, ws: ServerConnection, msg: dict) -> None:
        try:
            await ws.send(json.dumps(msg, ensure_ascii=False))
        except websockets.exceptions.ConnectionClosed:
            pass

    async def _broadcast(self, msg: dict, exclude: ServerConnection | None = None) -> None:
        raw  = json.dumps(msg, ensure_ascii=False)
        dead: Set[ServerConnection] = set()
        for ws in list(self._connections):
            if ws is exclude:
                continue
            try:
                await ws.send(raw)
            except websockets.exceptions.ConnectionClosed:
                dead.add(ws)
        self._connections -= dead

    # ── Inicio ───────────────────────────────────────────────────────────────

    async def serve(self) -> None:
        self._loop = asyncio.get_running_loop()
        logger.info(f"Servidor liminal iniciando en ws://{self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            logger.info(f"Servidor activo — esperando simulaciones...")
            await asyncio.Future()   # corre para siempre


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:20]
