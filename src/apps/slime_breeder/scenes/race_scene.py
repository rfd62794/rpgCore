import pygame
import random
import math
from typing import List, Optional, Tuple

from src.shared.engine.scene_manager import Scene
from src.shared.ui import Panel, Button, Label
from src.shared.teams.roster import Roster, RosterSlime, TeamRole
from src.shared.racing.race_engine import RaceEngine
from src.shared.racing.race_track import generate_track, SEGMENT_LENGTH
from src.apps.slime_breeder.ui.slime_renderer import SlimeRenderer
from src.shared.genetics.inheritance import generate_random

class RaceScene(Scene):
    def __init__(self, manager, **kwargs):
        super().__init__(manager, **kwargs)
        self.roster = kwargs.get("roster")
        if not self.roster:
            from src.shared.teams.roster_save import load_roster
            self.roster = load_roster()
            
        self.engine: Optional[RaceEngine] = None
        self.track = generate_track(1500)
        self.renderer = SlimeRenderer()
        
        # UI Setup
        self.ui_components = []
        self.setup_ui()
        
        self.start_countdown = 3.0
        self.camera_x = 0.0

    def setup_ui(self):
        self.ui_components.clear()
        self.exit_btn = Button(pygame.Rect(20, 20, 100, 40), "GARDEN", color=(100, 60, 60))
        self.ui_components.append(self.exit_btn)
        
    def on_enter(self, **kwargs):
        # Prepare participants
        team = self.roster.teams[TeamRole.RACING].members
        if not team:
            # Fallback for demo: pick first alive slime
            p = next((s for s in self.roster.slimes if s.alive), None)
            participants = [p] if p else []
        else:
            participants = [team[0]]
            
        # Add 3 AI competitors
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

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.exit_btn.rect.collidepoint(event.pos):
                    self.manager.switch_to("garden")

    def update(self, dt_ms: int):
        dt = dt_ms / 1000.0
        
        if self.start_countdown > 0:
            self.start_countdown -= dt
            return
            
        if self.engine and not self.engine.is_finished():
            self.engine.tick(dt)
            
            # Follow players (average distance or leading player)
            leading_dist = max(p.distance for p in self.engine.participants)
            target_cam = leading_dist - 200
            self.camera_x += (target_cam - self.camera_x) * 0.1

    def render(self, surface: pygame.Surface):
        surface.fill((40, 50, 60))
        
        # Render Track (Horizontal scrolling)
        self._render_track(surface)
        
        # Render Participants
        if self.engine:
            for i, p in enumerate(self.engine.participants):
                lane_y = 150 + (i * 120)
                # Map distance to screen
                screen_x = p.distance - self.camera_x
                
                # Draw lane line
                pygame.draw.line(surface, (80, 90, 100), (0, lane_y + 40), (800, lane_y + 40), 1)
                
                # Draw Slime using existing renderer
                # We need a temporary Slime object for the renderer
                # In a real app we'd refactor the renderer to accept genome/pos directly
                from src.apps.slime_breeder.entities.slime import Slime
                dummy_slime = Slime(p.slime.name, p.slime.genome, (screen_x, lane_y))
                self.renderer.render(surface, dummy_slime)
                
                # Rank tag if finished
                if p.finished:
                    txt = f"Rank {p.rank}"
                    Label(txt, (int(screen_x), lane_y - 40), size=18, color=(255, 255, 0)).render(surface)

        # UI
        for comp in self.ui_components:
            comp.render(surface)
            
        # Countdown Overlay
        if self.start_countdown > 0:
            msg = str(int(self.start_countdown) + 1)
            Label(msg, (400, 300), size=120, color=(255, 255, 255)).render(surface)

    def _render_track(self, surface: pygame.Surface):
        # Draw terrain segments based on camera
        visible_start = int(self.camera_x / SEGMENT_LENGTH)
        visible_end = visible_start + (800 // SEGMENT_LENGTH) + 2
        
        for i in range(visible_start, visible_end):
            if i >= len(self.track): break
            terrain = self.track[i]
            rect = pygame.Rect(i * SEGMENT_LENGTH - self.camera_x, 100, SEGMENT_LENGTH, 500)
            
            color = (80, 150, 80) # grass
            if terrain == "water": color = (80, 80, 200)
            elif terrain == "rock": color = (100, 100, 100)
            
            pygame.draw.rect(surface, color, rect)
            
        # Finish line
        finish_x = 1500 - self.camera_x
        if 0 <= finish_x <= 800:
            pygame.draw.line(surface, (255, 255, 255), (finish_x, 100), (finish_x, 600), 5)

    def on_exit(self):
        """Cleanup logic."""
        pass
