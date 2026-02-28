import pygame
from typing import List, Any, Optional, Tuple
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.button import Button
from src.shared.ui.base import UIComponent
from src.shared.physics import Vector2

class GardenSceneBase(Scene):
    """
    Standard template for entity creation and ambient interaction.
    Layout: 70% Garden (Left), 30% Details (Right), Bottom Action Bar.
    """
    def on_enter(self, **kwargs) -> None:
        self.width, self.height = self.manager.width, self.manager.height
        self.panel_width = int(self.width * 0.3)
        self.bar_height = 80
        
        self.garden_rect = pygame.Rect(0, 0, self.width - self.panel_width, self.height - self.bar_height)
        self.detail_rect = pygame.Rect(self.width - self.panel_width, 0, self.panel_width, self.height - self.bar_height)
        self.bar_rect = pygame.Rect(0, self.height - self.bar_height, self.width, self.bar_height)
        
        self.ui_components: List[UIComponent] = []
        self.selected_entities: List[Any] = []
        
        self._base_setup_ui()
        self.on_garden_enter(**kwargs)

    def _base_setup_ui(self):
        self.detail_panel = Panel(self.detail_rect, title="Entity Details", bg_color=(40, 40, 50))
        self.ui_components.append(self.detail_panel)
        
        self.action_bar = Panel(self.bar_rect, bg_color=(30, 30, 40))
        self.ui_components.append(self.action_bar)

    def on_exit(self) -> None:
        """Cleanup logic."""
        pass

    def on_garden_enter(self, **kwargs):
        """Hook for subclasses to add extra UI components."""
        pass

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            
            # 1. UI Interaction
            consumed = False
            for comp in reversed(self.ui_components):
                if hasattr(comp, "handle_event") and comp.handle_event(event):
                    consumed = True
                    break
            if consumed: continue
            
            # 2. Entity Selection
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.garden_rect.collidepoint(event.pos):
                    entity = self.pick_entity(event.pos)
                    mods = pygame.key.get_mods()
                    is_shift = mods & pygame.KMOD_SHIFT
                    
                    if entity:
                        if is_shift:
                            if entity in self.selected_entities:
                                self.selected_entities.remove(entity)
                            else:
                                self.selected_entities.append(entity)
                        else:
                            self.selected_entities = [entity]
                    else:
                        if not is_shift:
                            self.selected_entities = []
                    self.on_selection_changed()

    def pick_entity(self, pos: Tuple[int, int]) -> Optional[Any]:
        """Subclasses implement collision check."""
        return None

    def on_selection_changed(self):
        """Hook for subclasses when selection updates."""
        pass

    def update(self, dt_ms: float) -> None:
        for comp in self.ui_components:
            comp.update(int(dt_ms))
        self.update_garden(dt_ms)

    def update_garden(self, dt_ms: float):
        """Subclasses implement entity updates."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 20))
        self.render_garden(surface)
        for comp in self.ui_components:
            comp.render(surface)

    def render_garden(self, surface: pygame.Surface):
        """Subclasses implement entity rendering."""
        pass

    def on_exit(self) -> None:
        """Cleanup logic."""
        pass
