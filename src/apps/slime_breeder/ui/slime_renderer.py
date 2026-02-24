import pygame
import math
import time
from typing import Tuple, List
from src.apps.slime_breeder.entities.slime import Slime

class SlimeRenderer:
    def __init__(self):
        self.size_map = {
            "tiny": 8,
            "small": 15,
            "medium": 24,
            "large": 38,
            "massive": 56
        }

    def render(self, surface: pygame.Surface, slime: Slime, selected: bool = False) -> None:
        pos = (int(slime.kinematics.position.x), int(slime.kinematics.position.y))
        base_radius = self.size_map.get(slime.genome.size, 24)
        
        # Breathing animation
        pulse = math.sin(time.time() * 3.0) * 0.05
        radius = int(base_radius * (1.0 + pulse))
        
        # Selection highlight
        if selected:
            pygame.draw.circle(surface, (255, 255, 255), pos, radius + 4, 2)

        color = slime.genome.base_color
        p_color = slime.genome.pattern_color
        shape = slime.genome.shape
        seed = sum(color) # Deterministic seed based on color
        
        # 1. Base Shape
        if shape == "round":
            pygame.draw.circle(surface, color, pos, radius)
        elif shape == "cubic":
            rect = pygame.Rect(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)
            pygame.draw.rect(surface, color, rect)
        elif shape == "elongated":
            # Ellipse (wider than tall)
            rect = pygame.Rect(pos[0] - int(radius * 1.5), pos[1] - radius, radius * 3, radius * 2)
            pygame.draw.ellipse(surface, color, rect)
        elif shape == "crystalline":
            # Hexagon
            points = []
            for i in range(6):
                angle = math.radians(i * 60)
                px = pos[0] + radius * math.cos(angle)
                py = pos[1] + radius * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
        elif shape == "amorphous":
            # Circle with 4-6 random wobble points
            points = []
            num_points = 12
            for i in range(num_points):
                angle = math.radians(i * (360 / num_points))
                wobble = math.sin(time.time() * 2.0 + i + seed) * (radius * 0.2)
                px = pos[0] + (radius + wobble) * math.cos(angle)
                py = pos[1] + (radius + wobble) * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)

        # 2. Pattern Overlay
        pattern = slime.genome.pattern
        if pattern == "spotted":
            # 3-5 small circles
            for i in range(4):
                off_x = math.sin(i * 1.5 + seed) * (radius * 0.4)
                off_y = math.cos(i * 1.5 + seed) * (radius * 0.4)
                pygame.draw.circle(surface, p_color, (int(pos[0] + off_x), int(pos[1] + off_y)), max(2, radius // 6))
        elif pattern == "striped":
            # 2-3 horizontal lines
            line_w = max(1, radius // 8)
            for y_off in [-radius // 3, 0, radius // 3]:
                lx = pos[0] - radius + 2
                rx = pos[0] + radius - 2
                if shape == "elongated":
                    lx -= radius // 2
                    rx += radius // 2
                pygame.draw.line(surface, p_color, (lx, pos[1] + y_off), (rx, pos[1] + y_off), line_w)
        elif pattern == "marbled":
            # Swirl suggestion using arc
            rect = pygame.Rect(pos[0] - radius//2, pos[1] - radius//2, radius, radius)
            pygame.draw.arc(surface, p_color, rect, 0, math.pi, 2)
        elif pattern == "iridescent":
            # Second circle slightly offset, low alpha
            iri_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(iri_surf, (*p_color, 80), (radius * 2, radius * 2), radius)
            surface.blit(iri_surf, (pos[0] - radius * 2 + 3, pos[1] - radius * 2 + 3))

        # 3. Accessory indicator
        acc = slime.genome.accessory
        if acc == "crown":
            # Small yellow points above head
            pts = [(pos[0]-10, pos[1]-radius), (pos[0]-5, pos[1]-radius-10), (pos[0], pos[1]-radius), (pos[0]+5, pos[1]-radius-10), (pos[0]+10, pos[1]-radius)]
            pygame.draw.lines(surface, (255, 215, 0), False, pts, 2)
        elif acc == "glow":
            # soft circle, low alpha, slightly larger than slime
            glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 200, 40), (radius * 2, radius * 2), radius + 10)
            surface.blit(glow_surf, (pos[0] - radius * 2, pos[1] - radius * 2))
        elif acc == "shell":
            # small brown semicircle on back
            rect = pygame.Rect(pos[0] - radius, pos[1] - radius, radius, radius)
            pygame.draw.arc(surface, (139, 69, 19), rect, 0, math.pi, 3)
        elif acc == "crystals":
            # 2-3 small diamond shapes
            for i in range(2):
                cx, cy = pos[0] + (i*15 - 7), pos[1] - radius - 5
                pygame.draw.polygon(surface, (100, 200, 255), [(cx, cy-5), (cx+5, cy), (cx, cy+5), (cx-5, cy)])
        elif acc == "scar":
            # single dark line across face
            pygame.draw.line(surface, (50, 0, 0), (pos[0]-radius//2, pos[1]), (pos[0]+radius//2, pos[1]+radius//2), 2)

        # 4. Simple eyes/face
        eye_color = (0, 0, 0)
        eye_off = radius // 3
        pygame.draw.circle(surface, eye_color, (pos[0] - eye_off, pos[1] - eye_off), max(1, radius // 10))
        pygame.draw.circle(surface, eye_color, (pos[0] + eye_off, pos[1] - eye_off), max(1, radius // 10))
