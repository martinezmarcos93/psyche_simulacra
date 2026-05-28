"""
main.py — Punto de entrada del servidor LIMINAL ZONE.

Modo headless (sin Pygame). Expone:
  - WebSocket en ws://host:port  (protocolo de interconexión de simulaciones)
  - HTTP GET /state en http://host:port+1  (estado para NiceGUI / dashboard)
  - HTTP GET /health en http://host:port+1 (liveness probe)

Uso:
    python main.py
    python main.py --host 0.0.0.0 --port 8765 --seed 0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from aiohttp import web

import config
from core.liminal_world import LiminalWorld
from core.liminal_clock import LiminalClock
from core.simulation_registry import SimulationRegistry
from core.agent_registry import AgentRegistry
from transport.websocket_server import LiminalServer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("liminal.main")


# ── Endpoint HTTP /state ──────────────────────────────────────────────────────

def _build_state_handler(world: LiminalWorld, clock: LiminalClock,
                         sim_registry: SimulationRegistry,
                         agent_registry: AgentRegistry):
    async def state_handler(request: web.Request) -> web.Response:
        hexes = [
            {"q": h.q, "r": h.r, "sub_biome": h.sub_biome}
            for h in world.all_cells()
        ]
        agents = [
            {
                "agent_id":  a.agent_id,
                "nombre":    a.nombre,
                "from_sim":  a.from_sim,
                "pos":       list(a.pos),
                "arquetipo": a.dominant_archetype,
            }
            for a in agent_registry.all()
        ]
        sims = [
            {
                "sim_id":   sid,
                "n_agents": len(agent_registry.by_sim(sid)),
            }
            for sid in sim_registry.sim_ids()
        ]
        data = {
            "tick":     clock.tick,
            "n_sims":   sim_registry.count(),
            "n_agents": agent_registry.count(),
            "hexes":    hexes,
            "agents":   agents,
            "sims":     sims,
        }
        return web.Response(
            text=json.dumps(data),
            content_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    return state_handler


async def _run_http(world, clock, sim_registry, agent_registry, host: str, http_port: int):
    """Levanta el servidor HTTP con aiohttp en el event loop actual."""
    app = web.Application()
    app.router.add_get("/state",  _build_state_handler(world, clock, sim_registry, agent_registry))
    app.router.add_get("/health", lambda r: web.Response(text="ok"))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, http_port)
    await site.start()
    logger.info(f"HTTP /state disponible en http://{host}:{http_port}/state")
    return runner


# ── Clock ticker ──────────────────────────────────────────────────────────────

async def _clock_ticker(clock: LiminalClock, server: LiminalServer,
                        interval: float = 2.0) -> None:
    """Avanza el reloj liminal y ejecuta la lógica de retorno cada interval segundos."""
    while True:
        await asyncio.sleep(interval)
        clock.advance()
        server.tick()


# ── Entry point ───────────────────────────────────────────────────────────────

async def _run(args: argparse.Namespace) -> None:
    http_port = args.port + 1

    world          = LiminalWorld(seed=args.seed)
    clock          = LiminalClock()
    sim_registry   = SimulationRegistry()
    agent_registry = AgentRegistry()

    server = LiminalServer(
        world=world,
        clock=clock,
        sim_registry=sim_registry,
        agent_registry=agent_registry,
        host=args.host,
        port=args.port,
    )

    http_runner = await _run_http(world, clock, sim_registry, agent_registry,
                                   args.host, http_port)

    print()
    print("=" * 52)
    print("  LIMINAL ZONE — Servidor activo (headless)")
    print(f"  WebSocket : ws://{args.host}:{args.port}")
    print(f"  HTTP /state: http://{args.host}:{http_port}/state")
    print(f"  Mapa      : {world.WIDTH}x{world.HEIGHT} hexagonos")
    print(f"  Seed      : {args.seed}")
    print("=" * 52)
    print()
    print("  Esperando simulaciones... (Ctrl+C para detener)")
    print()

    try:
        await asyncio.gather(
            server.serve(),
            _clock_ticker(clock, server),
        )
    finally:
        await http_runner.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description="LIMINAL ZONE — Servidor de interconexion")
    parser.add_argument("--host", default=config.SERVER_HOST)
    parser.add_argument("--port", type=int, default=config.SERVER_PORT)
    parser.add_argument("--seed", type=int, default=config.WORLD_SEED)
    args = parser.parse_args()

    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
