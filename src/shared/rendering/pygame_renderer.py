"""
PyGame Renderer - Concrete implementation of RenderAdapter using PyGame.
Entity-based rendering pattern.
"""

from typing import Any, List, Dict
from math import cos, sin
import os

from .render_adapter import RenderAdapter

class PyGameRenderer(RenderAdapter):
    def __init__(self, width: int = 800, height: int = 600, title: str = "rpgCore Engine"):
        self.width = width
        self.height = height
        self.title = title
        self.screen = None
        
        # Avoid showing window during headless tests
        if os.environ.get("PYTEST_CURRENT_TEST"):
            os.environ["SDL_VIDEODRIVER"] = "dummy"

    def initialize(self) -> bool:
        import pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        return True

    def shutdown(self) -> None:
        import pygame
        pygame.quit()

    def clear(self, color: Any) -> None:
        if self.screen:
            self.screen.fill(color)

    def present(self) -> None:
        import pygame
        if self.screen:
            pygame.display.flip()

    def render_entities(self, entities: List[Dict[str, Any]]) -> None:
        """
        Renders a list of entities to the surface.
        Entities are expected to be dicts with 'x', 'y', 'type', 'color', 'radius', 'heading'.
        """
        import pygame
        if not self.screen:
            return

        for entity in entities:
            if not entity.get("active", True):
                continue
            
            e_type = entity.get("type", "unknown")
            x = entity.get("x", 0)
            y = entity.get("y", 0)
            radius = entity.get("radius", 10)
            color = entity.get("color", (255, 255, 255))
            heading = entity.get("heading", 0.0)

            if e_type == "circle":
                pygame.draw.circle(self.screen, color, (int(x), int(y)), int(radius))
            elif e_type == "triangle":
                x1 = x + cos(heading) * radius * 1.5
                y1 = y + sin(heading) * radius * 1.5
                x2 = x + cos(heading + 2.5) * radius
                y2 = y + sin(heading + 2.5) * radius
                x3 = x + cos(heading - 2.5) * radius
                y3 = y + sin(heading - 2.5) * radius
                points = [(x1, y1), (x2, y2), (x3, y3)]
                pygame.draw.polygon(self.screen, color, points, 1)
            else:
                # Default draw a simple rect if unknown
                rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
                pygame.draw.rect(self.screen, color, rect, 1)
