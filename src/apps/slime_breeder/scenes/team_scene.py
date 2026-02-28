import pygame
from loguru import logger
from typing import List, Optional, Tuple
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.button import Button
from src.shared.ui.label import Label
from src.shared.ui.spec import UISpec
from src.shared.ui.layouts import SelectionLayout
from src.shared.ui.profile_card import ProfileCard
from src.shared.teams.roster import Roster, TeamRole, RosterSlime
from src.shared.teams.roster_save import load_roster, save_roster

class TeamScene(Scene):
    """
    Dedicated team management screen using SelectionLayout.
    """
    def __init__(self, manager, spec: UISpec, **kwargs):
        super().__init__(manager, spec, **kwargs)
        self.layout = SelectionLayout(spec)
        self.roster = None
        self.team = None
        self.ui_components = []

    def on_enter(self) -> None:
        self.roster = load_roster()
        self.team = self.roster.get_dungeon_team()
        self._setup_ui()

    def _setup_ui(self):
        self.ui_components = []
        
        # 1. Panels
        self.left_panel = Panel(self.layout.left_panel, self.spec, variant="surface")
        self.ui_components.append(self.left_panel)
        
        self.right_panel = Panel(self.layout.right_panel, self.spec, variant="surface")
        self.ui_components.append(self.right_panel)
        
        self.action_panel = Panel(self.layout.action_bar, self.spec, variant="surface")
        self.ui_components.append(self.action_panel)
        
        # 2. Header
        header_label = Label("DUNGEON TEAM", (20, 15), self.spec, size="xl", bold=True)
        self.ui_components.append(header_label)
        
        # 3. Action Buttons
        back_btn = Button("← Garden", pygame.Rect(20, self.layout.action_bar.y + 10, 150, 44), 
                          self._back_to_garden, self.spec, variant="secondary")
        self.ui_components.append(back_btn)
        
        if self.team.members:
            enter_btn = Button("ENTER DUNGEON →", 
                               pygame.Rect(self.layout.action_bar.width - 220, self.layout.action_bar.y + 10, 200, 44),
                               self._enter_dungeon, self.spec, variant="primary")
            self.ui_components.append(enter_btn)

        # 4. Team Slots (Left Panel)
        Label("CURRENT TEAM", (self.layout.left_panel.x + 20, self.layout.left_panel.y + 10), 
               self.spec, size="md", bold=True).add_to(self.ui_components)
               
        for i in range(4):
            slot_y = self.layout.left_panel.y + 40 + (i * (self.spec.card_height + 40))
            if i < len(self.team.members):
                slime = self.team.members[i]
                card = ProfileCard(slime, (self.layout.left_panel.x + 20, slot_y), self.spec)
                self.ui_components.append(card)
                
                if not slime.locked:
                    rem_btn = Button("Remove", pygame.Rect(self.layout.left_panel.x + 20, slot_y + self.spec.card_height + 5, 100, 30),
                                     lambda s=slime: self._remove(s), self.spec, variant="ghost")
                    self.ui_components.append(rem_btn)
            else:
                # Empty Slot Label/Box
                empty_rect = pygame.Rect(self.layout.left_panel.x + 20, slot_y, self.spec.card_width, self.spec.card_height)
                Panel(empty_rect, self.spec, variant="surface", border=True).add_to(self.ui_components)
                Label("EMPTY", (empty_rect.centerx, empty_rect.centery), self.spec, centered=True).add_to(self.ui_components)

        # 5. Available Slimes (Right Panel)
        Label("AVAILABLE SLIMES", (self.layout.right_panel.x + 20, self.layout.right_panel.y + 10), 
               self.spec, size="md", bold=True).add_to(self.ui_components)
               
        unassigned = self.roster.unassigned()
        for i, slime in enumerate(unassigned):
            if i >= 6: break
            row_y = self.layout.right_panel.y + 40 + (i * 80)
            row_rect = pygame.Rect(self.layout.right_panel.x + 10, row_y, self.layout.right_panel.width - 20, 70)
            Panel(row_rect, self.spec, variant="surface", border=True).add_to(self.ui_components)
            
            Label(slime.name, (row_rect.x + 10, row_rect.y + 10), self.spec, bold=True).add_to(self.ui_components)
            
            if not self.team.is_full():
                add_btn = Button("Add", pygame.Rect(row_rect.right - 70, row_rect.y + 10, 60, 30),
                                 lambda s=slime: self._assign(s), self.spec, variant="primary")
                self.ui_components.append(add_btn)

    def _back_to_garden(self):
        self.request_scene("garden")

    def _enter_dungeon(self):
        logger.info("⚔️ Launching Dungeon Crawler...")
        self.request_scene("dungeon_ready")

    def _assign(self, slime: RosterSlime):
        if self.team.assign(slime):
            save_roster(self.roster)
            self._setup_ui()

    def _remove(self, slime: RosterSlime):
        if self.team.remove(slime.slime_id):
            save_roster(self.roster)
            self._setup_ui()

    def handle_event(self, event: pygame.event.Event) -> None:
        for comp in reversed(self.ui_components):
            if hasattr(comp, "handle_event") and comp.handle_event(event):
                break

    def update(self, dt: float) -> None:
        for comp in self.ui_components:
            comp.update(int(dt * 1000))

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(self.spec.color_bg)
        for comp in self.ui_components:
            comp.render(surface)

    def on_exit(self):
        save_roster(self.roster)
