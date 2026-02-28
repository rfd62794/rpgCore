import pygame
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.spec import UISpec
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession

class InventoryOverlay(Scene):
    def __init__(self, manager, spec: UISpec, session: DungeonSession, **kwargs):
        super().__init__(manager, spec, **kwargs)
        self.session = session
        
        self.bg_color = (10, 10, 15, 200) # Slightly transparent dark
        self.panel_bg = (30, 30, 40)
        self.text_color = (200, 200, 210)

        self.panels = []
        self.buttons = []
        
        self._build_ui()

    def on_enter(self, **kwargs) -> None:
        self._build_ui()

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process pygame events."""
        for button in self.buttons:
            if hasattr(button, 'handle_event') and button.handle_event(event):
                return

    def update(self, dt: float) -> None:
        """Update scene state."""
        for button in self.buttons:
            if hasattr(button, 'update'):
                button.update(int(dt * 1000))

    def render(self, surface: pygame.Surface) -> None:
        """Render the scene."""
        surface.fill((0, 0, 0))  # Clear background
        
        # Render semi-transparent overlay
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        surface.blit(overlay, (0, 0))
        
        # Render panels
        for panel in self.panels:
            if hasattr(panel, 'render'):
                panel.render(surface)
        
        # Render buttons
        for button in self.buttons:
            if hasattr(button, 'render'):
                button.render(surface)

    def _build_ui(self):
        self.panels = []
        self.buttons = []
        w, h = self.manager.width, self.manager.height

        # Main Overlay Panel
        bg_rect = pygame.Rect(50, 50, w - 100, h - 100)
        main_panel = Panel(bg_rect, bg_color=self.panel_bg)
        self.panels.append(main_panel)

        # Left: Equipment Slots
        eq_y = 100
        slots = ["Head", "Body", "Weapon", "Offhand", "Accessory"]
        for slot in slots:
            main_panel.add_child(Label(pygame.Rect(80, eq_y, 100, 20), text=f"{slot}:", font_size=18, color=(150, 150, 160)))
            main_panel.add_child(Label(pygame.Rect(180, eq_y, 150, 20), text="[Empty]", font_size=18, color=(100, 100, 100)))
            eq_y += 40

        # Center: Grid Inventory (Simple 4x5)
        grid_x, grid_y = 350, 100
        cell_size = 50
        for r in range(5):
            for c in range(4):
                rect = pygame.Rect(grid_x + c * cell_size, grid_y + r * cell_size, cell_size - 2, cell_size - 2)
                # Draw grid background cells
                # pygame.draw.rect(surface, (20, 20, 25), rect) # Will be handled in render or by child panels
                main_panel.add_child(Panel(rect, bg_color=(20, 20, 25)))

        # Right: Stats Panel
        stat_x = w - 280
        main_panel.add_child(Label(pygame.Rect(stat_x, 100, 200, 25), text="Character Stats", font_size=22, color=(200, 150, 50)))
        if self.session.hero:
            stats = [
                f"HP: {self.session.hero.stats.get('hp')}/{self.session.hero.stats.get('max_hp')}",
                f"ATK: {self.session.hero.effective_stat('attack')}",
                f"DEF: {self.session.hero.effective_stat('defense')}",
                f"SPD: {self.session.hero.effective_stat('speed')}",
                f"Gold: {self.session.hero.inventory.get_gold()}"
            ]
            sy = 140
            for s in stats:
                main_panel.add_child(Label(pygame.Rect(stat_x, sy, 200, 20), text=s, font_size=18, color=self.text_color))
                sy += 30

        # Close Button
        btn_close = Button(pygame.Rect(w - 150, h - 140, 80, 40), text="Close", on_click=self._handle_close)
        self.buttons.append(btn_close)

    def _handle_close(self):
        # Return to previous scene
        self.request_scene("the_room", session=self.session) # Simple fallback, could be smarter if tracked history


    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._handle_close()
                
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt_ms: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        # Full screen dimmed overlay if desired
        overlay = pygame.Surface((self.manager.width, self.manager.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        for p in self.panels:
            p.render(surface)
        for btn in self.buttons:
            btn.render(surface)
