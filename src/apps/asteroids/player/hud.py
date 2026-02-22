"""
Asteroids HUD Rendering
"""
import pygame
from src.shared.entities.game_state import GameSession

class HUD:
    """Renders game status to surface"""
    
    def __init__(self):
        try:
            self.font = pygame.font.Font(None, 16)
        except:
            self.font = pygame.font.SysFont('monospace', 12)
            
    def render(self, surface: pygame.Surface, session: GameSession, asteroid_count: int):
        """Draw HUD text to surface"""
        score_text = f"SCORE: {session.score}"
        lives_text = f"LIVES: {session.lives}"
        wave_text = f"WAVE: {session.wave}"
        count_text = f"ROCKS: {asteroid_count}"
        
        y = 4
        for text in [score_text, lives_text, wave_text, count_text]:
            s = self.font.render(text, True, (0, 255, 0))
            surface.blit(s, (4, y))
            y += 12
