"""
core/liminal/liminal_client.py — Cliente WebSocket hacia el servidor Zona Liminal.

Corre en un thread daemon con su propio event loop asyncio.
Thread-safe: usa queues para comunicarse con el thread principal de la simulación.

Uso:
    client = LiminalClient(sim_id="SIM_A:uuid", seed=42)
    client.start(host="localhost", port=8765)
    client.send_agent_enter(agent_id, nombre, archetypes, traits)
    events = client.drain_incoming()   # llamar desde el thread principal
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
import time
from typing import Callable

try:
    import websockets
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False

logger = logging.getLogger("liminal.client")

# Versión mínima de protocolo esperada en el servidor
_PROTOCOL_VERSION = "0.1.0"


class LiminalClient:
    """
    Cliente WebSocket no-bloqueante para PSYCHE SIMULACRA.
    La simulación usa este objeto sin preocuparse por async/threads.
    """

    def __init__(self, sim_id: str, seed: int) -> None:
        self.sim_id = sim_id
        self.seed   = seed

        self._outgoing:  queue.Queue[dict] = queue.Queue()
        self._incoming:  queue.Queue[dict] = queue.Queue()

        self._connected:  bool = False
        self._running:    bool = False
        self._thread:     threading.Thread | None = None
        self._loop:       asyncio.AbstractEventLoop | None = None

        # Callbacks opcionales (llamados en el thread de red — cuidado con thread-safety)
        self.on_agent_arrived: Callable[[dict], None] | None = None
        self.on_sim_joined:    Callable[[dict], None] | None = None

    # ── API pública (thread-safe) ─────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self, host: str = "localhost", port: int = 8765) -> None:
        """Inicia la conexión en un thread daemon. No bloquea."""
        if not _WS_AVAILABLE:
            logger.error("Librería 'websockets' no instalada. Zona Liminal desactivada.")
            logger.error("Instalá con: pip install websockets")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._thread_main,
            args=(host, port),
            daemon=True,
            name="LiminalClient",
        )
        self._thread.start()
        logger.info(f"LiminalClient iniciado → ws://{host}:{port}")

    def stop(self) -> None:
        self._running = False
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def send_agent_enter(
        self,
        agent_id:   str,
        nombre:     str,
        archetypes: dict,
        traits:     dict,
        tribe_id:   str | None = None,
    ) -> None:
        """Encola un evento agent_enter para enviarlo al servidor."""
        self._outgoing.put({
            "type":       "agent_enter",
            "sim_id":     self.sim_id,
            "agent_id":   agent_id,
            "nombre":     nombre,
            "archetypes": archetypes,
            "traits":     traits,
            "tribe_id":   tribe_id,
        })

    def send_myth_event(
        self,
        myth_name:  str,
        myth_type:  str,
        par:        tuple[str, str],
        intensity:  float,
        day:        int,
    ) -> None:
        """Encola un evento myth_crystallized para enviarlo al servidor."""
        self._outgoing.put({
            "type":      "myth_crystallized",
            "sim_id":    self.sim_id,
            "myth_name": myth_name,
            "myth_type": myth_type,
            "par":       list(par),
            "intensity": round(intensity, 3),
            "day":       day,
        })

    def drain_incoming(self) -> list[dict]:
        """
        Retorna y vacía todos los eventos entrantes del servidor.
        Llamar desde el thread principal de la simulación (es thread-safe).
        """
        events = []
        while True:
            try:
                events.append(self._incoming.get_nowait())
            except queue.Empty:
                break
        return events

    # ── Thread de red ─────────────────────────────────────────────────────────

    def _thread_main(self, host: str, port: int) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_loop(host, port))
        finally:
            self._loop.close()

    async def _connect_loop(self, host: str, port: int) -> None:
        """Reconecta automáticamente si se pierde la conexión."""
        uri = f"ws://{host}:{port}"
        while self._running:
            try:
                logger.info(f"Conectando a {uri}...")
                async with websockets.connect(uri) as ws:
                    self._connected = True
                    logger.info(f"Conectado al servidor liminal.")
                    await self._session(ws)
            except (OSError, websockets.exceptions.WebSocketException) as e:
                self._connected = False
                if self._running:
                    logger.warning(f"Conexión perdida ({e}). Reintentando en 5s...")
                    await asyncio.sleep(5)
            except Exception as e:
                self._connected = False
                logger.error(f"Error inesperado en LiminalClient: {e}")
                if self._running:
                    await asyncio.sleep(5)
        self._connected = False

    async def _session(self, ws) -> None:
        """Maneja una conexión activa: envía registro, luego pump bidireccional."""
        # Enviar sim_connect
        await ws.send(json.dumps({
            "type":    "sim_connect",
            "sim_id":  self.sim_id,
            "seed":    self.seed,
            "version": _PROTOCOL_VERSION,
        }, ensure_ascii=False))

        # Pump bidireccional: recibir del servidor + enviar de la queue
        recv_task = asyncio.create_task(self._recv_loop(ws))
        send_task = asyncio.create_task(self._send_loop(ws))

        done, pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _recv_loop(self, ws) -> None:
        async for raw in ws:
            try:
                msg = json.loads(raw)
                self._incoming.put(msg)
                # Callbacks opcionales
                mt = msg.get("type")
                if mt == "agent_arrived" and self.on_agent_arrived:
                    self.on_agent_arrived(msg)
                elif mt == "sim_joined" and self.on_sim_joined:
                    self.on_sim_joined(msg)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error procesando mensaje: {e}")

    async def _send_loop(self, ws) -> None:
        while self._running:
            # Drenar la queue de salida en bloques
            msgs = []
            try:
                msgs.append(self._outgoing.get_nowait())
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue

            # Intentar drenar más mensajes en el mismo ciclo
            while True:
                try:
                    msgs.append(self._outgoing.get_nowait())
                except queue.Empty:
                    break

            for msg in msgs:
                try:
                    await ws.send(json.dumps(msg, ensure_ascii=False))
                except websockets.exceptions.ConnectionClosed:
                    return
