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
        self.dungeon_team = None
        self.racing_team = None
        self.ui_components = []

    def on_enter(self) -> None:
        self.roster = load_roster()
        self.dungeon_team = self.roster.get_dungeon_team()
        self.racing_team = self.roster.get_racing_team()
        self._setup_ui()

    def _setup_ui(self):
        self.ui_components = []
        
        # 1. Panels
        self.left_panel = Panel(self.layout.left_panel, self.spec, variant="surface")
        self.ui_components.append(self.left_panel)
        
        self.center_panel = Panel(self.layout.center_area, self.spec, variant="surface")
        self.ui_components.append(self.center_panel)
        
        self.right_panel = Panel(self.layout.right_panel, self.spec, variant="surface")
        self.ui_components.append(self.right_panel)
        
        self.action_panel = Panel(self.layout.action_bar, self.spec, variant="surface")
        self.ui_components.append(self.action_panel)
        
        # 2. Headers
        dungeon_header = Label("DUNGEON TEAM", (self.layout.left_panel.x + 20, 15), self.spec, size="lg", bold=True)
        self.ui_components.append(dungeon_header)
        
        dungeon_subtext = Label("4 slots — enters the ruins together", (self.layout.left_panel.x + 20, 35), self.spec, size="sm", color=(160, 160, 180))
        self.ui_components.append(dungeon_subtext)
        
        racing_header = Label("RACING TEAM", (self.layout.center_area.x + 20, 15), self.spec, size="lg", bold=True)
        self.ui_components.append(racing_header)
        
        racing_subtext = Label("1 slot — competes in the derby", (self.layout.center_area.x + 20, 35), self.spec, size="sm", color=(160, 160, 180))
        self.ui_components.append(racing_subtext)
        
        # 3. Action Buttons
        back_btn = Button("← Garden", pygame.Rect(20, self.layout.action_bar.y + 10, 150, 44), 
                          self._back_to_garden, self.spec, variant="secondary")
        self.ui_components.append(back_btn)
        
        if self.dungeon_team.members:
            enter_btn = Button("ENTER DUNGEON →", 
                               pygame.Rect(self.layout.action_bar.width - 220, self.layout.action_bar.y + 10, 200, 44),
                               self._enter_dungeon, self.spec, variant="primary")
            self.ui_components.append(enter_btn)

        # 4. Dungeon Team Slots (Left Panel)
        for i in range(4):
            slot_y = self.layout.left_panel.y + 60 + (i * (self.spec.card_height + 20))
            if i < len(self.dungeon_team.members):
                slime = self.dungeon_team.members[i]
                card = ProfileCard(slime, (self.layout.left_panel.x + 20, slot_y), self.spec)
                self.ui_components.append(card)
                
                if not slime.locked:
                    rem_btn = Button("Remove", pygame.Rect(self.layout.left_panel.x + 20, slot_y + self.spec.card_height + 5, 100, 30),
                                     lambda s=slime: self._remove_from_dungeon(s), self.spec, variant="ghost")
                    self.ui_components.append(rem_btn)
            else:
                # Empty Slot
                empty_rect = pygame.Rect(self.layout.left_panel.x + 20, slot_y, self.spec.card_width, self.spec.card_height)
                Panel(empty_rect, self.spec, variant="surface", border=True).add_to(self.ui_components)
                Label("EMPTY", (empty_rect.centerx, empty_rect.centery), self.spec, centered=True).add_to(self.ui_components)

        # 5. Racing Team Slot (Center Panel - larger)
        racing_slot_y = self.layout.center_area.y + 60
        racing_slot_rect = pygame.Rect(self.layout.center_area.x + 20, racing_slot_y, 
                                      self.layout.center_area.width - 40, self.spec.card_height + 40)
        
        if self.racing_team.members:
            slime = self.racing_team.members[0]
            # Create larger racing card
            racing_card = self._create_racing_card(slime, racing_slot_rect)
            self.ui_components.append(racing_card)
            
            if not slime.locked:
                rem_btn = Button("Remove", pygame.Rect(racing_slot_rect.x + 20, racing_slot_rect.bottom - 35, 100, 30),
                                     lambda s=slime: self._remove_from_racing(s), self.spec, variant="ghost")
                self.ui_components.append(rem_btn)
        else:
            # Empty Racing Slot
            Panel(racing_slot_rect, self.spec, variant="surface", border=True).add_to(self.ui_components)
            Label("EMPTY", (racing_slot_rect.centerx, racing_slot_rect.centery), self.spec, centered=True, size="lg").add_to(self.ui_components)
        
        # 6. Available Slimes (Right Panel)
        Label("AVAILABLE SLIMES", (self.layout.right_panel.x + 20, self.layout.right_panel.y + 10), 
               self.spec, size="md", bold=True).add_to(self.ui_components)
        
        # Team assignment rules
        rules_y = self.layout.right_panel.y + self.layout.right_panel.height - 80
        Label("ASSIGNMENT RULES:", (self.layout.right_panel.x + 20, rules_y), self.spec, size="sm", bold=True).add_to(self.ui_components)
        Label("• Dungeon: 4 slimes, locked during runs", (self.layout.right_panel.x + 20, rules_y + 20), self.spec, size="xs", color=(140, 140, 160)).add_to(self.ui_components)
        Label("• Racing: 1 slime, speed determines performance", (self.layout.right_panel.x + 20, rules_y + 35), self.spec, size="xs", color=(140, 140, 160)).add_to(self.ui_components)
        
        # Available slimes list
        unassigned = self.roster.unassigned()
        for i, slime in enumerate(unassigned):
            if i >= 4: break
            row_y = self.layout.right_panel.y + 40 + (i * 70)
            row_rect = pygame.Rect(self.layout.right_panel.x + 10, row_y, self.layout.right_panel.width - 20, 65)
            Panel(row_rect, self.spec, variant="surface", border=True).add_to(self.ui_components)
            
            # Mini info: name, level, culture
            Label(slime.name, (row_rect.x + 10, row_rect.y + 5), self.spec, size="sm", bold=True).add_to(self.ui_components)
            Label(f"Lv.{slime.level} {slime.genome.cultural_base.value.title()}", 
                  (row_rect.x + 10, row_rect.y + 22), self.spec, size="xs", color=(160, 160, 180)).add_to(self.ui_components)
            
            # Assign buttons
            btn_y = row_rect.y + 40
            btn_width = 65
            
            if not self.dungeon_team.is_full():
                dungeon_btn = Button("⚔", pygame.Rect(row_rect.x + 10, btn_y, btn_width, 20),
                                         lambda s=slime: self._assign_to_dungeon(s), self.spec, variant="primary")
                self.ui_components.append(dungeon_btn)
            
            if not self.racing_team.is_full():
                racing_btn = Button("◎", pygame.Rect(row_rect.x + 80, btn_y, btn_width, 20),
                                        lambda s=slime: self._assign_to_racing(s), self.spec, variant="secondary")
                self.ui_components.append(racing_btn)

    def _back_to_garden(self):
        self.request_scene("garden")

    def _enter_dungeon(self):
        logger.info("⚔️ Launching Dungeon Crawler...")
        self.request_scene("dungeon")

    def _assign_to_dungeon(self, slime: RosterSlime):
        if self.dungeon_team.assign(slime):
            save_roster(self.roster)
            self._setup_ui()

    def _assign_to_racing(self, slime: RosterSlime):
        if self.racing_team.assign(slime):
            save_roster(self.roster)
            self._setup_ui()

    def _remove_from_dungeon(self, slime: RosterSlime):
        if self.dungeon_team.remove(slime.slime_id):
            save_roster(self.roster)
            self._setup_ui()

    def _remove_from_racing(self, slime: RosterSlime):
        if self.racing_team.remove(slime.slime_id):
            save_roster(self.roster)
            self._setup_ui()

    def _create_racing_card(self, slime: RosterSlime, rect: pygame.Rect):
        """Create a larger racing-focused profile card"""
        from src.shared.teams.stat_calculator import calculate_hp, calculate_attack, calculate_speed
        
        # Background
        bg_color = self.spec.color_surface_alt if slime.is_elder else self.spec.color_surface
        border_color = self.spec.color_accent if slime.is_elder else self.spec.color_border
        
        card = Panel(rect, self.spec, variant="surface", border=True)
        card.bg_color = bg_color
        card.border_color = border_color
        
        # Portrait (larger, left side)
        portrait_size = 80
        portrait_rect = pygame.Rect(rect.x + 20, rect.y + 20, portrait_size, portrait_size)
        # We'll render this in the panel's render method
        
        # Name and level
        name_x = rect.x + portrait_size + 40
        Label(slime.name, (name_x, rect.y + 20), self.spec, size="lg", bold=True).add_to(card.children)
        Label(f"Lv.{slime.level}", (rect.right - 80, rect.y + 20), self.spec, size="md", color=(200, 200, 100)).add_to(card.children)
        
        # Culture badge
        culture_color = {
            "ember": (200, 80, 40), "crystal": (140, 200, 255), "moss": (80, 180, 80),
            "coastal": (80, 140, 180), "void": (100, 40, 140), "mixed": (140, 140, 140)
        }.get(slime.genome.cultural_base.value, (140, 140, 140))
        
        # Stats (racing focused)
        hp = calculate_hp(slime.genome, slime.level)
        atk = calculate_attack(slime.genome, slime.level)
        spd = calculate_speed(slime.genome, slime.level)
        
        stats_y = rect.y + 60
        Label(f"HP: {hp}", (name_x, stats_y), self.spec, size="sm", color=(200, 100, 100)).add_to(card.children)
        Label(f"ATK: {atk}", (name_x + 80, stats_y), self.spec, size="sm", color=(220, 140, 60)).add_to(card.children)
        Label(f"SPD: {spd}", (name_x + 160, stats_y), self.spec, size="sm", color=(100, 180, 220), bold=True).add_to(card.children)
        
        # Speed emphasis
        Label("SPEED determines racing performance", (name_x, stats_y + 25), self.spec, size="xs", color=(140, 140, 160)).add_to(card.children)
        
        return card

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
