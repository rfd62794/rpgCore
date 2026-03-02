import pygame
import random
from loguru import logger
from typing import Optional, List, Tuple
from src.shared.engine.scene_templates.garden_scene import GardenSceneBase
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.layouts import HubLayout
from src.apps.slime_breeder.garden.garden_state import GardenState
from src.apps.slime_breeder.entities.slime import Slime
from src.shared.rendering.slime_renderer import SlimeRenderer
from src.shared.rendering.garden_renderer import GardenRenderer
from src.shared.genetics import generate_random, breed
from src.shared.teams.roster import Roster, RosterSlime, TeamRole
from src.shared.teams.roster_save import load_roster, save_roster
from src.shared.ui.profile_card import ProfileCard, render_text
from src.shared.ui.panel import Panel

NAMES = ["Mochi", "Pip", "Glimmer", "Bloop", "Sage", "Dew", "Ember", "Fizz", "Lumen", "Nook"]

class GardenScene(GardenSceneBase):
    def __init__(self, manager, spec: UISpec, **kwargs):
        super().__init__(manager, spec, **kwargs)
        self.layout = HubLayout(spec)
        
        # Get shared systems
        self.entity_registry = kwargs.get('entity_registry')
        self.game_session = kwargs.get('game_session')
        self.dispatch_system = kwargs.get('dispatch_system')
        
        # Garden area (center of screen, excluding right panel)
        self.garden_rect = pygame.Rect(
            0,
            self.layout.top_bar.height,
            self.spec.screen_width - self.layout.side_panel.width,
            self.spec.screen_height - self.layout.top_bar.height - self.layout.status_bar.height
        )
        
        # Initialize garden state
        self.garden_state = GardenState()
        
        # Initialize garden renderer with level
        self.garden_level = 0
        try:
            # Try to get garden level from GameSession
            # This is a graceful attempt - if it fails, we default to level 0
            from src.shared.session.game_session import GameSession
            # In a real implementation, this would come from scene manager or global state
            # For now, we'll default to level 0
            self.garden_level = 0
        except Exception:
            self.garden_level = 0
        
        # Initialize slime renderer
        self.renderer = SlimeRenderer()
        
        try:
            self.garden_renderer = GardenRenderer(self.garden_rect, session_id="garden_session")
        except Exception as e:
            logger.warning(f"Failed to initialize garden renderer: {e}")
            self.garden_renderer = None
        
        # Banner state
        self._banner_msg = ""
        self._banner_timer = 0.0
        self._banner_color = (255, 255, 255)
        
        # Context from return (using self._kwargs from Scene init)
        run_result = self._kwargs.get('run_result')
        race_result = self._kwargs.get('race_result')
        
        if run_result:
            floors = run_result.get('floors_cleared', 1) if isinstance(run_result, dict) else 1
            self._show_banner(f"Run complete — Floor {floors}", self.spec.color_success)
        elif race_result:
            self._show_banner(f"Race finished — {race_result['position']} place", self.spec.color_success)
            
        # Respect injected roster if provided (for UI Review)
        if not hasattr(self, "roster") or not self.roster:
            self.roster = load_roster()
            
        self._sync_roster_with_garden()
        
        # 1. Right Panel Layout (Exactly as sketched)
        padding = 8
        right_x = 880
        screen_w = self.spec.screen_width
        screen_h = self.spec.screen_height
        
        self.right_panel_rect = pygame.Rect(self.layout.side_panel.x, self.layout.side_panel.y, self.layout.side_panel.width, self.layout.side_panel.height)
        
        profile_w = int(self.right_panel_rect.width * 0.55)
        stats_w = self.right_panel_rect.width - profile_w - padding * 3
        # Shrink top panels to move buttons up
        top_h = 340
        bottom_h = self.right_panel_rect.height - top_h - padding * 3
        
        self.profile_rect = pygame.Rect(self.right_panel_rect.x + padding, self.right_panel_rect.y + padding, profile_w, top_h)
        self.stats_rect = pygame.Rect(self.profile_rect.right + padding, self.right_panel_rect.y + padding, stats_w, top_h)
        self.actions_rect = pygame.Rect(self.right_panel_rect.x + padding, self.profile_rect.bottom + padding, self.right_panel_rect.width - padding * 2, bottom_h)

        # Disable base detail_panel background to prevent overdrawing our custom sub-panels
        # This will be set in on_garden_enter after base setup

        # 2. Team Buttons (Stacked in actions_rect)
        btn_y = self.actions_rect.y + 10
        btn_w = self.actions_rect.width - 20
        btn_h = 40
        
        # We'll use these specific buttons for the actions area
        self.dungeon_btn = Button("→ Dungeon Team", pygame.Rect(self.actions_rect.x + 10, btn_y, btn_w, btn_h), self._assign_to_dungeon, self.spec)
        self.racing_btn = Button("→ Racing Team", pygame.Rect(self.actions_rect.x + 10, btn_y + btn_h + 8, btn_w, btn_h), self._assign_to_racing, self.spec)
        self.remove_btn = Button("Remove", pygame.Rect(self.actions_rect.x + 10, btn_y + btn_h + 8, btn_w, btn_h), self._remove_from_team, self.spec, variant="danger")
        self.mission_btn = Button("ON MISSION", pygame.Rect(self.actions_rect.x + 10, btn_y, btn_w, btn_h), None, self.spec, variant="warning")
        
        # Hide initially
        self.dungeon_btn.set_visible(False)
        self.racing_btn.set_visible(False)
        self.remove_btn.set_visible(False)
        self.mission_btn.set_visible(False)
        
        # Store buttons for later addition to detail_panel
        self._pending_buttons = [
            self.dungeon_btn,
            self.racing_btn, 
            self.remove_btn,
            self.mission_btn
        ]
        
        # 3. Custom Action Bar Buttons
        btn_y = self.bar_rect.y + 10
        btn_w, btn_h = 130, 44
        
        self.new_btn = Button("New Slime", pygame.Rect(20, btn_y, btn_w, btn_h), self._add_new_slime, self.spec)
        self.breed_btn = Button("Breed", pygame.Rect(160, btn_y, btn_w, btn_h), self._go_to_breeding, self.spec)
        self.release_btn = Button("Release", pygame.Rect(300, btn_y, btn_w, btn_h), self._release_selected, self.spec, variant="danger")
        self.release_btn.set_enabled(False)
        
        # Store buttons for later addition to action_bar
        self._pending_action_buttons = [
            self.new_btn,
            self.breed_btn,
            self.release_btn
        ]

        # 3. Top Navigation Bar (Using HubLayout.top_bar)
        self.top_bar = Panel(self.layout.top_bar, self.spec, variant="surface")
        self.ui_components.append(self.top_bar)
        
        nav_y = self.layout.top_bar.y + 4
        nav_h = self.layout.top_bar.height - 8
        self.teams_nav_btn = Button("TEAMS", pygame.Rect(20, nav_y, 100, nav_h), self._go_to_teams, self.spec, variant="ghost")
        self.top_bar.add_child(self.teams_nav_btn)
        
        self.dungeon_nav_btn = Button("DUNGEON", pygame.Rect(130, nav_y, 120, nav_h), self._go_to_dungeon, self.spec, variant="ghost")
        self.top_bar.add_child(self.dungeon_nav_btn)

        self.racing_nav_btn = Button("RACING", pygame.Rect(260, nav_y, 100, nav_h), self._go_to_racing, self.spec, variant="ghost")
        self.top_bar.add_child(self.racing_nav_btn)

        # Sync initial slimes if garden is empty but entity registry has slimes
        if not self.garden_state.slimes and self.entity_registry:
            for rs in self.entity_registry.all():
                pos = (random.randint(50, self.garden_rect.width - 50), random.randint(50, self.garden_rect.height - 50))
                slime = Slime(rs.name, rs.genome, pos, level=rs.level)
                self.garden_state.add_slime(slime)
        elif not self.garden_state.slimes and self.roster.slimes:
            for rs in self.roster.slimes:
                pos = (random.randint(50, self.garden_rect.width - 50), random.randint(50, self.garden_rect.height - 50))
                slime = Slime(rs.name, rs.genome, pos, level=rs.level)
                self.garden_state.add_slime(slime)
        elif not self.garden_state.slimes and self.roster.entries:
            # Fallback for new format - create slimes from entries
            for entry in self.roster.entries:
                # Try to get the actual slime from garden state or create one
                slime = self.garden_state.get_slime(entry.slime_id)
                if not slime:
                    # Create a new slime from roster entry
                    # We need to get the genome from somewhere - try garden state first
                    try:
                        # If we have garden state, try to get slime from there
                        existing_slime = self.garden_state.get_slime(entry.slime_id)
                        if existing_slime:
                            slime = existing_slime
                        else:
                            # Create new slime - we need to get genome data
                            # This is a fallback - ideally we'd get genome from saved data
                            from src.shared.genetics import generate_random
                            genome = generate_random()  # Fallback to random genome
                            pos = (random.randint(50, self.garden_rect.width - 50), random.randint(50, self.garden_rect.height - 50))
                            slime = Slime(entry.slime_id, genome, pos, level=1)
                            self.garden_state.add_slime(slime)
                    except Exception as e:
                        logger.warning(f"Could not create slime for {entry.slime_id}: {e}")
        elif not self.garden_state.slimes:
            self._add_new_slime()

    def on_garden_enter(self):
        """Set up UI components after base initialization"""
        # Disable base detail_panel background to prevent overdrawing our custom sub-panels
        self.detail_panel.bg_color = None
        self.detail_panel.border_width = 0
        
        # Add pending buttons to detail_panel
        for button in self._pending_buttons:
            self.detail_panel.add_child(button)
            
        # Add pending action buttons to action_bar
        for button in self._pending_action_buttons:
            self.action_bar.add_child(button)

    def _sync_roster_with_garden(self):
        """Ensure all garden slimes are in the roster."""
        for slime in self.garden_state.slimes:
            # Check both old and new formats
            slime_id = slime.name.lower().replace(" ", "_")
            has_old_format = any(rs.slime_id == slime_id for rs in self.roster.slimes)
            has_new_format = any(entry.slime_id == slime_id for entry in self.roster.entries)
            
            if not has_old_format and not has_new_format:
                # Create roster entry for this slime using old format for compatibility
                from src.shared.teams.roster import RosterSlime
                rs = RosterSlime(
                    slime_id=slime_id,
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
        from src.shared.teams.roster import RosterSlime
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
                self.roster.slimes = [rs for rs in self.roster.slimes if rs.slime_id != s.name.lower().replace(" ", "_")]
                self.roster.entries = [e for e in self.roster.entries if e.slime_id != s.name.lower().replace(" ", "_")]
                # Also remove from any team
                for team in self.roster.teams.values():
                    team.members = [m for m in team.members if m.slime_id != s.name.lower().replace(" ", "_")]
            
            save_roster(self.roster)
            self.selected_entities = []
            self.on_selection_changed()

    def _go_to_teams(self):
        self.request_scene("teams")

    def _go_to_racing(self):
        self.request_scene("racing")

    def _go_to_dungeon(self):
        team = self.roster.get_dungeon_team()
        if not team or len(team.members) == 0:
            self._show_banner(
                "Assign slimes to Dungeon Team first",
                color=self.spec.color_warning
            )
            return
        
        from src.apps.dungeon_crawler.ui.dungeon_session import DungeonSession
        session = DungeonSession(team=team.members)
        self.manager.switch_to(
            "dungeon_path",
            session=session,
            depth=1
        )

    def pick_entity(self, pos: Tuple[int, int]) -> Optional[Slime]:
        # Return the top-most slime at pos
        for slime in reversed(self.garden_state.slimes):
            dist = (slime.kinematics.position - pygame.Vector2(*pos)).magnitude()
            if dist < 40: # Hit radius
                return slime
        return None

    def on_selection_changed(self):
        """Update sub-panel content and button visibility based on selection."""
        # Reset visibility
        self.dungeon_btn.set_visible(False)
        self.racing_btn.set_visible(False)
        self.remove_btn.set_visible(False)
        self.mission_btn.set_visible(False)
        
        if len(self.selected_entities) == 1:
            s = self.selected_entities[0]
            # Find roster slime for this slime (check old format first)
            slime_id = s.name.lower().replace(" ", "_")
            rs = next((r for r in self.roster.slimes if r.slime_id == slime_id), None)
            if not rs:
                # Fallback to new format
                entry = next((e for e in self.roster.entries if e.slime_id == slime_id), None)
                if entry:
                    # Convert entry to rs-like object for compatibility
                    class EntryWrapper:
                        def __init__(self, entry):
                            self.slime_id = entry.slime_id
                            self.team = entry.team
                            self.locked = entry.locked
                    rs = EntryWrapper(entry)
            
            if rs:
                # Update Action Buttons based on state
                btn_y = self.actions_rect.y + 12
                if rs.locked:
                    self.mission_btn.set_visible(True)
                    self.mission_btn.set_enabled(False)
                elif rs.team == TeamRole.UNASSIGNED:
                    self.dungeon_btn.set_visible(True)
                    self.dungeon_btn.rect.y = btn_y
                    self.dungeon_btn.set_enabled(not self.roster.get_dungeon_team().is_full())
                    
                    self.racing_btn.set_visible(True)
                    self.racing_btn.rect.y = btn_y + 48
                    self.racing_btn.set_enabled(not self.roster.get_racing_team().is_full())
                else:
                    # Already on a team
                    label = "✓ Dungeon Team" if rs.team == TeamRole.DUNGEON else "✓ Racing Team"
                    btn = self.dungeon_btn if rs.team == TeamRole.DUNGEON else self.racing_btn
                    btn.text = label
                    btn.set_visible(True)
                    btn.set_enabled(False)
                    btn.rect.y = btn_y
                    
                    self.remove_btn.set_visible(True)
                    self.remove_btn.rect.y = btn_y + 48

    def _assign_to_dungeon(self):
        if len(self.selected_entities) == 1:
            s = self.selected_entities[0]
            slime_id = s.name.lower().replace(" ", "_")
            # Try old format first
            rs = next((r for r in self.roster.slimes if r.slime_id == slime_id), None)
            if rs:
                if self.roster.get_dungeon_team().assign(rs):
                    save_roster(self.roster)
                    self.on_selection_changed()
            else:
                # Try new format
                entry = next((e for e in self.roster.entries if e.slime_id == slime_id), None)
                if entry:
                    if self.roster.get_dungeon_team().assign(entry):
                        save_roster(self.roster)
                        self.on_selection_changed()

    def _assign_to_racing(self):
        if len(self.selected_entities) == 1:
            s = self.selected_entities[0]
            slime_id = s.name.lower().replace(" ", "_")
            # Try old format first
            rs = next((r for r in self.roster.slimes if r.slime_id == slime_id), None)
            if rs:
                if self.roster.get_racing_team().assign(rs):
                    save_roster(self.roster)
                    self.on_selection_changed()
            else:
                # Try new format
                entry = next((e for e in self.roster.entries if e.slime_id == slime_id), None)
                if entry:
                    if self.roster.get_racing_team().assign(entry):
                        save_roster(self.roster)
                        self.on_selection_changed()

    def _remove_from_team(self):
        if len(self.selected_entities) == 1:
            s = self.selected_entities[0]
            slime_id = s.name.lower().replace(" ", "_")
            # Try old format first
            rs = next((r for r in self.roster.slimes if r.slime_id == slime_id), None)
            if rs and rs.team != TeamRole.UNASSIGNED:
                if self.roster.teams[rs.team].remove(rs.slime_id):
                    save_roster(self.roster)
                    self.on_selection_changed()
            else:
                # Try new format
                entry = next((e for e in self.roster.entries if e.slime_id == slime_id), None)
                if entry and entry.team != TeamRole.UNASSIGNED:
                    if self.roster.teams[entry.team].remove(entry.slime_id):
                        save_roster(self.roster)
                        self.on_selection_changed()

    def update_garden(self, dt: float):
        if self._banner_timer > 0:
            self._banner_timer -= dt
        
        # Update ResourceFlow systems
        if self.game_session and self.dispatch_system:
            # Update game session tick
            self.game_session.current_tick += 1
            
            # Update active dispatches
            self.dispatch_system.current_tick = self.game_session.current_tick
            for dispatch in self.dispatch_system.active_dispatches[:]:  # Copy list to avoid modification during iteration
                if dispatch.end_tick <= self.game_session.current_tick:
                    # Dispatch completed
                    result = self.dispatch_system.resolve_dispatch(dispatch)
                    if result.success:
                        # Add resources to game session
                        for resource, amount in result.resource_gains.items():
                            self.game_session.resources[resource] = self.game_session.resources.get(resource, 0) + int(amount)
                    
                    # Move to completed
                    self.dispatch_system.active_dispatches.remove(dispatch)
                    self.dispatch_system.completed_dispatches.append(dispatch)
                    
                    # Update UI
                    self._show_banner(f"Dispatch complete! Gained: {result.message}")
            
            # Update idle zone resource generation
            self._update_idle_zones(dt)
            
        # Update garden renderer animations
        if self.garden_renderer:
            self.garden_renderer.update(dt)
            
        mouse_pos = pygame.mouse.get_pos()
        # Only pass cursor if in garden area
        cursor = mouse_pos if self.garden_rect.collidepoint(mouse_pos) else None
        self.garden_state.update(dt, cursor)

    def _update_idle_zones(self, dt: float):
        """Update idle zone resource generation"""
        if not self.game_session or not self.garden_renderer:
            return
        
        # Get idle zone target from garden renderer
        idle_target = self.garden_renderer.get_idle_zone_target()
        if not idle_target:
            return
        
        # Simple resource generation for idle zones
        # In a full implementation, this would check zone type and generate appropriate resources
        resource_generation_rate = 0.1  # Resources per second
        
        # Generate small amounts of resources
        if random.random() < resource_generation_rate * dt:
            resource_type = random.choice(['gold', 'food', 'scrap'])
            amount = random.randint(1, 3)
            self.game_session.resources[resource_type] = self.game_session.resources.get(resource_type, 0) + amount

    def render_garden(self, surface: pygame.Surface):
        # Render environmental elements before slimes
        if self.garden_renderer:
            try:
                self.garden_renderer.render_ground(surface, self.garden_level)
                self.garden_renderer.render_ship(surface)
                self.garden_renderer.render_environment(surface, self.garden_level)
            except Exception as e:
                logger.warning(f"Garden renderer failed: {e}")
                # Fallback to simple background
                surface.fill((20, 20, 30), self.garden_rect)
        
        # Render Slimes
        for slime in self.garden_state.slimes:
            is_selected = (slime in self.selected_entities)
            self.renderer.render(surface, slime, is_selected)
            
        self._render_banner(surface)
        self._render_right_panel(surface)
        self._render_team_status_bar(surface)

    def _render_right_panel(self, surface: pygame.Surface):
        from src.shared.ui.profile_card import render_text
        
        if len(self.selected_entities) != 1:
            # Show selection hint
            render_text(surface, "Select a slime", 
                       self.right_panel_rect.center, 
                       size=20, color=self.spec.color_text_dim, center=True)
            return
            
        s = self.selected_entities[0]
        rs = next((r for r in self.roster.slimes if r.name == s.name), None)
        if not rs:
            return

        # 1. Backgrounds (Draw all three first)
        for rect in [self.profile_rect, self.stats_rect, self.actions_rect]:
            pygame.draw.rect(surface, self.spec.color_surface, rect, border_radius=6)
            pygame.draw.rect(surface, self.spec.color_border, rect, width=1, border_radius=6)

        # 2. Profile Sub-panel Content
        from src.shared.ui.profile_card import render_slime_portrait, render_badge
        
        # Portrait (Top, slightly padded)
        portrait_size = 60
        portrait_rect = pygame.Rect(self.profile_rect.x + 12, self.profile_rect.y + 12, portrait_size, portrait_size)
        render_slime_portrait(surface, rs.genome, portrait_rect)
        
        # Text details
        text_x = self.profile_rect.x + 12
        y = portrait_rect.bottom + 8
        render_text(surface, rs.name, (text_x, y), size=18, bold=True)
        y += 22
        render_text(surface, f"Lv.{rs.level} | Gen {rs.generation}", (text_x, y), size=14, color=(200, 200, 100))
        y += 20
        
        # Culture badge
        culture_color = {
            "ember":   (200, 80, 40),
            "crystal": (140, 200, 255),
            "moss":    (80, 180, 80),
            "coastal": (80, 140, 180),
            "void":    (100, 40, 140),
            "mixed":   (140, 140, 140)
        }.get(rs.genome.cultural_base.value, (140, 140, 140))
        render_badge(surface, rs.genome.cultural_base.value.upper(), (text_x, y), culture_color)
        
        # Team badge
        team_label = rs.team.value.upper()
        team_color = (80, 80, 80)
        if rs.locked:
            team_label = "ON MISSION"
            team_color = (200, 140, 0)
        elif rs.team == TeamRole.DUNGEON:
            team_color = (180, 60, 60)
        render_badge(surface, team_label, (text_x + 75, y), team_color)
        y += 24
        
        # Trait badges (using get_dominant_trait logic)
        from src.shared.ui.profile_card import get_dominant_trait
        trait = get_dominant_trait(rs.genome)
        trait_color = (120, 100, 180)
        render_badge(surface, trait, (text_x, y), trait_color)
        
        if not rs.can_breed:
            render_badge(surface, "YOUNG", (text_x + 80, y), (200, 140, 60))
        y += 24
        
        # DNA line (visual representation of genome)
        dna_parts = [
            rs.genome.shape[0].upper(),
            rs.genome.size[0].upper(),
            rs.genome.pattern[0].upper(),
            rs.genome.accessory[0].upper() if rs.genome.accessory != "none" else "N"
        ]
        dna_text = "-".join(dna_parts) + f"-{rs.generation:02d}"
        render_text(surface, f"DNA: {dna_text}", (text_x, y), size=12, color=(100, 100, 120))

        # 3. Stats Sub-panel Content
        from src.shared.teams.stat_calculator import calculate_hp, calculate_attack, calculate_speed
        stats_x = self.stats_rect.x + 12
        stats_y = self.stats_rect.y + 12
        
        render_text(surface, "STATS", (stats_x, stats_y), size=12, color=self.spec.color_text_dim)
        stats_y += 20
        
        bar_w = self.stats_rect.width - 24
        bar_h = 10
        
        # Stat Bars
        stats = [
            ("HP", calculate_hp(rs.genome, rs.level), 100, (100, 200, 100)),
            ("ATK", calculate_attack(rs.genome, rs.level), 50, (200, 100, 100)),
            ("SPD", calculate_speed(rs.genome, rs.level), 50, (100, 100, 200)),
        ]
        
        for label, val, max_val, color in stats:
            render_text(surface, label, (stats_x, stats_y), size=14)
            render_text(surface, str(int(val)), (stats_x + bar_w - 30, stats_y), size=14, bold=True)
            stats_y += 18
            
            # Draw bar
            pygame.draw.rect(surface, (40, 40, 50), (stats_x, stats_y, bar_w, bar_h), border_radius=2)
            fill_w = int(bar_w * min(1.0, val / max_val))
            pygame.draw.rect(surface, color, (stats_x, stats_y, fill_w, bar_h), border_radius=2)
            stats_y += 22

        # 4. Actions Sub-panel Content (Buttons rendered by base system or manually)
        for btn in [self.dungeon_btn, self.racing_btn, self.remove_btn, self.mission_btn]:
            if btn.visible:
                btn.render(surface)

    def _render_team_status_bar(self, surface: pygame.Surface):
        dungeon_team = self.roster.get_dungeon_team()
        racing_team = self.roster.get_racing_team()
        
        # Respect modernized HubLayout bar rect
        bar_rect = self.bar_rect
        pygame.draw.rect(surface, (20, 20, 30), bar_rect)
        pygame.draw.rect(surface, (50, 50, 70), bar_rect, width=1)
        
        # Calculate positions
        center_x = bar_rect.centerx
        text_y = bar_rect.y + 12
        
        # Left side: Dungeon Team
        if not dungeon_team.members:
            dungeon_text = "⚔ DUNGEON: Empty"
            dungeon_color = self.spec.color_text_dim
        else:
            names = ", ".join(s.name for s in dungeon_team.members)
            dungeon_text = f"⚔ DUNGEON: {names} [{len(dungeon_team.members)}/4]"
            dungeon_color = self.spec.color_success if not any(s.locked for s in dungeon_team.members) else self.spec.color_warning
        
        render_text(surface, dungeon_text, (16, text_y), size=16, color=dungeon_color)
        
        # Center divider
        render_text(surface, "│", (center_x - 10, text_y), size=16, color=(100, 100, 120))
        
        # Right side: Racing Team
        racing_x = center_x + 10
        if not racing_team.members:
            racing_text = "RACING: Empty"
            racing_color = self.spec.color_text_dim
        else:
            racer = racing_team.members[0]
            racing_text = f"◎ RACING: {racer.name} [1/1]"
            racing_color = self.spec.color_success if not racer.locked else self.spec.color_warning
        
        # Calculate text width to ensure it fits
        render_text(surface, racing_text, (racing_x, text_y), size=16, color=racing_color)
        
        # Store click areas for interaction
        self.dungeon_status_area = pygame.Rect(16, bar_rect.y, center_x - 26, bar_rect.height)
        self.racing_status_area = pygame.Rect(center_x + 10, bar_rect.y, bar_rect.right - center_x - 26, bar_rect.height)

    def _show_banner(self, msg: str, color: Tuple[int, int, int]):
        self._banner_msg = msg
        self._banner_color = color
        self._banner_timer = 3.0

    def _render_banner(self, surface: pygame.Surface):
        if self._banner_timer <= 0:
            return
            
        alpha = int(min(1.0, self._banner_timer) * 255)
        banner_h = 40
        banner_rect = pygame.Rect(self.garden_rect.x, self.garden_rect.y, self.garden_rect.width, banner_h)
        
        # BG
        s = pygame.Surface((banner_rect.width, banner_rect.height), pygame.SRCALPHA)
        s.fill((*self.spec.color_surface, alpha // 2))
        surface.blit(s, banner_rect.topleft)
        
        # Text
        from src.shared.ui.profile_card import render_text
        render_text(surface, self._banner_msg, (banner_rect.centerx, banner_rect.centery), 
                    size=20, color=(*self._banner_color, alpha), center=True)

    def on_exit(self):
        """Cleanup logic."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        # First, check specialized team buttons
        for btn in [self.dungeon_btn, self.racing_btn, self.remove_btn, self.mission_btn]:
            if btn.visible and hasattr(btn, "handle_event") and btn.handle_event(event):
                return

        # Then, let the base class handle other UI components
        for comp in reversed(self.ui_components):
            if hasattr(comp, 'handle_event') and comp.handle_event(event):
                return
        
        # Handle status bar clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if clicking on dungeon status area
            if hasattr(self, 'dungeon_status_area') and self.dungeon_status_area.collidepoint(mouse_pos):
                self.request_scene("team")
                return
            
            # Check if clicking on racing status area  
            if hasattr(self, 'racing_status_area') and self.racing_status_area.collidepoint(mouse_pos):
                self.request_scene("team")
                return
            
            # Handle slime selection
            clicked_slime = self.pick_entity(mouse_pos)
            if clicked_slime:
                # Toggle selection
                if clicked_slime in self.selected_entities:
                    self.selected_entities.remove(clicked_slime)
                else:
                    self.selected_entities = [clicked_slime]
                self.on_selection_changed()
                return
