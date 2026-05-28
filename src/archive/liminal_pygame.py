"""
visualizer/liminal_pygame.py — Ventana Pygame de la Zona Liminal.

Muestra el mapa hexagonal etéreo con los agentes de todas las
simulaciones conectadas. Corre en el thread principal del servidor.
"""

from __future__ import annotations

import math
import pygame

from core.liminal_world import LiminalWorld, SUB_BIOME_COLORS_DEF
from core.agent_registry import AgentRegistry
from core.simulation_registry import SimulationRegistry
from core.liminal_clock import LiminalClock


# ── Paleta de colores ────────────────────────────────────────────────────────

# Se importa SUB_BIOME_COLORS_DEF desde liminal_world para que sean consistentes.
# Aquí también definimos los colores por sim de origen.
SIM_COLORS = [
    (100, 180, 255),   # SIM 0 — azul (PC-A por defecto)
    (255, 130, 110),   # SIM 1 — rojo suave (PC-B)
    ( 90, 230, 140),   # SIM 2 — verde
    (255, 220,  80),   # SIM 3 — amarillo
    (220, 120, 255),   # SIM 4 — magenta
]

SIDEBAR_W = 260
BG_COLOR  = (5, 4, 15)


# ── Utilidades hexagonales ───────────────────────────────────────────────────

def hex_to_pixel(q: int, r: int, size: float) -> tuple[float, float]:
    """Convierte coordenadas axiales a píxeles (Pointy-Top)."""
    x = size * math.sqrt(3) * (q + r / 2)
    y = size * 3 / 2 * r
    return x, y


def draw_hex(surface, color, x: float, y: float, size: float,
             border: tuple | None = None) -> None:
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        pts.append((x + size * math.cos(a), y + size * math.sin(a)))
    pygame.draw.polygon(surface, color, pts)
    if border:
        pygame.draw.polygon(surface, border, pts, 1)


# ── Clase principal ──────────────────────────────────────────────────────────

