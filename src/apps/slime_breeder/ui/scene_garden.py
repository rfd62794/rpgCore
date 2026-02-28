import pygame
import random
from loguru import logger
from typing import Optional, List, Tuple
from src.shared.engine.scene_templates.garden_scene import GardenSceneBase
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.apps.slime_breeder.garden.garden_state import GardenState
from src.apps.slime_breeder.entities.slime import Slime
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.genetics import generate_random, breed
from src.shared.teams.roster import Roster, RosterSlime, TeamRole
from src.shared.teams.roster_save import load_roster, save_roster
from src.shared.ui.profile_card import ProfileCard, render_text
from src.shared.ui.panel import Panel

NAMES = ["Mochi", "Pip", "Glimmer", "Bloop", "Sage", "Dew", "Ember", "Fizz", "Lumen", "Nook"]

class GardenScene(GardenSceneBase):
    def on_garden_enter(self, **kwargs) -> None:
        self.garden_state = GardenState()
        self.renderer = SlimeRenderer()
        self.roster = load_roster()
        self._sync_roster_with_garden()
        
        # 1. Custom Details UI (Profile Card)
        self.profile_card: Optional[ProfileCard] = None
        
        # Position buttons below the card area (Card is ~140h + margin)
        btn_y = 200
        self.assign_btn = Button(pygame.Rect(self.detail_rect.x + 10, btn_y, self.panel_width-20, 40), text="→ Dungeon Team", on_click=self._assign_to_dungeon)
        self.assign_btn.set_visible(False)
        self.detail_panel.add_child(self.assign_btn)

        self.remove_btn = Button(pygame.Rect(self.detail_rect.x + 10, btn_y, self.panel_width-20, 40), text="Remove from Team", on_click=self._remove_from_team)
        self.remove_btn.set_visible(False)
        self.detail_panel.add_child(self.remove_btn)
        
        # 2. Custom Action Bar Buttons
        btn_y = 15
        btn_w, btn_h = 120, 50
        
        self.new_btn = Button(pygame.Rect(20, btn_y, btn_w, btn_h), text="New Slime", on_click=self._add_new_slime)
        self.action_bar.add_child(self.new_btn)
        
        self.breed_btn = Button(pygame.Rect(150, btn_y, btn_w, btn_h), text="Breed", on_click=self._go_to_breeding)
        self.action_bar.add_child(self.breed_btn)

        self.release_btn = Button(pygame.Rect(280, btn_y, btn_w, btn_h), text="Release", on_click=self._release_selected)
        self.release_btn.set_enabled(False)
        self.action_bar.add_child(self.release_btn)

        # 3. Top Navigation Bar
        self.top_bar = Panel(pygame.Rect(0, 0, self.width - self.panel_width, 60), bg_color=(20, 20, 30))
        self.ui_components.append(self.top_bar)
        
        self.teams_nav_btn = Button(pygame.Rect(20, 10, 100, 40), text="TEAMS", on_click=self._go_to_teams)
        self.top_bar.add_child(self.teams_nav_btn)
        
        self.dungeon_nav_btn = Button(pygame.Rect(130, 10, 120, 40), text="DUNGEON", on_click=self._go_to_dungeon)
        self.top_bar.add_child(self.dungeon_nav_btn)

        self.racing_nav_btn = Button(pygame.Rect(260, 10, 100, 40), text="RACING", on_click=self._go_to_racing)
        self.top_bar.add_child(self.racing_nav_btn)

        # Sync initial slimes if garden is empty but roster has slimes
        if not self.garden_state.slimes and self.roster.slimes:
            for rs in self.roster.slimes:
                pos = (random.randint(50, self.garden_rect.width - 50), random.randint(50, self.garden_rect.height - 50))
                slime = Slime(rs.name, rs.genome, pos, level=rs.level)
                self.garden_state.add_slime(slime)
        elif not self.garden_state.slimes:
            self._add_new_slime()

    def _sync_roster_with_garden(self):
        """Ensure all garden slimes are in the roster."""
        for slime in self.garden_state.slimes:
            if not any(rs.name == slime.name for rs in self.roster.slimes):
                rs = RosterSlime(
                    slime_id=slime.name.lower().replace(" ", "_"),
                    name=slime.name,
                    genome=slime.genome
                )
                self.roster.add_slime(rs)
        save_roster(self.roster)

    def _add_new_slime(self):
        name = random.choice(NAMES) + " " + str(len(self.garden_state.slimes) + 1)
        genome = generate_random()
        pos = (random.randint(50, self.garden_rect.width - 50), random.randint(50, self.garden_rect.height - 50))
        slime = Slime(name, genome, pos, level=1)
        self.garden_state.add_slime(slime)
        
        # Add to roster
        rs = RosterSlime(
            slime_id=name.lower().replace(" ", "_"),
            name=name,
            genome=genome
        )
        self.roster.add_slime(rs)
        save_roster(self.roster)

    def _go_to_breeding(self):
        self.request_scene("breeding")

    def _release_selected(self):
            for s in self.selected_entities:
                print(f"DEBUG: Releasing {s.name} into the wild...")
                self.garden_state.remove_slime(s.name)
                # Remove from roster
                self.roster.slimes = [rs for rs in self.roster.slimes if rs.name != s.name]
                # Also remove from any team
                for team in self.roster.teams.values():
                    team.members = [m for m in team.members if m.name != s.name]
            
            save_roster(self.roster)
            self.selected_entities = []
            self.on_selection_changed()

    def _go_to_teams(self):
        self.request_scene("teams")

    def _go_to_racing(self):
        self.request_scene("racing")

    def _go_to_dungeon(self):
        team = self.roster.get_dungeon_team()
        if not team.members:
            self.request_scene("teams")
        else:
            # Entry point for Dungeon Crawler demo
            # In game.py logic, we'd launch the demo. 
            # Here we'll just log and maybe switch to a scene if we register it.
            logger.info("⚔️ Entering Dungeon with team...")
            # For now, transition to TeamScene as it has the ENTER button
            self.request_scene("teams")

    def pick_entity(self, pos: Tuple[int, int]) -> Optional[Slime]:
        # Return the top-most slime at pos
        for slime in reversed(self.garden_state.slimes):
            dist = (slime.kinematics.position - pygame.Vector2(*pos)).magnitude()
            if dist < 40: # Hit radius
                return slime
        return None

    def on_selection_changed(self):
        num_selected = len(self.selected_entities)
        self.release_btn.set_enabled(num_selected > 0)
        
        # Clear previous card
        if self.profile_card:
            self.detail_panel.remove_child(self.profile_card)
            self.profile_card = None

        # Update details for the primary selection
        if num_selected == 1:
            s = self.selected_entities[0]
            
            # Find in roster
            rs = next((r for r in self.roster.slimes if r.name == s.name), None)
            if rs:
                self.profile_card = ProfileCard(rs, (self.detail_rect.x + 10, 50))
                self.detail_panel.add_child(self.profile_card)
                
                if rs.locked:
                    self.assign_btn.set_visible(False)
                    self.remove_btn.set_visible(False)
                elif rs.team == TeamRole.UNASSIGNED:
                    self.assign_btn.set_visible(not self.roster.get_dungeon_team().is_full())
                    self.remove_btn.set_visible(False)
                else:
                    self.assign_btn.set_visible(False)
                    self.remove_btn.set_visible(True)
            else:
                self.assign_btn.set_visible(False)
                self.remove_btn.set_visible(False)

        else:
            self.assign_btn.set_visible(False)
            self.remove_btn.set_visible(False)

    def _assign_to_dungeon(self):
        if len(self.selected_entities) == 1:
            s = self.selected_entities[0]
            rs = next((r for r in self.roster.slimes if r.name == s.name), None)
            if rs:
                if self.roster.get_dungeon_team().assign(rs):
                    save_roster(self.roster)
                    self.on_selection_changed()

    def _remove_from_team(self):
        if len(self.selected_entities) == 1:
            s = self.selected_entities[0]
            rs = next((r for r in self.roster.slimes if r.name == s.name), None)
            if rs and rs.team != TeamRole.UNASSIGNED:
                if self.roster.teams[rs.team].remove(rs.slime_id):
                    save_roster(self.roster)
                    self.on_selection_changed()

    def update_garden(self, dt_ms: float):
        dt = dt_ms / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        # Only pass cursor if in garden area
        cursor = mouse_pos if self.garden_rect.collidepoint(mouse_pos) else None
        self.garden_state.update(dt, cursor)

    def render_garden(self, surface: pygame.Surface):
        # Background color is handled by base
        # Render Slimes
        for slime in self.garden_state.slimes:
            is_selected = (slime in self.selected_entities)
            self.renderer.render(surface, slime, is_selected)
            
        self._render_team_status_bar(surface)

    def _render_team_status_bar(self, surface: pygame.Surface):
        team = self.roster.get_dungeon_team()
        bar_rect = pygame.Rect(0, self.height - 36, self.width, 36)
        pygame.draw.rect(surface, (20, 20, 30), bar_rect)
        pygame.draw.rect(surface, (50, 50, 70), bar_rect, width=1)
        
        if not team.members:
            render_text(surface, 
                       "DUNGEON TEAM: Empty — visit Teams to assign slimes",
                       (16, self.height - 24),
                       size=18, color=(100, 100, 120))
        else:
            names = ", ".join(s.name for s in team.members)
            label = f"DUNGEON TEAM: {names} [{len(team.members)}/4]"
            render_text(surface, label,
                       (16, self.height - 24),
                       size=18, color=(180, 220, 180))

    def on_exit(self):
        """Cleanup logic."""
        pass
