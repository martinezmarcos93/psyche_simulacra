"""
visualizer.py — Visualizador en tiempo real de PSYCHE SIMULACRA usando Pygame.

Uso:
    python scripts/visualizer.py                     # Nueva sesión, 30 días
    python scripts/visualizer.py --resume            # Reanuda último checkpoint
    python scripts/visualizer.py --fps 20            # Cambia la velocidad
"""

import argparse
import sys
import math
import threading
from pathlib import Path

# Asegurar que el raíz del proyecto esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simulation import SimulationRunner
import pygame

# --- Configuración Visual ---
BIOME_COLORS = {
    "bosque_templado": (34, 139, 34),
    "pradera_humeda": (154, 205, 50),
    "rio_lago": (65, 105, 225),
    "montana_alta": (169, 169, 169),
    "sabana_abierta": (218, 165, 32),
    "pantano_costero": (85, 107, 47),
    "cueva": (105, 105, 105),
    "valle_fertil": (0, 128, 0),
    "costa_abierta": (244, 164, 96),
    "desierto_borde": (237, 201, 175),
    "colinas_suaves": (189, 183, 107),
    "lago_interior": (30, 144, 255),
}

UNEXPLORED_COLOR = (20, 20, 20)
AGENT_COLOR = (255, 50, 50)
AGENT_TEXT_COLOR = (255, 255, 255)
HUD_BG_COLOR = (0, 0, 0, 150)


def hex_to_pixel(q: int, r: int, size: float):
    """Convierte coordenadas axiales (q, r) a píxeles (x, y) (Pointy-Top)."""
    x = size * math.sqrt(3) * (q + r / 2)
    y = size * 3 / 2 * r
    return x, y

def draw_hexagon(surface, color, x, y, size):
    """Dibuja un hexágono Pointy-Top."""
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        hx = x + size * math.cos(angle_rad)
        hy = y + size * math.sin(angle_rad)
        points.append((hx, hy))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (50, 50, 50), points, 1)  # Borde


