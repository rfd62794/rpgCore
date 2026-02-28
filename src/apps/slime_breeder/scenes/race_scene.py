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
from src.shared.racing.race_track import generate_track, SEGMENT_LENGTH
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
        self.renderer = SlimeRenderer()
        
        self.ui_components = []
        self._setup_ui()
        
        # Camera & Animation State
        self.start_countdown = 3.0
        self.camera_x = 0.0
        self.camera_vel = 0.0
        self.camera_zoom = 1.0
        self.target_zoom = 1.0
        
        # Shake state
        self.shake_mag = 0.0
        self.shake_timer = 0.0
        
        # Motion Effects
        self.speed_lines = [] 
        
        # Track Layout Constants
        self.track_height_ratio = 0.6  # Road takes 60% of arena height
        self.track_border_width = 8
        self.lane_count = 4

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
        self.camera_x = 0.0
        self.camera_vel = 0.0
        self.camera_zoom = 1.0
        self.target_zoom = 1.0

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
            target_cam = leading_dist - (self.spec.screen_width * 0.3)
            
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
        dists = [p.distance for p in self.engine.participants]
        gap = max(dists) - min(dists)
        new_target = 1.0
        if gap > 400: new_target = 0.85
        if gap > 800: new_target = 0.75
        lead_p = max(self.engine.participants, key=lambda x: x.distance)
        dist_to_finish = 3000 - lead_p.distance
        if dist_to_finish < 600: new_target = 1.2 
        self.camera_zoom += (new_target - self.camera_zoom) * 0.05

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
        
        # Create Arena Scratch Surface for Zoom/Shake
        arena_surf = pygame.Surface((self.layout.arena.width, self.layout.arena.height))
        arena_surf.fill((30, 50, 30)) # Off-track dark green background
        
        self._render_arena_content(arena_surf)
        
        # Apply Zoom
        if abs(self.camera_zoom - 1.0) > 0.01:
            scaled_w = int(arena_surf.get_width() * self.camera_zoom)
            scaled_h = int(arena_surf.get_height() * self.camera_zoom)
            scaled_surf = pygame.transform.smoothscale(arena_surf, (scaled_w, scaled_h))
            ox = (arena_surf.get_width() - scaled_w) // 2
            oy = (arena_surf.get_height() - scaled_h) // 2
            surface.blit(scaled_surf, (self.layout.arena.x + ox, self.layout.arena.y + oy))
        else:
            surface.blit(arena_surf, self.layout.arena.topleft)

        # Shake
        if self.shake_mag > 0:
            sx = random.uniform(-self.shake_mag, self.shake_mag)
            sy = random.uniform(-self.shake_mag, self.shake_mag)
            temp = surface.copy()
            surface.fill((0,0,0))
            surface.blit(temp, (sx, sy))

        for comp in self.ui_components:
            comp.render(surface)
            
        if self.start_countdown > 0:
            msg = "READY" if self.start_countdown > 2 else "SET" if self.start_countdown > 1 else "GO!"
            Label(msg, (self.spec.screen_width // 2, self.spec.screen_height // 2), self.spec, size="hd", color=(255, 255, 255), centered=True).render(surface)

    def _render_arena_content(self, surface: pygame.Surface):
        arena_w = surface.get_width()
        arena_h = surface.get_height()
        
        # Path Dimensions
        track_h = int(arena_h * self.track_height_ratio)
        track_y = (arena_h - track_h) // 2
        
        # 1. Draw Road Base (Continuous band)
        road_rect = pygame.Rect(0, track_y, arena_w, track_h)
        pygame.draw.rect(surface, (40, 40, 40), road_rect) # Slate dark grey road
        
        # 2. Track Terrain Zones (Inside road)
        visible_start = int(self.camera_x / SEGMENT_LENGTH)
        visible_end = visible_start + (arena_w // SEGMENT_LENGTH) + 4
        for i in range(visible_start, visible_end):
            if i >= len(self.track): break
            terrain = self.track[i]
            if terrain == "grass": continue # Just use road base
            
            rect = pygame.Rect(i * SEGMENT_LENGTH - self.camera_x, track_y, SEGMENT_LENGTH, track_h)
            color = (30, 50, 80) if terrain == "water" else (60, 60, 60) # Rock is lighter grey
            pygame.draw.rect(surface, color, rect)
            
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

        # 4. Finish Line
        fx = 3000 - self.camera_x
        if -20 < fx < arena_w + 20:
            pygame.draw.line(surface, (255, 255, 255), (fx, track_y), (fx, track_y + track_h), 12)
            # Finish line pattern
            for fy in range(track_y, track_y + track_h, 20):
                color = (0,0,0) if (fy // 20) % 2 == 0 else (255, 255, 255)
                pygame.draw.rect(surface, color, (fx - 4, fy, 8, 20))

        # 5. Participants
        if self.engine:
            for i, p in enumerate(self.engine.participants):
                # Center in lane
                ly = track_y + (i * lane_h) + (lane_h // 2) - 20
                screen_x = p.distance - self.camera_x
                
                from src.apps.slime_breeder.entities.slime import Slime
                dummy_slime = Slime(p.slime.name, p.slime.genome, (screen_x, ly))
                self.renderer.render(surface, dummy_slime)
                
                if p.finished:
                    Label(f"FINISH #{p.rank}", (int(screen_x), ly - 20), self.spec, color=self.spec.color_accent, bold=True, centered=True).render(surface)

        # 6. Speed Lines
        for line in self.speed_lines:
            ly = line["y"] - self.layout.arena.y
            pygame.draw.line(surface, (240, 240, 255, 150), (line["x"], ly), (line["x"] + line["len"], ly), 2)

    def on_exit(self):
        pass
