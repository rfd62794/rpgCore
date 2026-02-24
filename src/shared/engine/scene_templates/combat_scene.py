import pygame
from typing import List, Any, Dict
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button

class CombatSceneBase(Scene):
    """
    Standard template for turn-based combat.
    Pre-wired for: HP bars, action buttons, turn order, result overlay.
    """
    def on_enter(self, **kwargs) -> None:
        self.width, self.height = self.manager.width, self.manager.height
        self.combatants = kwargs.get("combatants", [])
        self.turn_index = 0
        
        self.ui_components = []
        self._setup_combat_ui()
        self.on_combat_enter(**kwargs)

    def _setup_combat_ui(self):
        # Action Bar (Bottom)
        bar_h = 120
        self.action_panel = Panel(pygame.Rect(0, self.height - bar_h, self.width, bar_h), bg_color=(40, 20, 20))
        self.ui_components.append(self.action_panel)
        
        # Turn Order Display (Top)
        self.turn_panel = Panel(pygame.Rect(0, 0, self.width, 40), bg_color=(20, 20, 20))
        self.ui_components.append(self.turn_panel)
        self.turn_label = Label(pygame.Rect(10, 10, 400, 20), text="Turn Order: ...")
        self.turn_panel.add_child(self.turn_label)

    def on_combat_enter(self, **kwargs):
        pass

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            for comp in reversed(self.ui_components):
                if hasattr(comp, "handle_event") and comp.handle_event(event):
                    break

    def update(self, dt_ms: float) -> None:
        for comp in self.ui_components:
            comp.update(int(dt_ms))

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((30, 10, 10))
        self.render_combatants(surface)
        for comp in self.ui_components:
            comp.render(surface)

    def render_combatants(self, surface: pygame.Surface):
        """Subclasses render characters/monsters."""
        pass
