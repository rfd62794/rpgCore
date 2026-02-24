import pygame
import math
from typing import List, Any, Dict, Optional
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button

class CombatSceneBase(Scene):
    """
    Standard template for turn-based 5v5 combat.
    Features:
    - Top bar: Turn info and metadata
    - Middle: 5 Party slots | Action Log | 5 Enemy slots
    - Bottom: Action Bar
    - Logic: log_messages, turn tracking, hit/miss flashes
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

    def on_enter(self, **kwargs) -> None:
        self.width, self.height = self.manager.width, self.manager.height
        self._setup_combat_ui()
        self.on_combat_enter(**kwargs)

    def _setup_combat_ui(self):
        w, h = self.width, self.height
        self.ui_components = []
        
        # 1. Action Bar (Bottom) - 100px height
        bar_h = 100
        self.action_panel = Panel(pygame.Rect(0, h - bar_h, w, bar_h), bg_color=(25, 20, 20))
        self.ui_components.append(self.action_panel)
        self._setup_action_buttons()
        
        # 2. Turn Order Display (Top) - 50px height
        self.turn_panel = Panel(pygame.Rect(0, 0, w, 50), bg_color=(15, 15, 15))
        self.ui_components.append(self.turn_panel)
        self.turn_label = Label(pygame.Rect(20, 15, w - 40, 20), text="Turn Order: ...", font_size=18)
        self.turn_panel.add_child(self.turn_label)
        
        # 3. Action Log (Center) - 200px width
        log_w = 260
        self.log_panel = Panel(pygame.Rect((w - log_w)//2, 70, log_w, h - bar_h - 90), bg_color=(20, 20, 25))
        self.ui_components.append(self.log_panel)

    def _setup_action_buttons(self):
        """Subclasses can override to add specific buttons."""
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
            if event.type == pygame.QUIT:
                self.request_quit()
            for comp in reversed(self.ui_components):
                if hasattr(comp, "handle_event") and comp.handle_event(event):
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
        surface.fill((20, 10, 10)) # Darker background
        
        self._render_slots(surface)
        
        for comp in self.ui_components:
            comp.render(surface)
            
        self._render_log_content(surface)
        
        # Draw Flash
        if self.flash_color and self.flash_timer > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(100 * (self.flash_timer / 0.2)) # Fade out
            overlay.fill((*self.flash_color, alpha))
            surface.blit(overlay, (0, 0))

    def _render_slots(self, surface: pygame.Surface):
        w, h = self.width, self.height
        slot_h = 80
        start_y = 80
        gap = 10
        
        # Render Party (Left)
        for i in range(5):
            y = start_y + i * (slot_h + gap)
            self._draw_unit_slot(surface, 50, y, self.party[i], side="party")
            
        # Render Enemies (Right)
        for i in range(5):
            y = start_y + i * (slot_h + gap)
            self._draw_unit_slot(surface, w - 210, y, self.enemies[i], side="enemy")

    def _draw_unit_slot(self, surface: pygame.Surface, x: int, y: int, entity: Optional[Any], side: str):
        rect = pygame.Rect(x, y, 160, 80)
        bg_col = (40, 30, 30) if side == "party" else (30, 30, 40)
        pygame.draw.rect(surface, bg_col, rect)
        pygame.draw.rect(surface, (60, 60, 70), rect, 1)
        
        if entity:
            # Highlight Active
            if getattr(entity, "id", None) == self.active_actor_id:
                pygame.draw.rect(surface, (255, 165, 0), rect, 3) # Orange
            # Highlight Target
            if getattr(entity, "id", None) == self.target_actor_id:
                pygame.draw.rect(surface, (255, 50, 50), rect, 3) # Red
                
            # Name and HP
            name = getattr(entity, "name", "Unit")
            stats = getattr(entity, "stats", {})
            hp = stats.get("hp", 0)
            max_hp = stats.get("max_hp", 1)
            
            # Simple HP Bar within slot
            bar_rect = pygame.Rect(x + 10, y + 55, 140, 8)
            pygame.draw.rect(surface, (100, 20, 20), bar_rect)
            if max_hp > 0:
                pygame.draw.rect(surface, (50, 200, 50), (x+10, y+55, int(140 * (hp/max_hp)), 8))
            
            # Text
            font = pygame.font.SysFont(None, 20)
            img = font.render(name, True, (250, 250, 250))
            surface.blit(img, (x + 10, y + 10))

    def _render_log_content(self, surface: pygame.Surface):
        rect = self.log_panel.rect
        font = pygame.font.SysFont(None, 18)
        for i, msg in enumerate(self.log_messages[-12:]):
            img = font.render(f"> {msg}", True, (180, 180, 180))
            surface.blit(img, (rect.x + 10, rect.y + 10 + i * 20))

    def on_exit(self) -> None:
        pass
