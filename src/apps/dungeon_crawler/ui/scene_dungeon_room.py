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

from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.apps.slime_breeder.entities.slime import Slime
from src.shared.genetics import generate_random
from src.shared.physics import Vector2

class DungeonRoomScene(Scene):
    def __init__(self, manager, session: DungeonSession, **kwargs):
        super().__init__(manager, **kwargs)
        self.session = session
        
        self.bg_color = (15, 10, 10)
        self.panel_bg = (25, 25, 30)
        
        # Grid settings
        self.tile_size = 48
        self.grid_rows = 9
        self.grid_cols = 9
        self.grid_offset_x = (self.manager.width - (self.grid_cols * self.tile_size)) // 2
        self.grid_offset_y = 100
        
        # Atmospheric state
        self.torch_flicker = 1.0
        self.torch_timer = 0.0
        
        # Room logic state
        self.hero_grid_pos = [4, 1]
        self.enemy_grid_pos = [4, 4]
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
        
        # Check for combat result
        res = kwargs.get("combat_result")
        if res == "victory":
            self.enemy_defeated = True
            logger.info("🏆 Victory confirmed in Exploration Mode")
            
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

        # Exploration Actions (No Attack button)
        action_y = h - 80
        btn_flee = Button(pygame.Rect(50, action_y, 120, 40), text="Flee (ESC)", on_click=self._handle_flee)
        self.buttons.append(btn_flee)

        # Navigation (Exit Flag logic)
        if self.enemy_defeated or not room.has_enemies():
            nx = 200
            for conn_id in room.connections:
                btn_nav = Button(pygame.Rect(nx, action_y, 120, 40), text=f"-> {conn_id}", on_click=lambda cid=conn_id: self._handle_move(cid))
                self.buttons.append(btn_nav)
                nx += 130

    def _handle_flee(self):
        logger.info("🏃 Flee to previous room")
        self.request_scene("the_room", session=self.session)

    def _handle_move(self, target_id: str):
        if self.session.floor.move_to(target_id):
            # Reset enemy state for new room (in a real game, this is in room object)
            self.enemy_defeated = False
            self.hero_grid_pos = [4, 1]
            self.enemy_grid_pos = [4, 4]
            self._build_ui()

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        room = self.session.floor.get_current_room()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN:
                moved = False
                if event.key in [pygame.K_w, pygame.K_UP]:
                    self.hero_grid_pos[1] = max(0, self.hero_grid_pos[1] - 1)
                    moved = True
                elif event.key in [pygame.K_s, pygame.K_DOWN]:
                    self.hero_grid_pos[1] = min(self.grid_rows - 1, self.hero_grid_pos[1] + 1)
                    moved = True
                elif event.key in [pygame.K_a, pygame.K_LEFT]:
                    self.hero_grid_pos[0] = max(0, self.hero_grid_pos[0] - 1)
                    moved = True
                elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                    self.hero_grid_pos[0] = min(self.grid_cols - 1, self.hero_grid_pos[0] + 1)
                    moved = True
                elif event.key == pygame.K_ESCAPE:
                    self._handle_flee()
                
                if moved:
                    self._check_collision()
                    if not self.enemy_defeated:
                        self._enemy_turn()
                        self._check_collision()

            for btn in self.buttons:
                btn.handle_event(event)

    def _enemy_turn(self):
        """Enemies move toward hero."""
        if self.enemy_defeated: return
        
        dx = self.hero_grid_pos[0] - self.enemy_grid_pos[0]
        dy = self.hero_grid_pos[1] - self.enemy_grid_pos[1]
        
        # Simple mindless AI: move on axis with largest distance
        if abs(dx) > abs(dy):
            self.enemy_grid_pos[0] += 1 if dx > 0 else -1
        elif dy != 0:
            self.enemy_grid_pos[1] += 1 if dy > 0 else -1

    def _check_collision(self):
        if self.enemy_defeated: return
        if self.hero_grid_pos == self.enemy_grid_pos:
            logger.info("💥 COLLISION! Entering Combat...")
            self.request_scene("dungeon_combat", session=self.session, enemy_entity=self.slime_entity)

    def update(self, dt_ms: float) -> None:
        dt = dt_ms / 1000.0
        self.torch_timer += dt
        self.torch_flicker = 1.0 + math.sin(self.torch_timer * 4.0) * 0.1
        
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
        
        # 1. Border
        grid_w = self.grid_cols * self.tile_size
        grid_h = self.grid_rows * self.tile_size
        pygame.draw.rect(surface, (40, 40, 45), (self.grid_offset_x - 10, self.grid_offset_y - 10, grid_w + 20, grid_h + 20))
        
        # 2. Torches
        torch_color = (int(200 * self.torch_flicker), int(100 * self.torch_flicker), 0)
        for tx, ty in [(self.grid_offset_x-10, self.grid_offset_y-10), (self.grid_offset_x+grid_w+10, self.grid_offset_y-10)]:
            pygame.draw.circle(surface, torch_color, (tx, ty), 8)
        
        # 3. Grid
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                rect = self._get_tile_rect(c, r)
                color = (30, 25, 25) if (r + c) % 2 == 0 else (35, 30, 30)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (20, 15, 15), rect, 1)

        # 4. Hero
        hx = self.grid_offset_x + (self.hero_grid_pos[0] + 0.5) * self.tile_size
        hy = self.grid_offset_y + (self.hero_grid_pos[1] + 0.5) * self.tile_size
        pygame.draw.rect(surface, (100, 255, 100), (hx - 15, hy - 20, 30, 40))

        # 5. Enemy
        if not self.enemy_defeated:
            self.slime_renderer.render(surface, self.slime_entity)
            
        # 6. Exit Flag (at 7,7)
        if self.enemy_defeated:
            flag_rect = self._get_tile_rect(7, 7)
            fx, fy = flag_rect.centerx, flag_rect.centery
            pygame.draw.line(surface, (100, 100, 100), (fx, fy + 15), (fx, fy - 15), 2)
            gold = (230, 190, 50)
            pygame.draw.polygon(surface, gold, [(fx, fy - 15), (fx + 15, fy - 7), (fx, fy)])

        for p in self.panels: p.render(surface)
        for b in self.buttons: b.render(surface)
