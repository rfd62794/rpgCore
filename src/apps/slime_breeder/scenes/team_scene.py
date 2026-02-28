import pygame
from loguru import logger
from typing import List, Optional, Tuple
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.button import Button
from src.shared.ui.label import Label
from src.shared.ui.profile_card import ProfileCard, render_text
from src.shared.teams.roster import Roster, TeamRole, RosterSlime
from src.shared.teams.roster_save import load_roster, save_roster

class TeamScene(Scene):
    """
    Dedicated team management screen.
    Accessed from garden via "TEAMS" button.
    Shows all roster slots, assign/remove actions.
    """
    
    DUNGEON_SLOTS = 4
    
    def on_enter(self, **kwargs) -> None:
        self.width, self.height = self.manager.width, self.manager.height
        self.roster = load_roster()
        self.team = self.roster.get_dungeon_team()
        
        self.ui_components: List[pygame.sprite.Sprite] = [] # Using a list for manual update/render
        self.buttons: List[Button] = []
        
        self._setup_ui()

    def _setup_ui(self):
        self.buttons = []
        
        # Back button
        back_btn = Button(
            pygame.Rect(40, self.height - 70, 150, 40), 
            text="← Garden", 
            on_click=self._back_to_garden
        )
        self.buttons.append(back_btn)
        
        # Enter Dungeon button (bottom right)
        if self.team.members:
            enter_btn = Button(
                pygame.Rect(self.width - 240, self.height - 70, 200, 40),
                text="ENTER DUNGEON →",
                bg_color_normal=(180, 60, 60),
                on_click=self._enter_dungeon
            )
            self.buttons.append(enter_btn)

        # Create buttons for each unassigned slime
        unassigned = self.roster.unassigned()
        for i, slime in enumerate(unassigned):
            if i >= 6: break # Limit display for now
            card_y = 100 + (i * 90)
            if not self.team.is_full():
                btn = Button(
                    pygame.Rect(600, card_y, 120, 30),
                    text="→ Dungeon",
                    on_click=lambda s=slime: self._assign(s)
                )
                self.buttons.append(btn)
                
        # Remove buttons for team members
        for i, slime in enumerate(self.team.members):
            slot_y = 100 + (i * 150)
            if not slime.locked:
                btn = Button(
                    pygame.Rect(320, slot_y + 40, 100, 30),
                    text="Remove",
                    on_click=lambda s=slime: self._remove(s)
                )
                self.buttons.append(btn)

    def _back_to_garden(self):
        self.request_scene("garden")

    def _enter_dungeon(self):
        # In a real integration, this would switch to the dungeon crawler application/scene
        # For this demo, we'll assume the manager has it registered or we trigger a handoff.
        self.request_scene("dungeon_ready") # Placeholder or specific scene

    def _assign(self, slime: RosterSlime):
        if self.team.assign(slime):
            save_roster(self.roster)
            self._setup_ui() # Refresh buttons

    def _remove(self, slime: RosterSlime):
        if self.team.remove(slime.slime_id):
            save_roster(self.roster)
            self._setup_ui() # Refresh buttons

    def on_exit(self) -> None:
        save_roster(self.roster)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            for btn in self.buttons:
                if btn.handle_event(event):
                    break

    def update(self, dt_ms: float) -> None:
        for btn in self.buttons:
            btn.update(int(dt_ms))

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((25, 25, 35))
        
        # Header
        render_text(surface, "DUNGEON TEAM", (40, 30), size=32, bold=True)
        render_text(surface, "Your slimes that enter the ruins.", 
                   (40, 65), size=18, color=(140, 140, 160))
        
        # Four team slots
        for i in range(self.DUNGEON_SLOTS):
            slot_y = 100 + (i * 150)
            slot_rect = pygame.Rect(40, slot_y, 300, 140)
            
            if i < len(self.team.members):
                slime = self.team.members[i]
                card = ProfileCard(slime, (40, slot_y))
                card.render(surface)
            else:
                # Empty slot
                pygame.draw.rect(surface, (20, 20, 30), slot_rect, border_radius=8)
                pygame.draw.rect(surface, (50, 50, 70), slot_rect, width=1, border_radius=8)
                render_text(surface, "— Empty Slot —",
                           (slot_rect.centerx - 50, slot_rect.centery - 10),
                           size=18, color=(70, 70, 90))
        
        # Unassigned slimes panel (right side)
        render_text(surface, "AVAILABLE SLIMES", (450, 30), 
                   size=24, bold=True)
        
        unassigned = self.roster.unassigned()
        for i, slime in enumerate(unassigned):
            if i >= 6: break
            card_y = 100 + (i * 90)
            row_rect = pygame.Rect(450, card_y - 10, 320, 80)
            pygame.draw.rect(surface, (30, 30, 40), row_rect, border_radius=8)
            
            # Mini info (could be a mini card, for now just text)
            render_text(surface, slime.name, (460, card_y), size=18, bold=True)
            render_text(surface, f"HP: {slime.genome.energy*100:.0f}", (460, card_y + 25), size=14, color=(140, 140, 160))
        
        # Render buttons
        for btn in self.buttons:
            btn.render(surface)
