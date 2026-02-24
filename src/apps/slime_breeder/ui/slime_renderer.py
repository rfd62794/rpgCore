import pygame
import math
import time
from typing import Tuple
from src.apps.slime_breeder.entities.slime import Slime

class SlimeRenderer:
    def __init__(self):
        self.size_map = {
            "tiny": 12,
            "small": 18,
            "medium": 26,
            "large": 36,
            "massive": 48
        }

    def render(self, surface: pygame.Surface, slime: Slime, selected: bool = False) -> None:
        pos = (int(slime.kinematics.position.x), int(slime.kinematics.position.y))
        radius = self.size_map.get(slime.genome.size, 26)
        
        # Breathing animation
        pulse = math.sin(time.time() * 3.0) * 0.05
        current_radius = int(radius * (1.0 + pulse))
        
        # Selection highlight
        if selected:
            pygame.draw.circle(surface, (255, 255, 255), pos, current_radius + 4, 2)

        # 1. Base Shape
        color = slime.genome.base_color
        shape = slime.genome.shape
        
        if shape == "round":
            pygame.draw.circle(surface, color, pos, current_radius)
        elif shape == "cubic":
            rect = pygame.Rect(pos[0] - current_radius, pos[1] - current_radius, current_radius * 2, current_radius * 2)
            pygame.draw.rect(surface, color, rect)
        elif shape == "elongated":
            rect = pygame.Rect(pos[0] - current_radius, pos[1] - (current_radius // 2), current_radius * 2, current_radius)
            pygame.draw.ellipse(surface, color, rect)
        elif shape == "crystalline":
            # 6-sided polygon
            points = []
            for i in range(6):
                angle = math.radians(i * 60)
                px = pos[0] + current_radius * math.cos(angle)
                py = pos[1] + current_radius * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
        elif shape == "amorphous":
            # Circle with wobble
            points = []
            for i in range(12):
                angle = math.radians(i * 30)
                wobble = math.sin(time.time() * 2.0 + i) * 3
                px = pos[0] + (current_radius + wobble) * math.cos(angle)
                py = pos[1] + (current_radius + wobble) * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
        else:
            pygame.draw.circle(surface, color, pos, current_radius)

        # 2. Pattern Overlay (simplistic representative dots)
        p_color = slime.genome.pattern_color
        pattern = slime.genome.pattern
        if pattern == "spotted":
            for i in range(5):
                off_x = math.sin(i * 1.5) * (current_radius * 0.5)
                off_y = math.cos(i * 1.5) * (current_radius * 0.5)
                pygame.draw.circle(surface, p_color, (int(pos[0] + off_x), int(pos[1] + off_y)), 3)
        elif pattern == "striped":
            rect = pygame.Rect(pos[0] - current_radius, pos[1] - 2, current_radius * 2, 4)
            pygame.draw.rect(surface, p_color, rect)
        
        # 3. Accessory indicator
        acc = slime.genome.accessory
        if acc != "none":
            acc_pos = (pos[0], pos[1] - current_radius - 5)
            pygame.draw.circle(surface, (255, 215, 0), acc_pos, 4) # Gold dot for accessory

        # 4. Simple eyes/face
        eye_color = (0, 0, 0)
        eye_off = current_radius // 3
        pygame.draw.circle(surface, eye_color, (pos[0] - eye_off, pos[1] - eye_off), 2)
        pygame.draw.circle(surface, eye_color, (pos[0] + eye_off, pos[1] - eye_off), 2)
