import pygame
import random
from typing import List, Optional

from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.button import Button
from src.shared.ui.label import Label
from src.shared.ui.spec import UISpec
from src.shared.ui.layouts import ArenaLayout
from src.shared.ui.profile_card import render_text
from src.shared.teams.roster import Roster, RosterSlime, TeamRole
from src.shared.dungeon.dungeon_track import DungeonTrack, DungeonZoneType, generate_dungeon_track, ZONE_COLORS, ZONE_LABELS
from src.shared.dungeon.dungeon_engine import DungeonEngine
from src.shared.racing.race_camera import RaceCamera
from src.shared.racing.minimap import RaceMinimap
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer

class DungeonPathScene(Scene):
    """
    Dungeon traversal scene based on a linear path simulation.
    Reuses racing engine patterns for autonomous party movement.
    """
    def __init__(self, manager, spec: UISpec, **kwargs):
        super().__init__(manager, spec, **kwargs)
        self.layout = ArenaLayout(spec)
        self.session = kwargs.get('session')
        self.team = kwargs.get('team', [])
        
        # Load team if not provided
        if not self.team:
            from src.shared.teams.roster_save import load_roster
            self.roster = load_roster()
            d_team = self.roster.teams.get(TeamRole.DUNGEON)
            self.team = d_team.members if d_team else []

        # Core Simulation Components
        depth = kwargs.get('depth', 1)
        self.track = generate_dungeon_track(depth)
        self.engine = DungeonEngine(self.track, self.team)
        self.camera = RaceCamera()
        
        # UI & Rendering
        self.renderer = SlimeRenderer()
        self.minimap = RaceMinimap(spec)
        self.ui_components = []
        self._setup_ui()
        
        # Visual Constants
        self.track_height_ratio = 0.4
        self.track_rect = self._get_track_rect()

    def _setup_ui(self):
        self.ui_components = []
        # Header bar
        header = Panel(self.layout.header, self.spec, variant="surface")
        header.add_to(self.ui_components)
        
        Label("DUNGEON DEPTHS", (self.layout.header.centerx, self.layout.header.centery), 
              self.spec, size="lg", bold=True, centered=True).add_to(self.ui_components)
        
        # FLEE / EXIT Button
        Button("FLEE", pygame.Rect(self.layout.header.x + 10, self.layout.header.y + 5, 80, self.layout.header.height - 10),
               self._retreat, self.spec, variant="secondary").add_to(self.ui_components)

        # Team Status Bar (Bottom)
        Panel(self.layout.team_bar, self.spec, variant="surface").add_to(self.ui_components)

    def on_enter(self) -> None:
        self.camera.x = 0.0
        self.camera.zoom_x = 1.0

    def handle_event(self, event: pygame.event.Event) -> None:
        for comp in reversed(self.ui_components):
            if hasattr(comp, 'handle_event') and comp.handle_event(event):
                return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._retreat()

    def update(self, dt: float) -> None:
        dt_ms = int(dt * 1000)
        for comp in self.ui_components:
            comp.update(dt_ms)
            
        events = self.engine.tick(dt)
        for event in events:
            self._handle_event(event)
            
        # Update camera to follow party
        target_x = self.engine.party.distance
        self.camera.x += (target_x - self.camera.x - self.spec.screen_width * 0.3) * 0.06

    def _handle_event(self, event_type: str):
        if event_type == "combat_encounter":
            self._handle_combat()
        elif event_type == "rest_encountered":
            self._handle_rest()
        elif event_type == "treasure_found":
            self._handle_treasure()
        elif event_type == "boss_encountered":
            self._handle_boss()
        elif event_type == "path_complete":
            self._on_complete()

    def _handle_combat(self):
        # Pause logic is handled by engine. Tick returns event once.
        # Switch to combat scene
        from src.apps.dungeon_crawler.ui.scene_dungeon_combat import DungeonCombatScene
        self.manager.switch_to("dungeon_combat", 
                               session=self.session, 
                               party_slimes=self.team,
                               on_complete=self._on_encounter_resolved)

    def _on_encounter_resolved(self, result=None):
        self.engine.resume()

    def _handle_rest(self):
        # Simple animation/delay and resume for now
        self.engine.resume()

    def _handle_treasure(self):
        # Resolve treasure and resume
        self.engine.resume()

    def _handle_boss(self):
        self._handle_combat() # Reuses combat for now

    def _on_complete(self):
        self.manager.switch_to("garden", run_result="Success")

    def _retreat(self):
        self.manager.switch_to("garden", message="Team retreated from the dungeon")

    def render(self, surface: pygame.Surface):
        surface.fill((20, 15, 25)) # Background: Dark Abyss
        
        # 1. Render Path
        self._render_track(surface)
        
        # 2. Render Party Marker
        self._render_party(surface)
        
        # 3. UI Layer
        for comp in self.ui_components:
            comp.render(surface)
            
        # 4. Minimap & HUD
        self._render_hud(surface)
        
        # Minimap (reused logic)
        # Wrapping party for RaceMinimap compatibility
        class MockParticipant:
            def __init__(self, p, slime):
                self.distance = p.distance
                self.slime = slime
                self.rank = 1
        
        self.minimap.render(surface, [MockParticipant(self.engine.party, self.team[0])], 
                             self.track.total_length, self.camera.x)

    def _render_track(self, surface):
        track_rect = self.track_rect
        
        # Path Floor
        pygame.draw.rect(surface, (45, 40, 55), track_rect)
        
        # Zones
        for zone in self.track.zones:
            sx = self.camera.to_screen_x(zone.start_dist, 0)
            ex = self.camera.to_screen_x(zone.end_dist, 0)
            
            visible_s = max(sx, 0)
            visible_e = min(ex, self.spec.screen_width)
            
            if visible_e > visible_s:
                color = ZONE_COLORS[zone.zone_type]
                if zone.resolved:
                    color = tuple(max(0, c - 40) for c in color) # Darken resolved
                
                pygame.draw.rect(surface, color, (visible_s, track_rect.top, visible_e - visible_s, track_rect.height))
                
                # Label
                if sx > -100 and sx < self.spec.screen_width:
                    label = ZONE_LABELS[zone.zone_type]
                    render_text(surface, label, (int(sx) + 10, track_rect.top + 10), size=16, color=(255, 255, 255))

        # Borders (Stone ridges)
        pygame.draw.line(surface, (120, 110, 130), track_rect.topleft, track_rect.topright, 4)
        pygame.draw.line(surface, (120, 110, 130), track_rect.bottomleft, track_rect.bottomright, 4)

    def _render_party(self, surface):
        track_rect = self.track_rect
        px = self.camera.to_screen_x(self.engine.party.distance, 0)
        py = track_rect.centery
        
        # Cluster of slime portraits for party
        for i, slime in enumerate(self.team[:4]):
            ox = (i % 2) * 24 - 12
            oy = (i // 2) * 24 - 12
            
            # Use SlimeRenderer or similar for visuals
            # For path, we just draw small slimes
            from src.apps.slime_breeder.entities.slime import Slime
            dummy = Slime(slime.name, slime.genome, (px + ox, py + oy))
            self.renderer.render(surface, dummy)

        # Pause Indicator
        if self.engine.party.paused:
            # Floating icon above party
            pygame.draw.circle(surface, (255, 200, 0), (int(px), int(track_rect.top - 20)), 10)
            render_text(surface, "!", (int(px), int(track_rect.top - 20)), size=18, color=(0,0,0), center=True, bold=True)

    def _render_hud(self, surface):
        # HUD Information in team_bar
        bar = self.layout.team_bar
        dist_text = f"DEPTH: {int(self.engine.party.distance)}m / {int(self.track.total_length)}m"
        render_text(surface, dist_text, (bar.centerx, bar.y + 15), size=18, bold=True, center=True)

    def _get_track_rect(self):
        h = int(self.spec.screen_height * self.track_height_ratio)
        y = (self.spec.screen_height - h) // 2
        return pygame.Rect(0, y, self.spec.screen_width, h)

    def on_exit(self):
        pass