class LiminalPygame:
    """
    Ventana Pygame que visualiza la Zona Liminal en tiempo real.
    Corre en el thread principal (main.py la llama en su loop).
    """

    def __init__(
        self,
        world:          LiminalWorld,
        agent_registry: AgentRegistry,
        sim_registry:   SimulationRegistry,
        clock:          LiminalClock,
    ) -> None:
        self.world          = world
        self.agent_registry = agent_registry
        self.sim_registry   = sim_registry
        self.clock          = clock

        pygame.init()
        self.W, self.H = 1100, 700
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
        pygame.display.set_caption("PSYCHE SIMULACRA — ZONA LIMINAL")

        self.pg_clock  = pygame.time.Clock()
        self.font_sm   = pygame.font.SysFont("Consolas", 13)
        self.font_md   = pygame.font.SysFont("Consolas", 16, bold=True)
        self.font_lg   = pygame.font.SysFont("Consolas", 22, bold=True)

        # Cámara
        self.hex_size = 24.0
        cx, cy = hex_to_pixel(self.world.WIDTH // 2, self.world.HEIGHT // 2, self.hex_size)
        self.cam_x = (self.W - SIDEBAR_W) // 2 - cx
        self.cam_y = self.H // 2 - cy
        self.dragging     = False
        self.last_mouse   = (0, 0)

        # Animación
        self._pulse = 0.0

        # Mapeo sim_id → índice de color
        self._sim_color_idx: dict[str, int] = {}
        self._next_color_idx = 0

        self.running = True

    # ── Color por sim ────────────────────────────────────────────────────────

    def _sim_color(self, sim_id: str) -> tuple:
        if sim_id not in self._sim_color_idx:
            self._sim_color_idx[sim_id] = self._next_color_idx % len(SIM_COLORS)
            self._next_color_idx += 1
        return SIM_COLORS[self._sim_color_idx[sim_id]]

    # ── Eventos Pygame ───────────────────────────────────────────────────────

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.VIDEORESIZE:
                self.W, self.H = event.w, event.h
                self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEWHEEL:
                old = self.hex_size
                self.hex_size = max(8.0, min(60.0, self.hex_size + event.y * 2.0))
                scale = self.hex_size / old
                mid_x = (self.W - SIDEBAR_W) // 2
                self.cam_x = mid_x - (mid_x - self.cam_x) * scale
                self.cam_y = self.H // 2 - (self.H // 2 - self.cam_y) * scale
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                self.dragging   = True
                self.last_mouse = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                dx = event.pos[0] - self.last_mouse[0]
                dy = event.pos[1] - self.last_mouse[1]
                self.cam_x += dx
                self.cam_y += dy
                self.last_mouse = event.pos
        return True

    # ── Render ───────────────────────────────────────────────────────────────

    def render(self) -> None:
        self._pulse = (self._pulse + 0.04) % (2 * math.pi)
        self.screen.fill(BG_COLOR)
        map_w = self.W - SIDEBAR_W

        # --- Mapa hexagonal ---
        for cell in self.world.all_cells():
            px, py = hex_to_pixel(cell.q, cell.r, self.hex_size)
            sx = px + self.cam_x
            sy = py + self.cam_y
            if -self.hex_size <= sx <= map_w + self.hex_size and \
               -self.hex_size <= sy <= self.H + self.hex_size:
                color = SUB_BIOME_COLORS_DEF.get(cell.sub_biome, (20, 18, 40))
                draw_hex(self.screen, color, sx, sy, self.hex_size - 1,
                         border=(30, 25, 55))

        # --- Agentes ---
        for agent in self.agent_registry.all():
            q, r = agent.pos
            px, py = hex_to_pixel(q, r, self.hex_size)
            sx = px + self.cam_x
            sy = py + self.cam_y
            if -self.hex_size <= sx <= map_w + self.hex_size and \
               -self.hex_size <= sy <= self.H + self.hex_size:
                base  = self._sim_color(agent.from_sim)
                pulse = 0.65 + 0.35 * math.sin(self._pulse)
                glow  = tuple(min(255, int(c * pulse)) for c in base)
                r_px  = max(5, int(self.hex_size * 0.42))
                # Halo
                pygame.draw.circle(self.screen, (25, 20, 50), (int(sx), int(sy)), r_px + 4)
                # Cuerpo
                pygame.draw.circle(self.screen, glow, (int(sx), int(sy)), r_px)
                # Nombre
                if self.hex_size > 14:
                    lbl = self.font_sm.render(agent.nombre[:10], True, (200, 200, 230))
                    self.screen.blit(lbl, lbl.get_rect(center=(int(sx), int(sy - self.hex_size * 0.9))))

        # --- Línea divisora del sidebar ---
        pygame.draw.line(self.screen, (40, 35, 70), (map_w, 0), (map_w, self.H), 1)

        # --- Sidebar ---
        self._draw_sidebar(map_w + 8)

        pygame.display.flip()

    def _draw_sidebar(self, x: int) -> None:
        pygame.draw.rect(self.screen, (8, 7, 22), (x - 8, 0, SIDEBAR_W + 8, self.H))
        y = 14

        # Título
        title = self.font_lg.render("ZONA LIMINAL", True, (160, 80, 255))
        self.screen.blit(title, (x, y)); y += 32

        # Tick
        self.screen.blit(
            self.font_md.render(f"Tick: {self.clock.tick}", True, (130, 130, 210)),
            (x, y)); y += 22

        # Sims conectadas
        self.screen.blit(
            self.font_md.render(f"Sims: {self.sim_registry.count()}", True, (100, 200, 120)),
            (x, y)); y += 22

        # Agentes presentes
        self.screen.blit(
            self.font_md.render(f"Agentes: {self.agent_registry.count()}", True, (210, 170, 80)),
            (x, y)); y += 28

        # Lista de sims
        sep = self.font_sm.render("── SIMULACIONES ──", True, (90, 70, 150))
        self.screen.blit(sep, (x, y)); y += 18
        for sid in self.sim_registry.sim_ids():
            color = self._sim_color(sid)
            label = (sid[:22] + "…") if len(sid) > 23 else sid
            self.screen.blit(self.font_sm.render(f"● {label}", True, color), (x, y))
            y += 16

        y += 8

        # Lista de agentes
        sep2 = self.font_sm.render("── AGENTES ──", True, (90, 70, 150))
        self.screen.blit(sep2, (x, y)); y += 18
        agents = self.agent_registry.all()
        for agent in agents[:14]:
            color = self._sim_color(agent.from_sim)
            self.screen.blit(
                self.font_sm.render(f"  {agent.nombre[:18]}", True, color),
                (x, y)); y += 15
        if len(agents) > 14:
            self.screen.blit(
                self.font_sm.render(f"  …y {len(agents) - 14} más", True, (110, 110, 160)),
                (x, y))

    # ── Loop externo ─────────────────────────────────────────────────────────

    def run_frame(self) -> bool:
        """Procesa un frame. Retorna False si se cerró la ventana."""
        if not self.handle_events():
            return False
        self.render()
        self.pg_clock.tick(30)
        return self.running
