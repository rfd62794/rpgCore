import pygame
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession

class TheRoomScene(Scene):
    """
    The Hub scene — The Room.
    A dark bedroom with interactive elements.
    """
    def __init__(self, manager, session: DungeonSession, **kwargs):
        super().__init__(manager, **kwargs)
        self.session = session
        
        # Aesthetic colors
        self.bg_color = (15, 12, 12) # Dark reddish black
        self.panel_bg = (25, 20, 20)
        self.torch_accent = (200, 100, 40)
        self.text_color = (220, 210, 200)

        self.panels = []
        self.buttons = []
        
        self._build_ui()

    def on_enter(self, **kwargs) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _build_ui(self):
        self.panels = []
        self.buttons = []
        
        w, h = self.manager.width, self.manager.height

        # Main Panels
        main_panel = Panel(pygame.Rect(20, 20, w - 40, h - 160), bg_color=self.panel_bg)
        self.panels.append(main_panel)

        # Flavor Text
        flavor_panel = Panel(pygame.Rect(20, h - 130, w - 40, 110), bg_color=(18, 15, 15))
        flavor_text = "A worn bedroom. Peeling wallpaper. A chest in the corner. A ladder descends into darkness beneath a frayed rug."
        flavor_panel.add_child(Label(pygame.Rect(35, h - 115, w - 70, 80), text=flavor_text, font_size=20, color=self.text_color))
        self.panels.append(flavor_panel)

        # Hall of Ancestors (Right side of main panel)
        ancestor_x = w - 240
        main_panel.add_child(Label(pygame.Rect(ancestor_x, 40, 200, 25), text="Hall of Ancestors", font_size=22, color=self.torch_accent))
        
        ancestors = self.session.get_ancestor_list()
        ay = 75
        for ancestor_str in ancestors[-10:]: # Show last 10
            main_panel.add_child(Label(pygame.Rect(ancestor_x, ay, 200, 20), text=ancestor_str, font_size=16, color=(160, 150, 140)))
            ay += 25

        # Buttons
        # Chest (Top Left)
        btn_chest = Button(pygame.Rect(40, 40, 120, 40), text="Open Chest", on_click=self._handle_chest)
        self.buttons.append(btn_chest)

        # Ladder Down (Center)
        btn_ladder = Button(pygame.Rect(w // 2 - 80, h // 2 - 60, 160, 50), text="Go Down", on_click=self._handle_descend)
        self.buttons.append(btn_ladder)

        # Escape Rope (Bottom Right of main panel) - grayed out/inactive in hub usually
        btn_rope = Button(pygame.Rect(w - 180, h - 200, 140, 40), text="Escape Rope", on_click=None) # Grayed out by lack of on_click if logic allows
        self.buttons.append(btn_rope)

    def _handle_chest(self):
        self.request_scene("inventory", session=self.session)

    def _handle_descend(self):
        if not self.session.hero:
            self.session.start_run("fighter") # Default to fighter for now
        else:
            self.session.descend()
        self.request_scene("dungeon_room", session=self.session)


    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt_ms: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(self.bg_color)
        
        for p in self.panels:
            p.render(surface)
            
        for btn in self.buttons:
            btn.render(surface)
