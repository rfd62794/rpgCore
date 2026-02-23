import pygame
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.progress_bar import ProgressBar
from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession

class DungeonRoomScene(Scene):
    def __init__(self, manager, session: DungeonSession, **kwargs):
        super().__init__(manager, **kwargs)
        self.session = session
        
        self.bg_color = (5, 5, 8)
        self.panel_bg = (20, 20, 25)
        self.accent_color = (150, 150, 180)

        self.panels = []
        self.buttons = []
        
        self._build_ui()

    def on_enter(self, **kwargs) -> None:
        if not self.session.floor:
            self.session.descend()
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
        info_panel.add_child(Label(pygame.Rect(35, 35, 300, 30), text=f"Floor {self.session.floor.depth} - {room.id} ({room.room_type.upper()})", font_size=20, color=(200, 200, 200)))
        # Explore counter stub
        info_panel.add_child(Label(pygame.Rect(w - 200, 35, 150, 30), text="Explored: ?/?", font_size=18, color=(150, 150, 150)))
        self.panels.append(info_panel)

        # Center: Enemy Display
        if room.has_enemies():
            enemy_panel = Panel(pygame.Rect(w // 2 - 200, h // 2 - 150, 400, 200), bg_color=(30, 30, 35))
            for i, enemy in enumerate(room.enemies):
                ey = 40 + i * 80
                enemy_panel.add_child(Label(pygame.Rect(20, ey, 200, 25), text=enemy.name, font_size=22, color=(255, 100, 100)))
                
                hp_val = enemy.stats.get("hp", 0)
                max_hp = enemy.stats.get("max_hp", 1)
                hp_bar = ProgressBar(pygame.Rect(20, ey + 30, 360, 15), progress=hp_val/max_hp, color=(200, 50, 50))
                enemy_panel.add_child(hp_bar)
                
                stance = enemy.stance_controller.current.value.upper()
                enemy_panel.add_child(Label(pygame.Rect(w // 2 + 50, ey, 100, 20), text=stance, font_size=16, color=(150, 150, 150)))
            self.panels.append(enemy_panel)
        else:
            msg_panel = Panel(pygame.Rect(w // 2 - 150, h // 2 - 50, 300, 100), bg_color=self.panel_bg)
            msg_panel.add_child(Label(pygame.Rect(50, 40, 200, 20), text="Room is clear.", font_size=24, color=(100, 255, 100)))
            self.panels.append(msg_panel)

        # Bottom Actions
        action_y = h - 180
        btn_attack = Button(pygame.Rect(50, action_y, 120, 40), text="Attack", on_click=self._handle_attack)
        btn_flee = Button(pygame.Rect(180, action_y, 120, 40), text="Flee", on_click=self._handle_flee)
        btn_item = Button(pygame.Rect(310, action_y, 120, 40), text="Item", on_click=None)
        self.buttons.extend([btn_attack, btn_flee, btn_item])

        # Navigation
        nav_y = h - 100
        nx = 50
        for conn_id in room.connections:
            btn_nav = Button(pygame.Rect(nx, nav_y, 120, 40), text=f"-> {conn_id}", on_click=lambda cid=conn_id: self._handle_move(cid))
            self.buttons.append(btn_nav)
            nx += 130

    def _handle_attack(self):
        # Stub: just log for now
        logger.info("⚔️ Attack requested")
        # In a real impl, this would trigger combat logic in session
        self._build_ui()

    def _handle_flee(self):
        logger.info("🏃 Flee requested")
        self.request_scene("the_room", session=self.session)

    def _handle_move(self, target_id: str):
        if self.session.floor.move_to(target_id):
            self._build_ui()

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                self.request_scene("inventory", session=self.session)

                
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
