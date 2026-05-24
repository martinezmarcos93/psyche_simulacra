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
        # Callback opcional para notificar al visualizador de eventos nuevos
        self.on_event_cb = None
        # Pares de encuentros ya notificados (para no spamear el mismo encuentro)
        self._notified_meetings: set[frozenset] = set()
        # Event loop de asyncio — se asigna en serve()
        self._loop: asyncio.AbstractEventLoop | None = None

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
        agent_id   = msg.get("agent_id", "")
        nombre     = msg.get("nombre", "Desconocido")
        from_sim   = msg.get("sim_id", "?")
        archetypes = msg.get("archetypes", {})
        traits     = msg.get("traits", {})

        pos = self.world.spawn_position(agent_id)
        self.agent_registry.register(
            agent_id=agent_id,
            nombre=nombre,
            from_sim=from_sim,
            pos=pos,
            archetypes=archetypes,
            traits=traits,
            arrived_at_tick=self.clock.tick,
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
        """Devuelve agentes que superaron LIMINAL_RETURN_AFTER_TICKS."""
        now_tick = self.clock.tick
        to_return = [
            a for a in self.agent_registry.all()
            if (now_tick - a.arrived_at_tick) >= cfg.LIMINAL_RETURN_AFTER_TICKS
        ]
        for agent in to_return:
            await self._return_agent(agent)

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
        """Detecta si el agente recién llegado comparte hex con otro de distinta sim."""
        for existing in self.agent_registry.all():
            if existing.agent_id == new_agent_id:
                continue
            if existing.pos != pos:
                continue
            if existing.from_sim == new_sim:
                continue   # misma sim, no es un encuentro cross-sim

            pair = frozenset([new_agent_id, existing.agent_id])
            if pair in self._notified_meetings:
                continue

            self._notified_meetings.add(pair)

            # Registrar encuentro en ambos agentes
            new_agent_rec = self.agent_registry.get(new_agent_id)
            if new_agent_rec:
                new_agent_rec.encounters.append({
                    "nombre":              existing.nombre,
                    "dominant_archetype":  existing.dominant_archetype,
                    "from_sim":            existing.from_sim,
                })
                existing.encounters.append({
                    "nombre":              new_nombre,
                    "dominant_archetype":  new_agent_rec.dominant_archetype,
                    "from_sim":            new_sim,
                })

            await self._broadcast_meeting(
                agent_a_id=new_agent_id, agent_a_nombre=new_nombre, sim_a=new_sim,
                agent_b_id=existing.agent_id, agent_b_nombre=existing.nombre, sim_b=existing.from_sim,
                pos=pos,
            )

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
