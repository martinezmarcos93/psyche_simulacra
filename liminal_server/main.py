"""
main.py — Punto de entrada del servidor LIMINAL ZONE.

Arranca el servidor WebSocket en un thread de asyncio y el
visualizador Pygame en el thread principal.

Uso:
    python main.py
    python main.py --host 0.0.0.0 --port 8765 --seed 0
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import threading

import pygame

import config
from core.liminal_world import LiminalWorld
from core.liminal_clock import LiminalClock
from core.simulation_registry import SimulationRegistry
from core.agent_registry import AgentRegistry
from transport.websocket_server import LiminalServer
from visualizer.liminal_pygame import LiminalPygame


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("liminal.main")


def _run_server_thread(server: LiminalServer) -> None:
    """Corre el servidor WebSocket en un thread dedicado con su propio event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(server.serve())
    except Exception as e:
        logger.error(f"Error fatal en el servidor: {e}")
    finally:
        loop.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="LIMINAL ZONE — Servidor de interconexión")
    parser.add_argument("--host", default=config.SERVER_HOST)
    parser.add_argument("--port", type=int, default=config.SERVER_PORT)
    parser.add_argument("--seed", type=int, default=config.WORLD_SEED)
    args = parser.parse_args()

    # ── Construir el mundo compartido ────────────────────────────────────────
    logger.info(f"Inicializando LiminalWorld (seed={args.seed})")
    world          = LiminalWorld(seed=args.seed)
    clock          = LiminalClock()
    sim_registry   = SimulationRegistry()
    agent_registry = AgentRegistry()

    # ── Construir e iniciar el servidor WebSocket en background ──────────────
    server = LiminalServer(
        world=world,
        clock=clock,
        sim_registry=sim_registry,
        agent_registry=agent_registry,
        host=args.host,
        port=args.port,
    )

    srv_thread = threading.Thread(target=_run_server_thread, args=(server,), daemon=True)
    srv_thread.start()
    logger.info(f"Servidor WebSocket iniciado en ws://{args.host}:{args.port}")

    # ── Construir el visualizador Pygame (thread principal) ──────────────────
    viz = LiminalPygame(
        world=world,
        agent_registry=agent_registry,
        sim_registry=sim_registry,
        clock=clock,
    )

    logger.info("Visualizador Pygame listo — loop principal iniciado")
    print()
    print("=" * 50)
    print("  LIMINAL ZONE — Servidor activo")
    print(f"  WebSocket: ws://{args.host}:{args.port}")
    print(f"  Mapa:      {world.WIDTH}×{world.HEIGHT} hexágonos")
    print(f"  Seed:      {args.seed}")
    print("=" * 50)
    print()
    print("  Esperando simulaciones...")
    print("  Cerrá la ventana Pygame para detener el servidor.")
    print()

    # Loop principal: Pygame en foreground, servidor en background
    tick_counter = 0
    while viz.running:
        if not viz.run_frame():
            break
        # Avanzar el reloj liminal cada 60 frames (~2 segundos a 30 FPS)
        tick_counter += 1
        if tick_counter >= 60:
            clock.advance()
            server.tick()   # chequea retornos y actualiza lógica liminal
            tick_counter = 0

    pygame.quit()
    logger.info("Servidor detenido.")
    sys.exit(0)


if __name__ == "__main__":
    main()
