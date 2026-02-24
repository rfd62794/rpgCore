import pygame
import math
import random
from typing import List, Tuple, Optional
from loguru import logger

from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.progress_bar import ProgressBar
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession

# New visibility for Slime variety
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.apps.slime_breeder.entities.slime import Slime
from src.shared.genetics import generate_random
from src.shared.physics import Vector2

class DungeonRoomScene(Scene):
    def __init__(self, manager, session: DungeonSession, **kwargs):
        super().__init__(manager, **kwargs)
        self.session = session
        
        self.bg_color = (15, 10, 10) # Darker cave feel
        self.panel_bg = (25, 25, 30)
        
        # Grid settings
        self.tile_size = 48
        self.grid_rows = 9
        self.grid_cols = 9
        # Center grid in room area (avoiding top info and bottom buttons)
        self.grid_offset_x = (self.manager.width - (self.grid_cols * self.tile_size)) // 2
        self.grid_offset_y = 100
        
        # Atmospheric state
        self.torch_flicker = 1.0
        self.torch_timer = 0.0
        
        # Room logic state
        self.hero_grid_pos = [4, 1]
        self.hero_render_offset = Vector2(0, 0) # For attack/flee visuals
        
        self.enemy_grid_pos = [4, 4]
        self.enemy_patrol_dir = 1 # 1 = right, -1 = left
        self.enemy_patrol_timer = 0.0
        self.enemy_patrol_speed = 1.0 # sec per cell
        self.enemy_patrol_range = 2
        self.enemy_defeated = False
        
        # Entity renderers
        self.slime_renderer = SlimeRenderer()
        self.slime_entity = Slime("Slime", generate_random(), (0, 0))
        
        self.panels = []
        self.buttons = []
        self._build_ui()

    def on_enter(self, **kwargs) -> None:
        if not self.session.floor:
            self.session.descend()
        # Reset scene state for new room
        self.enemy_defeated = False
        self.enemy_grid_pos = [4, 4]
        self._build_ui()

    def on_exit(self) -> None:
        pass

    def _build_ui(self):
        self.panels = []
        self.buttons = []
        w, h = self.manager.width, self.manager.height

        if not self.session.floor:
            return

        room = self.session.floor.get_current_room()
        
        # Room Info Top
        info_panel = Panel(pygame.Rect(20, 20, w - 40, 60), bg_color=self.panel_bg)
        info_panel.add_child(Label(pygame.Rect(35, 35, 400, 30), text=f"Floor {self.session.floor.depth} - {room.id} ({room.room_type.upper()})", font_size=20, color=(200, 200, 200)))
        self.panels.append(info_panel)

        # Bottom Actions
        action_y = h - 160
        btn_attack = Button(pygame.Rect(50, action_y, 120, 40), text="Attack", on_click=self._handle_attack)
        btn_flee = Button(pygame.Rect(180, action_y, 120, 40), text="Flee", on_click=self._handle_flee)
        self.buttons.extend([btn_attack, btn_flee])

        # Navigation (Only if room clear)
        if self.enemy_defeated or not room.has_enemies():
            nav_y = h - 80
            nx = 50
            for conn_id in room.connections:
                btn_nav = Button(pygame.Rect(nx, nav_y, 120, 40), text=f"-> {conn_id}", on_click=lambda cid=conn_id: self._handle_move(cid))
                self.buttons.append(btn_nav)
                nx += 130

    def _handle_attack(self):
        if self.enemy_defeated: return
        logger.info("⚔️ Attack requested")
        # Visual step forward
        self.hero_render_offset = Vector2(0, 40)
        # Immediate defeat for this demo pass
        self.enemy_defeated = True
        self._build_ui()

    def _handle_flee(self):
        logger.info("🏃 Flee requested")
        self.hero_render_offset = Vector2(0, -40)
        # Small delay then exit
        self.request_scene("the_room", session=self.session)

    def _handle_move(self, target_id: str):
        if self.session.floor.move_to(target_id):
            self.on_enter()

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt_ms: float) -> None:
        dt = dt_ms / 1000.0
        
        # 1. Torch Flicker
        self.torch_timer += dt
        self.torch_flicker = 1.0 + math.sin(self.torch_timer * 4.0) * 0.1
        
        # 2. Hero Move Decay
        if self.hero_render_offset.magnitude() > 1:
            self.hero_render_offset *= 0.8
            
        # 3. Enemy Patrol
        if not self.enemy_defeated:
            self.enemy_patrol_timer += dt
            if self.enemy_patrol_timer >= self.enemy_patrol_speed:
                self.enemy_patrol_timer = 0
                self.enemy_grid_pos[0] += self.enemy_patrol_dir
                
                # Check range relative to center (4)
                if abs(self.enemy_grid_pos[0] - 4) >= self.enemy_patrol_range:
                    self.enemy_patrol_dir *= -1
                    
        # Update slime visuals position
        ex = self.grid_offset_x + (self.enemy_grid_pos[0] + 0.5) * self.tile_size
        ey = self.grid_offset_y + (self.enemy_grid_pos[1] + 0.5) * self.tile_size
        self.slime_entity.kinematics.position = Vector2(ex, ey)

    def _get_tile_rect(self, col: int, row: int) -> pygame.Rect:
        return pygame.Rect(
            self.grid_offset_x + col * self.tile_size,
            self.grid_offset_y + row * self.tile_size,
            self.tile_size,
            self.tile_size
        )

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(self.bg_color)
        
        # 1. Room Border (Stone Walls)
        border_rect = pygame.Rect(
            self.grid_offset_x - 10, self.grid_offset_y - 10,
            (self.grid_cols * self.tile_size) + 20,
            (self.grid_rows * self.tile_size) + 20
        )
        pygame.draw.rect(surface, (40, 40, 45), border_rect) # Dark Stone
        pygame.draw.rect(surface, (60, 60, 70), border_rect, 2) # Outer edge
        
        # 2. Torch Flicker
        torch_color = (int(200 * self.torch_flicker), int(100 * self.torch_flicker), 0)
        # Draw 4 torches at corners
        for tx, ty in [(border_rect.left, border_rect.top), (border_rect.right, border_rect.top),
                       (border_rect.left, border_rect.bottom), (border_rect.right, border_rect.bottom)]:
            pygame.draw.circle(surface, torch_color, (tx, ty), 8)
        
        # 3. Grid Floor
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                rect = self._get_tile_rect(c, r)
                color = (30, 25, 25) if (r + c) % 2 == 0 else (35, 30, 30)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (20, 15, 15), rect, 1) # Subtle tile border

        # 4. Hero
        hw, hh = 30, 40
        hx = self.grid_offset_x + (self.hero_grid_pos[0] + 0.5) * self.tile_size + self.hero_render_offset.x
        hy = self.grid_offset_y + (self.hero_grid_pos[1] + 0.5) * self.tile_size + self.hero_render_offset.y
        hero_rect = pygame.Rect(hx - hw//2, hy - hh//2, hw, hh)
        pygame.draw.rect(surface, (100, 255, 100), hero_rect) # Hero Green
        # Hero direction indicator (down)
        pygame.draw.line(surface, (255, 255, 255), (hx, hy), (hx, hy + 15), 3)

        # 5. Enemy
        if not self.enemy_defeated:
            self.slime_renderer.render(surface, self.slime_entity)
            
        # 6. Exit Flag (at 7,7)
        if self.enemy_defeated:
            flag_rect = self._get_tile_rect(7, 7)
            fx, fy = flag_rect.centerx, flag_rect.centery
            # Triangle on stick
            pygame.draw.line(surface, (100, 100, 100), (fx, fy + 15), (fx, fy - 15), 2)
            # Gold pulse
            pulse = math.sin(self.torch_timer * 5.0) * 0.5 + 0.5
            gold = (int(200 + 55 * pulse), int(180 + 35 * pulse), 50)
            pygame.draw.polygon(surface, gold, [(fx, fy - 15), (fx + 15, fy - 7), (fx, fy)])

        # UI Layers
        for p in self.panels:
            p.render(surface)
        for btn in self.buttons:
            btn.render(surface)
