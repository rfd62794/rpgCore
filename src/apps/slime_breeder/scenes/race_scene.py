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
        self.track = generate_track(3000) # Longer track for 720p
        self.renderer = SlimeRenderer()
        
        # UI Setup
        self.ui_components = []
        self._setup_ui()
        
        self.start_countdown = 3.0
        self.camera_x = 0.0

    def _setup_ui(self):
        self.ui_components = []
        
        # Header & Team Bar Panels
        Panel(self.layout.header, self.spec, variant="surface").add_to(self.ui_components)
        Panel(self.layout.team_bar, self.spec, variant="surface").add_to(self.ui_components)
        
        # Header Info
        Label("SLIME DERBY", (self.layout.header.centerx, self.layout.header.centery), self.spec, size="lg", bold=True, centered=True).add_to(self.ui_components)
        
        Button("EXIT", pygame.Rect(self.layout.header.x + 10, self.layout.header.y + 5, 80, self.layout.header.height - 10),
               lambda: self.manager.switch_to("garden"), self.spec, variant="secondary").add_to(self.ui_components)

    def on_enter(self) -> None:
        # Prepare participants
        team = self.roster.teams[TeamRole.RACING].members
        if not team:
            p = next((s for s in self.roster.slimes if s.alive), None)
            participants = [p] if p else []
        else:
            participants = [team[0]]
            
        # Add AI competitors
        for i in range(3):
            ai_slime = RosterSlime(
                slime_id=f"ai_{i}",
                name=f"Racer_{i+1}",
                genome=generate_random(),
                level=random.randint(1, 5)
            )
            participants.append(ai_slime)
            
        self.engine = RaceEngine(participants, self.track)
        self.start_countdown = 3.0
        self.camera_x = 0.0

    def handle_event(self, event: pygame.event.Event):
        for comp in reversed(self.ui_components):
            if hasattr(comp, "handle_event") and comp.handle_event(event):
                return

    def update(self, dt: float) -> None:
        dt_ms = int(dt * 1000)
        for comp in self.ui_components:
            comp.update(dt_ms)
            
        if self.start_countdown > 0:
            self.start_countdown -= dt
            return
            
        if self.engine and not self.engine.is_finished():
            self.engine.tick(dt)
            
            # Follow players
            leading_dist = max(p.distance for p in self.engine.participants)
            target_cam = leading_dist - (self.spec.screen_width * 0.25)
            self.camera_x += (target_cam - self.camera_x) * 0.1

    def render(self, surface: pygame.Surface):
        surface.fill(self.spec.color_bg)
        
        # Render Arena/Track
        self._render_track(surface)
        
        if self.engine:
            for i, p in enumerate(self.engine.participants):
                lane_y = self.layout.arena.y + 60 + (i * (self.layout.arena.height // 5))
                screen_x = p.distance - self.camera_x
                
                # Lane separator
                pygame.draw.line(surface, self.spec.color_border, (0, lane_y + 40), (self.spec.screen_width, lane_y + 40), 1)
                
                # Participant
                from src.apps.slime_breeder.entities.slime import Slime
                dummy_slime = Slime(p.slime.name, p.slime.genome, (screen_x, lane_y))
                self.renderer.render(surface, dummy_slime)
                
                # Status tag
                if p.finished:
                    Label(f"RANK {p.rank}", (int(screen_x), lane_y - 20), self.spec, color=self.spec.color_accent, bold=True, centered=True).render(surface)

        # UI Overlay
        for comp in self.ui_components:
            comp.render(surface)
            
        # Countdown
        if self.start_countdown > 0:
            msg = str(int(self.start_countdown) + 1)
            Label(msg, (self.spec.screen_width // 2, self.spec.screen_height // 2), self.spec, size="hd", color=(255, 255, 255), centered=True).render(surface)

    def _render_track(self, surface: pygame.Surface):
        # Draw terrain
        sw = self.spec.screen_width
        visible_start = int(self.camera_x / SEGMENT_LENGTH)
        visible_end = visible_start + (sw // SEGMENT_LENGTH) + 2
        
        for i in range(visible_start, visible_end):
            if i >= len(self.track): break
            terrain = self.track[i]
            rect = pygame.Rect(i * SEGMENT_LENGTH - self.camera_x, self.layout.arena.y, SEGMENT_LENGTH, self.layout.arena.height)
            
            color = (60, 120, 60) # grass
            if terrain == "water": color = (40, 80, 160)
            elif terrain == "rock": color = (80, 80, 80)
            
            pygame.draw.rect(surface, color, rect)
            
        # Finish line
        finish_x = 3000 - self.camera_x
        if 0 <= finish_x <= sw:
            pygame.draw.line(surface, (255, 255, 255), (finish_x, self.layout.arena.y), (finish_x, self.layout.arena.bottom), 5)

    def on_exit(self):
        pass
