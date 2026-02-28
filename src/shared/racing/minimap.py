"""Race minimap component for showing racer positions."""

import pygame
from typing import List
from src.shared.ui.spec import UISpec

class RaceMinimap:
    WIDTH = 200
    HEIGHT = 48
    PADDING = 8
    
    def __init__(self, spec: UISpec):
        self.spec = spec
        
    def render(self, surface, racers, track_length, camera_x):
        """Render the minimap in the top-right corner."""
        # Position: top-right of arena, below header
        x = self.spec.screen_width - self.WIDTH - self.PADDING
        y = self.PADDING + 48  # below header bar
        
        # Background
        minimap_rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(surface, (20, 20, 30), minimap_rect, border_radius=4)
        pygame.draw.rect(surface, (80, 80, 100), minimap_rect, width=1, border_radius=4)
        
        # Track line
        track_y = y + self.HEIGHT // 2
        pygame.draw.line(surface, (80, 80, 80), (x + 8, track_y), (x + self.WIDTH - 8, track_y), 2)
        
        # Finish line marker
        finish_x = x + self.WIDTH - 12
        pygame.draw.line(surface, (255, 255, 255), (finish_x, y + 8), (finish_x, y + self.HEIGHT - 8), 2)
        
        # Racer dots
        for racer in racers:
            progress = racer.distance / track_length
            dot_x = int(x + 8 + progress * (self.WIDTH - 16))
            dot_y = track_y
            
            # Get cultural color for racer
            cultural_color = self._get_cultural_color(racer.slime.genome.cultural_base.value)
            pygame.draw.circle(surface, cultural_color, (dot_x, dot_y), 4)
            
            # Rank number above dot
            self._render_text(surface, str(racer.rank), (dot_x, dot_y - 10), size="sm", centered=True)
        
        # Camera position indicator
        cam_progress = camera_x / track_length  
        cam_x = int(x + 8 + cam_progress * (self.WIDTH - 16))
        pygame.draw.rect(surface, (255, 255, 255, 60), pygame.Rect(cam_x - 15, y + 2, 30, self.HEIGHT - 4))
    
    def _get_cultural_color(self, cultural_base: str) -> tuple:
        """Get color for cultural base."""
        colors = {
            "ember": (200, 80, 40),
            "crystal": (140, 200, 255), 
            "moss": (80, 180, 80),
            "coastal": (80, 140, 180),
            "void": (100, 40, 140),
            "mixed": (140, 140, 140)
        }
        return colors.get(cultural_base, (140, 140, 140))
    
    def _render_text(self, surface, text, pos, size="md", centered=False, color=(255, 255, 255)):
        """Simple text rendering helper."""
        try:
            font_sizes = {"xs": 10, "sm": 12, "md": 14, "lg": 16, "xl": 18, "hd": 24}
            font = pygame.font.Font(None, font_sizes.get(size, 14))
            if centered:
                text_surface = font.render(text, True, color)
                rect = text_surface.get_rect(center=pos)
                surface.blit(text_surface, rect)
            else:
                surface.blit(font.render(text, True, color), pos)
        except:
            pass
