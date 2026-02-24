import pygame
import math
from typing import List, Any, Dict, Optional
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from loguru import logger

class CombatSceneBase(Scene):
    """
    Standard template for turn-based 5v5 combat.
    Proportions (FF-Style):
    - Top: 8% (Turn Order)
    - Bottom: 15% (Button Bar)
    - Middle: Remainder (Party Slots | Action Log | Enemy Slots)
    """
    def __init__(self, manager, **kwargs):
        super().__init__(manager, **kwargs)
        self.log_messages: List[str] = []
        self.party: List[Optional[Any]] = [None] * 5
        self.enemies: List[Optional[Any]] = [None] * 5
        self.active_actor_id: Optional[str] = None
        self.target_actor_id: Optional[str] = None
        
        # Flash feedback state
        self.flash_timer = 0.0
        self.flash_color: Optional[tuple] = None
        
        self.ui_components = []
        self.padding = 8
        self.font_n = None
        self.font_s = None
        self.font_l = None

    def on_enter(self, **kwargs) -> None:
        self.width = self.manager.width
        self.height = self.manager.height
        print(f"DEBUG: Pygame Window Height detected as {self.height}px")
        logger.info(f"Combat scene window size: {self.width}x{self.height}")
        
        # Initialize fonts
        self.font_n = pygame.font.SysFont(None, 20) # Name
        self.font_s = pygame.font.SysFont(None, 16) # Stance
        self.font_l = pygame.font.SysFont(None, 16) # Log
        
        self._calculate_layout()
        self._setup_combat_ui()
        self.on_combat_enter(**kwargs)

    def _calculate_layout(self):
        w, h = self.width, self.height
        p = self.padding
        
        # Proportions - prioritized from bottom up
        self.bottom_h = int(h * 0.15)
        self.top_h = int(h * 0.08)
        
        # Mid occupies everything between (with top padding for slots)
        self.mid_h = h - self.top_h - self.bottom_h - (3 * p)
        
        # Widths
        self.side_w = int(w * 0.25)
        self.center_w = int(w * 0.50)
        
        # Rects
        self.top_rect = pygame.Rect(0, 0, w, self.top_h)
        self.bottom_rect = pygame.Rect(0, h - self.bottom_h, w, self.bottom_h)
        self.mid_rect = pygame.Rect(0, self.top_h + 2*p, w, self.mid_h)
        
        self.party_rect = pygame.Rect(p, self.mid_rect.y, self.side_w - 2*p, self.mid_h)
        self.log_rect = pygame.Rect(self.side_w + p, self.mid_rect.y, self.center_w - 2*p, self.mid_h)
        self.enemy_rect = pygame.Rect(self.side_w + self.center_w + p, self.mid_rect.y, self.side_w - 2*p, self.mid_h)

        logger.debug(f"Layout Refined: Top={self.top_h}px, Mid={self.mid_h}px, Bottom={self.bottom_rect.y}px (h={self.bottom_h}px)")

    def _setup_combat_ui(self):
        self.ui_components = []
        
        # 1. Action Bar (Bottom)
        self.action_panel = Panel(self.bottom_rect, bg_color=(25, 20, 20))
        self.ui_components.append(self.action_panel)
        self._setup_action_buttons()
        
        # 2. Turn Order Display (Top)
        self.turn_panel = Panel(self.top_rect, bg_color=(15, 15, 15))
        self.ui_components.append(self.turn_panel)
        self.turn_label_active = Label(pygame.Rect(20, self.top_h//2 - 10, self.width//2 - 40, 20), text="Turn: ...", font_size=18, align="left")
        self.turn_label_next = Label(pygame.Rect(self.width//2, self.top_h//2 - 10, self.width//2 - 20, 20), text="Next: ...", font_size=18, align="right")
        self.turn_panel.add_child(self.turn_label_active)
        self.turn_panel.add_child(self.turn_label_next)
        
        # 3. Action Log (Center)
        self.log_panel = Panel(self.log_rect, bg_color=(20, 20, 25))
        self.ui_components.append(self.log_panel)

    def _setup_action_buttons(self):
        """Standard buttons evenly spaced."""
        pass

    def on_combat_enter(self, **kwargs):
        pass

    def add_log(self, message: str):
        self.log_messages.append(message)
        if len(self.log_messages) > 100:
            self.log_messages.pop(0)

    def trigger_flash(self, color: tuple, duration: float = 0.2):
        self.flash_color = color
        self.flash_timer = duration

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                print(f"DEBUG EVENT: {event.type}, pos: {getattr(event, 'pos', None)}")
            if event.type == pygame.QUIT:
                self.request_quit()
            for comp in reversed(self.ui_components):
                if hasattr(comp, "handle_event") and comp.handle_event(event):
                    if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                        print(f"DEBUG: Event consumed by {comp}")
                    break

    def update(self, dt_ms: float) -> None:
        dt = dt_ms / 1000.0
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_color = None
                
        for comp in self.ui_components:
            comp.update(int(dt_ms))

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((20, 10, 15))
        
        self._render_slots(surface)
        
        for comp in self.ui_components:
            comp.render(surface)
            
        self._render_log_content(surface)
        
        # Draw Flash
        if self.flash_color and self.flash_timer > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(100 * (self.flash_timer / 0.2))
            overlay.fill((*self.flash_color, alpha))
            surface.blit(overlay, (0, 0))

    def _render_slots(self, surface: pygame.Surface):
        # Dynamically fit slots into mid_h
        slot_h = (self.mid_h // 5) - self.padding
        
        # Render Party (Left)
        for i in range(5):
            y = self.party_rect.y + i * (slot_h + self.padding)
            self._draw_unit_slot(surface, self.party_rect.x, y, self.party_rect.width, slot_h, self.party[i], side="party")
            
        # Render Enemies (Right)
        for i in range(5):
            y = self.enemy_rect.y + i * (slot_h + self.padding)
            self._draw_unit_slot(surface, self.enemy_rect.x, y, self.enemy_rect.width, slot_h, self.enemies[i], side="enemy")

    def _draw_unit_slot(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, entity: Optional[Any], side: str):
        rect = pygame.Rect(x, y, w, h)
        
        # Base slot look
        if not entity:
            pygame.draw.rect(surface, (25, 25, 30), rect)
            pygame.draw.rect(surface, (40, 40, 45), rect, 1)
            return

        bg_col = (45, 35, 35) if side == "party" else (35, 35, 50)
        pygame.draw.rect(surface, bg_col, rect)
        
        # Highlights
        if getattr(entity, "id", None) == self.active_actor_id:
            pygame.draw.rect(surface, (255, 165, 0), rect, 2)
        elif getattr(entity, "id", None) == self.target_actor_id:
            pygame.draw.rect(surface, (255, 50, 50), rect, 2)
        else:
            pygame.draw.rect(surface, (70, 70, 80), rect, 1)
        
        # Name and HP
        name = getattr(entity, "name", "Unit")
        stats = getattr(entity, "stats", {})
        hp = stats.get("hp", 0)
        max_hp = stats.get("max_hp", 1)
        
        # Text (Name at top)
        img_n = self.font_n.render(name, True, (240, 240, 240))
        surface.blit(img_n, (x + 8, y + 6))
        
        # HP Bar (Bottom)
        bar_w = w - 16
        bar_h = min(8, h // 8)
        bar_rect = pygame.Rect(x + 8, y + h - (bar_h + 8), bar_w, bar_h)
        pygame.draw.rect(surface, (80, 20, 20), bar_rect)
        if max_hp > 0:
            fill_w = int(bar_w * (max(0, hp) / max_hp))
            pygame.draw.rect(surface, (40, 180, 40), (x+8, y + h - (bar_h + 8), fill_w, bar_h))

        # Stance (Middle for enemies)
        if side == "enemy":
            stance = stats.get("stance", "NEUTRAL").upper()
            img_s = self.font_s.render(stance, True, (150, 150, 180))
            # Offset it slightly down from name
            surface.blit(img_s, (x + 8, y + 24))

    def _render_log_content(self, surface: pygame.Surface):
        rect = self.log_rect
        visible_msgs = self.log_messages[-6:]
        
        for i, msg in enumerate(visible_msgs):
            # Calculate fade
            alpha = int(100 + (i * 155 // 5)) # 100 to 255
            color = (alpha, alpha, alpha)
            
            img = self.font_l.render(f"> {msg}", True, color)
            surface.blit(img, (rect.x + 10, rect.y + 10 + i * 18))

    def on_exit(self) -> None:
        pass
