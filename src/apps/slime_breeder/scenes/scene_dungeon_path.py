import pygame
import random
import math
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
from src.shared.rendering.slime_renderer import SlimeRenderer

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
        self.depth = kwargs.get('depth', 1)
        self.track = generate_dungeon_track(self.depth)
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
        
        # Genetic Enemy Management
        self.zone_enemies = {}
        
        class MockEnemy:
            def __init__(self, data):
                self.genome = data['genome']
                self.level = 1
                class Kinematics:
                    def __init__(self): self.position = pygame.Vector2(0,0)
                self.kinematics = Kinematics()
        self.MockEnemy = MockEnemy

        self._generate_zone_visuals()

    def _generate_zone_visuals(self):
        depth = self.depth
        from src.shared.genetics import generate_random
        
        for zone in self.track.zones:
            if zone.zone_type in [DungeonZoneType.COMBAT, DungeonZoneType.BOSS]:
                # Dynamic squad size: 1-4 for combat, 1 for boss
                count = 1 if zone.zone_type == DungeonZoneType.BOSS else random.randint(1, 4)
                enemies = []
                name_prefix = "Boss" if zone.zone_type == DungeonZoneType.BOSS else "Wild"
                
                for i in range(count):
                    hp = 15 + depth * 5
                    if zone.zone_type == DungeonZoneType.BOSS:
                        hp *= 3
                        
                    enemies.append({
                        "id": f"enemy_{id(zone)}_{i}",
                        "name": f"{name_prefix} Slime {i+1}" if count > 1 else f"{name_prefix} Slime",
                        "stats": {
                            "hp": hp,
                            "max_hp": hp,
                            "attack": 3 + depth,
                            "defense": 1 + depth // 2,
                            "speed": 4 + random.randint(0, 2),
                            "stance": "Aggressive"
                        },
                        "genome": generate_random(),
                        "offset_x": (i - (count-1)/2) * 35, # Centered squad
                        "offset_y": random.choice([-20, 0, 20]),
                        "size": 14 if zone.zone_type == DungeonZoneType.COMBAT else 30
                    })
                self.zone_enemies[id(zone)] = enemies

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

    def on_enter(self, **kwargs) -> None:
        self.camera.x = 0.0
        self.camera.zoom_x = 1.0

    def on_resume(self, **kwargs) -> None:
        """Called when returning from combat or other pushed scenes."""
        result = kwargs.get('combat_result')
        if not result and self.session:
            result = getattr(self.session, 'last_combat_result', None)
            
        if result == "victory" or result == "flee":
            self.engine.resume()
        elif result == "defeat":
            self._retreat()

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
        # Pull pre-generated enemies for this zone
        zone = self.engine.party.current_zone
        enemies = self.zone_enemies.get(id(zone), [])
        
        # Push to combat scene
        self.manager.push("dungeon_combat", 
                          session=self.session, 
                          party_slimes=self.team,
                          enemies=enemies)

    def _generate_enemy_group(self, zone, depth: int) -> List[dict]:
        """No longer used, replaced by pre-generation in _generate_zone_visuals."""
        return []

    def _on_encounter_resolved(self, result=None):
        # No longer used, handled by on_resume
        pass

    def _handle_rest(self):
        # Simple animation/delay and resume for now
        self.engine.resume()

    def _handle_treasure(self):
        # Resolve treasure and resume
        self.engine.resume()

    def _handle_boss(self):
        self._handle_combat() # Reuses combat for now

    def _on_complete(self):
        self.manager.switch_to("garden", run_result={"floors_cleared": getattr(self.track, 'depth', 1)})

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
            
        # Minimap (fixed logic)
        self._render_minimap(surface)

    def _render_minimap(self, surface):
        track_rect = self.track_rect
        minimap_width = 200
        minimap_height = 40
        padding = 10
        
        m_left = self.spec.screen_width - minimap_width - padding
        m_top = padding + 64 # below header
        
        # Minimap Background
        m_rect = pygame.Rect(m_left, m_top, minimap_width, minimap_height)
        pygame.draw.rect(surface, (10, 10, 15), m_rect, border_radius=4)
        pygame.draw.rect(surface, (60, 60, 80), m_rect, width=1, border_radius=4)
        
        # Zone colors on minimap background
        track_len = self.track.total_length
        m_inner_w = minimap_width - 16
        m_inner_x = m_left + 8
        
        for zone in self.track.zones:
            z_start = int(m_inner_x + (zone.start_dist / track_len) * m_inner_w)
            z_end = int(m_inner_x + (zone.end_dist / track_len) * m_inner_w)
            z_color = tuple(c // 2 for c in ZONE_COLORS[zone.zone_type])
            pygame.draw.rect(surface, z_color, (z_start, m_top + 2, max(1, z_end - z_start), minimap_height - 4))

        # Party position dot
        progress = min(1.0, self.engine.party.distance / track_len)
        dot_x = int(m_inner_x + progress * m_inner_w)
        dot_y = m_top + minimap_height // 2
        
        # Cluster of dots for party
        for i, slime in enumerate(self.team[:4]):
            offset = (i - 1.5) * 4
            color = slime.genome.base_color
            pygame.draw.circle(surface, color, (dot_x, dot_y + int(offset)), 3)
            pygame.draw.circle(surface, (255, 255, 255), (dot_x, dot_y + int(offset)), 3, width=1)

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
                
                # Previews and Markers
                if not zone.resolved:
                    zone_center_x = self.camera.to_screen_x((zone.start_dist + zone.end_dist) / 2, 0)
                    if zone.zone_type in [DungeonZoneType.COMBAT, DungeonZoneType.BOSS]:
                        # Genetic Enemy Rendering (Phase 7)
                        enemies = self.zone_enemies.get(id(zone), [])
                        for enemy_data in enemies:
                            ex = zone_center_x + enemy_data['offset_x']
                            ey = track_rect.centery + enemy_data['offset_y']
                            
                            # Render small genome-based slime using a proxy object
                            enemy_proxy = self.MockEnemy(enemy_data)
                            self.renderer.render_at(surface, enemy_proxy, int(ex), int(ey), radius=enemy_data['size'])
                            
                            # Add small red eyes for "aggression" indicator if needed, 
                            # but the genetics alone might be enough. 
                            # Let's add a subtle red shadow or glow if it fits.
                else:
                    # Checkmark for resolved
                    zone_center_x = self.camera.to_screen_x((zone.start_dist + zone.end_dist) / 2, 0)
                    render_text(surface, "✓", (int(zone_center_x), track_rect.centery), size=24, color=(100, 255, 100), center=True)

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
        
        # FIX 3: Vertical Squad Formation
        SLIME_SPACING = 38 # Increased from 28
        total_h = len(self.team[:5]) * SLIME_SPACING
        start_y = py - total_h // 2 + SLIME_SPACING // 2
        
        for i, slime in enumerate(self.team[:5]):
            sy = start_y + i * SLIME_SPACING
            # Use SlimeRenderer or similar for visuals
            from src.apps.slime_breeder.entities.slime import Slime
            dummy = Slime(slime.name, slime.genome, (px, sy))
            self.renderer.render(surface, dummy)

        # Pause Indicator
        if self.engine.party.paused:
            # Floating icon above party
            label = "!"
            color = (255, 200, 0)
            if self.engine.party.pause_reason == "rest":
                label = "RESTING..."
                color = (100, 200, 255)
                # Pulse effect
                size_mod = 1.0 + math.sin(pygame.time.get_ticks() * 0.01) * 0.1
                pygame.draw.circle(surface, color, (int(px), int(track_rect.top - 20)), int(15 * size_mod), width=2)
            
            pygame.draw.circle(surface, color, (int(px), int(track_rect.top - 20)), 10)
            render_text(surface, label, (int(px), int(track_rect.top - 20)), size=18, color=(0,0,0), center=True, bold=True)
            
            if self.engine.party.pause_reason == "rest":
                # Floating HP text
                if pygame.time.get_ticks() % 500 < 50:
                    render_text(surface, "HP +1", (int(px) + random.randint(-20, 20), int(track_rect.top - 40)), size=14, color=(100, 255, 100), center=True)

        # 3. Party Cards (Bottom)
        self._render_party_cards(surface)

    def _render_party_cards(self, surface):
        track_rect = self.track_rect
        bar_y = track_rect.bottom + 20
        card_h = self.layout.team_bar.height - 10
        card_w = (self.spec.screen_width - 50) // 4
        
        for i, slime in enumerate(self.team[:4]):
            card_x = 10 + i * (card_w + 10)
            card_rect = pygame.Rect(card_x, bar_y, card_w, card_h)
            
            # Background
            pygame.draw.rect(surface, (35, 30, 45), card_rect, border_radius=6)
            pygame.draw.rect(surface, (70, 60, 90), card_rect, width=1, border_radius=6)
            
            # Portrait
            self.renderer.render_at(surface, slime, card_x + 25, bar_y + card_h // 2, radius=18)
            
            # Name & LV
            render_text(surface, slime.name, (card_x + 55, bar_y + 10), size=14, bold=True, color=(255,255,255))
            render_text(surface, f"Lv.{slime.level}", (card_x + 55, bar_y + 26), size=12, color=(180, 180, 200))
            
            # HP Bar
            hp_pct = max(0.0, min(1.0, slime.current_hp / slime.max_hp))
            bar_rect = pygame.Rect(card_x + 55, bar_y + 44, card_w - 65, 8)
            pygame.draw.rect(surface, (20, 15, 25), bar_rect, border_radius=4)
            if hp_pct > 0:
                hp_color = (100, 255, 100) if hp_pct > 0.5 else (255, 200, 0) if hp_pct > 0.2 else (255, 50, 50)
                pygame.draw.rect(surface, hp_color, (bar_rect.x, bar_rect.y, int(bar_rect.width * hp_pct), bar_rect.height), border_radius=4)

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