class Visualizer:
    def __init__(self, runner: SimulationRunner, target_fps: int = 10):
        self.runner = runner
        self.target_fps = target_fps
        
        pygame.init()
        self.width, self.height = 1280, 720
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("PSYCHE SIMULACRA - Live Visualizer")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 14)
        self.hud_font = pygame.font.SysFont("Consolas", 18, bold=True)
        
        # Cámara
        self.hex_size = 15.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        
        # Centrar cámara inicialmente en el centro del mapa (40, 30)
        cx, cy = hex_to_pixel(40, 30, self.hex_size)
        self.offset_x = self.width / 2 - cx
        self.offset_y = self.height / 2 - cy
        
        self.running = True
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        
    def start_simulation_thread(self, days):
        """Inicia el motor de simulación en un hilo secundario con velocidad reducida."""
        # Limitar la velocidad para que sea visible (ej. 10 ticks por segundo)
        # Si target_fps es 10, queremos 0.1 segundos por tick.
        self.runner.clock.set_speed(1.0 / self.target_fps)
        
        def run_sim():
            print("Simulación iniciada en background...")
            self.runner.run(n_days=days)
            print("Simulación finalizada.")
            
        self.sim_thread = threading.Thread(target=run_sim, daemon=True)
        self.sim_thread.start()
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.runner.shutdown()
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            
            # Zoom con rueda del ratón
            elif event.type == pygame.MOUSEWHEEL:
                old_size = self.hex_size
                self.hex_size = max(5.0, min(100.0, self.hex_size + event.y * 2.0))
                
                # Ajustar offset para hacer zoom hacia el centro de la pantalla
                scale = self.hex_size / old_size
                self.offset_x = self.width / 2 - (self.width / 2 - self.offset_x) * scale
                self.offset_y = self.height / 2 - (self.height / 2 - self.offset_y) * scale

            # Panning (Desplazamiento con clic izquierdo o derecho)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 or event.button == 3:
                    self.dragging = True
                    self.last_mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 or event.button == 3:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    self.offset_x += dx
                    self.offset_y += dy
                    self.last_mouse_pos = event.pos

    def render(self):
        self.screen.fill((30, 30, 40))  # Océano / Vacío
        
        # 1. Dibujar Mundo Explorada
        explored_coords = set(self.runner.world.terrain.explored_coords())
        
        # Para optimizar, solo dibujamos los hexes que están en la vista o simplemente todos
        # El mapa es de 4800, pygame aguanta dibujarlos todos si no es muy grande.
        for r in range(self.runner.world.terrain.HEIGHT):
            for q in range(self.runner.world.terrain.WIDTH):
                if (q, r) in explored_coords:
                    cell = self.runner.world.terrain.get(q, r)
                    color = BIOME_COLORS.get(cell.biome, (100, 100, 100))
                else:
                    color = UNEXPLORED_COLOR
                    
                px, py = hex_to_pixel(q, r, self.hex_size)
                sx = px + self.offset_x
                sy = py + self.offset_y
                
                # Culling básico: no dibujar si está fuera de pantalla
                if -self.hex_size <= sx <= self.width + self.hex_size and -self.hex_size <= sy <= self.height + self.hex_size:
                    draw_hexagon(self.screen, color, sx, sy, self.hex_size)

        # 2. Dibujar Agentes
        for agent in self.runner.agents.agents.values():
            if not agent.is_alive:
                continue
                
            q, r = agent.posicion
            px, py = hex_to_pixel(q, r, self.hex_size)
            sx = px + self.offset_x
            sy = py + self.offset_y
            
            if -self.hex_size <= sx <= self.width + self.hex_size and -self.hex_size <= sy <= self.height + self.hex_size:
                # Dibujar cuerpo
                pygame.draw.circle(self.screen, AGENT_COLOR, (int(sx), int(sy)), max(4, int(self.hex_size * 0.4)))
                # Dibujar nombre
                if self.hex_size > 10:  # Mostrar nombre solo si el zoom es suficiente
                    text_surface = self.font.render(agent.id, True, AGENT_TEXT_COLOR)
                    text_rect = text_surface.get_rect(center=(int(sx), int(sy - self.hex_size * 0.8)))
                    self.screen.blit(text_surface, text_rect)

        # 3. Dibujar HUD
        hud_surface = pygame.Surface((300, 150), pygame.SRCALPHA)
        hud_surface.fill(HUD_BG_COLOR)
        
        status_text = [
            f"PSYCHE SIMULACRA",
            f"-----------------",
            f"Día: {self.runner.current_dia}",
            f"Hora: {self.runner.clock.now.hora_del_dia:02d}:00",
            f"Estación: {self.runner.clock.now.estacion}",
            f"Agentes Vivos: {self.runner.alive_count}/{len(self.runner.agents.agents)}",
            f"FPS Real: {int(self.clock.get_fps())}",
        ]
        
        y_offset = 10
        for line in status_text:
            text = self.hud_font.render(line, True, (255, 255, 255))
            hud_surface.blit(text, (10, y_offset))
            y_offset += 20
            
        self.screen.blit(hud_surface, (10, 10))
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(60)  # Limitar render a 60 FPS
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="PSYCHE SIMULACRA - Visualizador")
    parser.add_argument("--resume", action="store_true", help="Reanudar desde el checkpoint más reciente")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path a un checkpoint específico")
    parser.add_argument("--days", type=int, default=30, help="Número de días a simular (default: 30)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument("--fps", type=int, default=10, help="Velocidad de simulación (ticks por segundo)")
    parser.add_argument("--seeds-file", type=str, default="data/seeds/initial_personas.yaml")
    parser.add_argument("--db", type=str, default="data/db/simulation.db")
    parser.add_argument("--checkpoints-dir", type=str, default="data/checkpoints")
    args = parser.parse_args()

    if args.resume or args.checkpoint:
        print(f"Reanudando desde checkpoint (Visualizador)...")
        runner = SimulationRunner.resume(
            checkpoint_path=args.checkpoint,
            db_path=args.db,
            checkpoint_dir=args.checkpoints_dir,
        )
    else:
        print(f"Nueva sesión | seed={args.seed} (Visualizador)")
        runner = SimulationRunner.new_session(
            seed_file=args.seeds_file,
            seed=args.seed,
            db_path=args.db,
            checkpoint_dir=args.checkpoints_dir,
        )

    viz = Visualizer(runner, target_fps=args.fps)
    
    # Iniciar motor de simulación en background
    days_to_run = None if args.days <= 0 else args.days
    viz.start_simulation_thread(days_to_run)
    
    viz.run()
    
    # Esperar a que el hilo de simulación termine de guardar el checkpoint antes de salir
    if viz.sim_thread.is_alive():
        print("Guardando checkpoint de cierre...")
        viz.sim_thread.join()


if __name__ == "__main__":
    main()
