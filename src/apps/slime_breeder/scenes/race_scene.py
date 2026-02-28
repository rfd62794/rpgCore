import pygame
import random
import math
from typing import List, Optional, Tuple

from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.button import Button
from src.shared.ui.label import Label
from src.shared.ui.spec import UISpec
from src.shared.ui.layouts import ArenaLayout
from src.shared.teams.roster import Roster, RosterSlime, TeamRole
from src.shared.racing.race_engine import RaceEngine
from src.shared.racing.race_track import generate_track, generate_zones, TerrainType, SEGMENT_LENGTH
from src.shared.racing.minimap import RaceMinimap
from src.shared.racing.race_hud import RaceHUD
from src.shared.racing.race_camera import RaceCamera
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.genetics.inheritance import generate_random

class RaceScene(Scene):
    """
    Focused racing screen using ArenaLayout.
    """
    def __init__(self, manager, spec: UISpec, **kwargs):
        super().__init__(manager, spec, **kwargs)
        self.layout = ArenaLayout(spec)
        self.roster = kwargs.get("roster")
        if not self.roster:
            from src.shared.teams.roster_save import load_roster
            self.roster = load_roster()
            
        self.engine: Optional[RaceEngine] = None
        self.track = generate_track(3000)
        self.terrain_zones = generate_zones(3000)
        self.renderer = SlimeRenderer()
        self.minimap = RaceMinimap(spec)
        self.hud = RaceHUD(spec, self.layout)
        self.camera = RaceCamera()
        
        self.ui_components = []
        self._setup_ui()
        
        # Camera & Animation State
        self.start_countdown = 3.0
        self.shake_mag = 0.0
        self.shake_timer = 0.0
        
        # Motion Effects
        self.speed_lines = [] 
        
        # Track Layout Constants
        self.track_height_ratio = 0.45  # Track takes 45% of arena height
        self.min_track_height = 240     # Minimum track height for comfortable lanes
        self.track_border_width = 8
        self.lane_count = 4
        
        # Race state
        self.current_lap = 1
        self.total_laps = 3
        self.terrain_ahead = None
    
    def world_to_screen_x(self, world_x: float) -> float:
        """Convert world X coordinate to screen X using camera."""
        return self.camera.to_screen_x(world_x, self.layout.arena.x)
    
    def world_to_screen_y(self, lane: int, track_top: int, track_height: int) -> int:
        """Convert lane to screen Y coordinate (never affected by zoom)."""
        return self.camera.to_screen_y(lane, track_top, track_height)

    def _setup_ui(self):
        self.ui_components = []
        Panel(self.layout.header, self.spec, variant="surface").add_to(self.ui_components)
        Panel(self.layout.team_bar, self.spec, variant="surface").add_to(self.ui_components)
        Label("SLIME DERBY", (self.layout.header.centerx, self.layout.header.centery), self.spec, size="lg", bold=True, centered=True).add_to(self.ui_components)
        Button("EXIT", pygame.Rect(self.layout.header.x + 10, self.layout.header.y + 5, 80, self.layout.header.height - 10),
               lambda: self.manager.switch_to("garden"), self.spec, variant="secondary").add_to(self.ui_components)

    def on_enter(self) -> None:
        team = self.roster.teams[TeamRole.RACING].members
        participants = [team[0]] if team else [next((s for s in self.roster.slimes if s.alive), None)]
        participants = [p for p in participants if p]
        
        for i in range(3):
            ai_slime = RosterSlime(slime_id=f"ai_{i}", name=f"Racer_{i+1}", genome=generate_random(), level=random.randint(1, 5))
            participants.append(ai_slime)
            
        self.engine = RaceEngine(participants, self.track, length=3000)
        self.start_countdown = 3.0
        self.camera.x = 0.0
        self.camera.zoom_x = 1.0

    def trigger_shake(self, magnitude: float, duration: float):
        self.shake_mag = magnitude
        self.shake_timer = duration

    def handle_event(self, event: pygame.event.Event) -> None:
        # Process UI components first
        for comp in reversed(self.ui_components):
            if hasattr(comp, 'handle_event') and comp.handle_event(event):
                return
        
        # Handle race-specific events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.request_scene("garden")
            elif event.key == pygame.K_SPACE and self.start_countdown <= 0:
                if self.engine and not self.engine.is_finished():
                    self.engine.tick(0.1)  # Fast forward slightly

    def update(self, dt: float) -> None:
        dt_ms = int(dt * 1000)
        for comp in self.ui_components:
            comp.update(dt_ms)
            
        if self.start_countdown > 0:
            self.start_countdown -= dt
            if 0 < self.start_countdown < 0.1: self.trigger_shake(5.0, 0.3)
            return
            
        if self.engine and not self.engine.is_finished():
            self.engine.tick(dt)
            
            # 1. Momentum Camera Follow
            leading_dist = max(p.distance for p in self.engine.participants)
            target_cam = leading_dist - (self.spec.screen_width * 0.35)  # Leader at 35% from left
            
            dist_diff = target_cam - self.camera_x
            accel = dist_diff * 5.0
            self.camera_vel += accel * dt
            self.camera_vel *= 0.9 
            self.camera_x += self.camera_vel * dt
            
            # 2. Dynamic Zoom Logic
            self._update_zoom()
            
            # 3. Speed Lines
            self._update_speed_lines(dt)
            
        if self.shake_timer > 0:
            self.shake_timer -= dt
        else:
            self.shake_mag = 0

    def _update_zoom(self):
        if not self.engine or not self.engine.participants:
            return
            
        dists = [p.distance for p in self.engine.participants]
        gap = max(dists) - min(dists)
        lead_p = max(self.engine.participants, key=lambda x: x.distance)
        dist_to_finish = 3000 - lead_p.distance
        
        # Determine target zoom based on race conditions
        new_target = self.ZOOM_NORMAL
        
        # Zoom out if pack is spread out
        if gap > 400: 
            new_target = self.ZOOM_OUT_MAX
        
        # Zoom in on final stretch
        if dist_to_finish < 600: 
            new_target = self.ZOOM_FINISH
        
        # Smooth zoom transition (lerp)
        zoom_speed = 0.03  # Slower = more cinematic
        self.camera_zoom += (new_target - self.camera_zoom) * zoom_speed

    def _update_speed_lines(self, dt: float):
        lead_p = max(self.engine.participants, key=lambda x: x.distance)
        if lead_p.velocity > 150:
            for _ in range(int(lead_p.velocity // 100)):
                self.speed_lines.append({
                    "x": self.spec.screen_width + random.randint(0, 100),
                    "y": random.randint(self.layout.arena.y, self.layout.arena.bottom),
                    "len": random.randint(40, 100),
                    "speed": lead_p.velocity * 1.5 + random.randint(0, 200)
                })
        for line in self.speed_lines[:]:
            line["x"] -= line["speed"] * dt
            if line["x"] < -200:
                self.speed_lines.remove(line)

    def render(self, surface: pygame.Surface):
        surface.fill(self.spec.color_bg)
        
        # Render arena content directly (no viewport scaling)
        self._render_arena_content(surface)
        
        # Shake
        if self.shake_mag > 0:
            sx = random.uniform(-self.shake_mag, self.shake_mag)
            sy = random.uniform(-self.shake_mag, self.shake_mag)
            temp = surface.copy()
            surface.fill((0,0,0))
            surface.blit(temp, (sx, sy))

        for comp in self.ui_components:
            comp.render(surface)
        
        # Render minimap
        if self.engine:
            # Update terrain ahead for player
            player = self.engine.participants[0]
            from src.shared.racing.race_track import get_terrain_at
            look_ahead_distance = player.distance + 200
            self.terrain_ahead = get_terrain_at(self.track, look_ahead_distance)
            
            # Update current lap from player
            self.current_lap = player.laps_complete + 1 if not player.finished else self.engine.total_laps
            
            self.minimap.render(surface, self.engine.participants, 3000, self.camera_x)
            self.hud.render(surface, self.engine.participants, self.current_lap, self.total_laps, self.terrain_ahead)
            
        if self.start_countdown > 0:
            msg = "READY" if self.start_countdown > 2 else "SET" if self.start_countdown > 1 else "GO!"
            Label(msg, (self.spec.screen_width // 2, self.spec.screen_height // 2), self.spec, size="hd", color=(255, 255, 255), centered=True).render(surface)

    def _render_arena_content(self, surface: pygame.Surface):
        # Render within arena bounds
        arena_rect = self.layout.arena
        arena_w = arena_rect.width
        arena_h = arena_rect.height
        
        # Create temporary surface for arena content
        arena_surf = pygame.Surface((arena_w, arena_h))
        arena_surf.fill((30, 50, 30)) # Off-track dark green background
        
        # Path Dimensions
        track_h = max(self.min_track_height, int(arena_h * self.track_height_ratio))
        track_y = (arena_h - track_h) // 2
        
        # Render all arena content to arena_surf
        self._render_track_content(arena_surf, arena_w, arena_h, track_y, track_h)
        
        # Blit arena surface to main surface
        surface.blit(arena_surf, arena_rect.topleft)
    
    def _render_track_content(self, surface, arena_w, arena_h, track_y, track_h):
        
        # 1. Draw Road Base (Continuous band)
        road_rect = pygame.Rect(0, track_y, arena_w, track_h)
        pygame.draw.rect(surface, (40, 40, 40), road_rect) # Slate dark grey road
        
        # 2. Track Terrain Zones (Wide blocks, not stripes)
        # Terrain colors
        terrain_colors = {
            TerrainType.GRASS: (55, 110, 55),   # base track color
            TerrainType.WATER: (40, 100, 180),  # blue, slightly lighter
            TerrainType.ROCK:  (100, 90, 80),   # grey-brown
            TerrainType.MUD:   (90, 70, 50),    # dark brown
        }
        
        # Render zones as wide blocks with horizontal-only zoom
        for zone in self.terrain_zones:
            screen_start = self.world_to_screen_x(zone.start_dist)
            screen_end   = self.world_to_screen_x(zone.end_dist)
            
            # Clip to screen
            visible_start = max(screen_start, 0)
            visible_end   = min(screen_end, arena_w)
            
            if visible_end <= visible_start:
                continue  # off screen
            
            width = visible_end - visible_start
            
            # Skip grass zones (use road base color)
            if zone.terrain_type != TerrainType.GRASS:
                terrain_color = terrain_colors.get(zone.terrain_type, (60, 60, 60))
                pygame.draw.rect(surface, terrain_color, (visible_start, track_y, width, track_h))
                
                # Zone label at entry point
                if screen_start > 0 and screen_start < arena_w:
                    label = zone.terrain_type.value.upper()
                    if zone.terrain_type == TerrainType.WATER: label = "~ POND"
                    elif zone.terrain_type == TerrainType.ROCK: label = "▲ ROCKS"
                    elif zone.terrain_type == TerrainType.MUD: label = "◼ MUD"
                    
                    # Simple text rendering for terrain label
                    font = pygame.font.Font(None, 14)
                    text_surface = font.render(label, True, (255, 255, 255, 180))
                    surface.blit(text_surface, (visible_start + 8, track_y + 8))
            
        # 3. Track Borders & Lanes
        # Top/Bottom borders
        pygame.draw.line(surface, (200, 200, 200), (0, track_y), (arena_w, track_y), 3)
        pygame.draw.line(surface, (200, 200, 200), (0, track_y + track_h), (arena_w, track_y + track_h), 3)
        
        # Lanes
        lane_h = track_h // self.lane_count
        for i in range(1, self.lane_count):
            ly = track_y + (i * lane_h)
            # Dashed lane markers
            for dx in range(0, arena_w, 40):
                pygame.draw.line(surface, (100, 100, 100), (dx, ly), (dx + 20, ly), 1)

        # 4. Finish Line (checkered pattern, not blocking)
        fx = self.world_to_screen_x(3000)
        if -20 < fx < arena_w + 20:
            # Checkered pattern — alternating black/white squares
            square_h = 16
            squares = track_h // square_h
            
            for i in range(squares):
                color = (255, 255, 255) if i % 2 == 0 else (0, 0, 0)
                pygame.draw.rect(surface, color, (fx - 3, track_y + i * square_h, 6, square_h))
            
            # No collision. No blocking. Visual only.

        # 5. Participants
        if self.engine:
            for i, p in enumerate(self.engine.participants):
                # Use world_to_screen coordinate conversion
                ly = self.world_to_screen_y(i, track_y, track_h)
                screen_x = self.world_to_screen_x(p.distance)
                
                # Render shadow when jumping
                if p.jump_height > 2:
                    shadow_alpha = int(120 * (1 - p.jump_height/20))
                    shadow_surface = pygame.Surface((24, 8), pygame.SRCALPHA)
                    pygame.draw.ellipse(shadow_surface, (0, 0, 0, shadow_alpha), pygame.Rect(0, 0, 24, 8))
                    surface.blit(shadow_surface, (screen_x - 12, ly - 4))
                
                # Create dummy slime with jump height offset
                from src.apps.slime_breeder.entities.slime import Slime
                jump_y = ly - int(p.jump_height)
                dummy_slime = Slime(p.slime.name, p.slime.genome, (screen_x, jump_y))
                
                # Override render size to be fixed regardless of zoom
                original_radius = getattr(self.renderer, 'render_radius', None)
                self.renderer.render_radius = self.SLIME_RENDER_RADIUS
                self.renderer.render(surface, dummy_slime)
                if original_radius is not None:
                    self.renderer.render_radius = original_radius
                
                if p.finished:
                    Label(f"FINISH #{p.rank}", (int(screen_x), ly - 30), self.spec, color=self.spec.color_accent, bold=True, centered=True).render(surface)

        # 6. Speed Lines
        for line in self.speed_lines:
            ly = line["y"] - self.layout.arena.y
            pygame.draw.line(surface, (240, 240, 255, 150), (line["x"], ly), (line["x"] + line["len"], ly), 2)

    def on_exit(self):
        pass
