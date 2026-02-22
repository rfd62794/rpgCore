"""
Asteroids HUD Rendering using Shared UI Components
"""
import pygame
from src.shared.entities.game_state import GameSession
from src.shared.ui import Panel, Label

class HUD:
    """Renders game status using shared UI system"""
    
    def __init__(self):
        # Small panel in top-left
        self.panel = Panel(
            rect=pygame.Rect(0, 0, 60, 52),
            bg_color=(0, 0, 0, 100),  # Transparent black
            border_color=(0, 255, 0),
            border_width=1,
            border_radius=0
        )
        
        # Labels for stats
        self.score_label = Label(pygame.Rect(4, 4, 52, 12), text="SCORE: 0", font_size=16, color=(0, 255, 0))
        self.lives_label = Label(pygame.Rect(4, 16, 52, 12), text="LIVES: 0", font_size=16, color=(0, 255, 0))
        self.wave_label = Label(pygame.Rect(4, 28, 52, 12), text="WAVE: 0", font_size=16, color=(0, 255, 0))
        self.rocks_label = Label(pygame.Rect(4, 40, 52, 12), text="ROCKS: 0", font_size=16, color=(0, 255, 0))
        
        self.panel.add_child(self.score_label)
        self.panel.add_child(self.lives_label)
        self.panel.add_child(self.wave_label)
        self.panel.add_child(self.rocks_label)
            
    def render(self, surface: pygame.Surface, session: GameSession, asteroid_count: int):
        """Update and draw HUD to surface"""
        self.score_label.set_text(f"SCORE: {session.score}")
        self.lives_label.set_text(f"LIVES: {session.lives}")
        self.wave_label.set_text(f"WAVE: {session.wave}")
        self.rocks_label.set_text(f"ROCKS: {asteroid_count}")
        
        self.panel.render(surface)
