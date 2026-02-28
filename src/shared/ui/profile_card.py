import pygame
import math
from dataclasses import dataclass
from typing import Tuple, Optional
from src.shared.ui.base import UIComponent
from src.shared.genetics.genome import SlimeGenome
from src.shared.teams.roster import RosterSlime, TeamRole
from src.shared.teams.stat_calculator import (
    calculate_hp, calculate_attack, calculate_speed
)

class ProfileCard(UIComponent):
    def __init__(self, slime: RosterSlime, position: Tuple[int, int]):
        # Card dimensions
        self.WIDTH = 220
        self.HEIGHT = 140
        self.PADDING = 10
        
        rect = pygame.Rect(position[0], position[1], self.WIDTH, self.HEIGHT)
        super().__init__(rect)
        self.slime = slime
        self.position = position

    def update(self, dt_ms: int) -> None:
        pass
    
    def render(self, surface: pygame.Surface):
        x, y = self.position
        
        # Background
        card_rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(surface, (30, 30, 40), card_rect, border_radius=8)
        pygame.draw.rect(surface, (80, 80, 100), card_rect, width=1, border_radius=8)
        
        # Slime portrait (left side)
        portrait_rect = pygame.Rect(x + self.PADDING, y + self.PADDING, 60, 60)
        render_slime_portrait(surface, self.slime.genome, portrait_rect)
        
        # Name
        render_text(surface, self.slime.name, 
                   (x + 80, y + 12), size=16, bold=True)
        
        # Team badge
        team_color = {
            TeamRole.DUNGEON:    (180, 60,  60),
            TeamRole.UNASSIGNED: (80,  80,  80),
        }.get(self.slime.team, (80, 80, 80))
        
        team_label = self.slime.team.value.upper()
        if self.slime.locked:
            team_label = "ON MISSION"
            team_color = (200, 140, 0)
        if not self.slime.alive:
            team_label = "FALLEN"
            team_color = (60, 60, 60)
            
        render_badge(surface, team_label, 
                    (x + 80, y + 36), team_color)
        
        # Stats from genome
        hp  = calculate_hp(self.slime.genome)
        atk = calculate_attack(self.slime.genome)
        spd = calculate_speed(self.slime.genome)
        
        render_stat(surface, "HP",  hp,  (x + 80, y + 66))
        render_stat(surface, "ATK", atk, (x + 80, y + 84))
        render_stat(surface, "SPD", spd, (x + 80, y + 102))
        
        # Genetic trait hint (bottom)
        trait_hint = get_dominant_trait(self.slime.genome)
        render_text(surface, f"Trait: {trait_hint}",
                   (x + self.PADDING, y + self.HEIGHT - 22),
                   size=12, color=(140, 140, 160))

# --- Local Rendering Helpers ---

def render_text(surface, text, pos, size=14, color=(255, 255, 255), bold=False):
    try:
        font = pygame.font.Font(None, size)
        if bold:
            font.set_bold(True)
        img = font.render(text, True, color)
        surface.blit(img, pos)
    except:
        pass

def render_badge(surface, text, pos, color):
    # Small rounded rect for badge
    try:
        font = pygame.font.Font(None, 12)
        font.set_bold(True)
        text_surf = font.render(text, True, (255, 255, 255))
        rect = pygame.Rect(pos[0], pos[1], text_surf.get_width() + 8, 16)
        pygame.draw.rect(surface, color, rect, border_radius=4)
        surface.blit(text_surf, (pos[0] + 4, pos[1] + 2))
    except:
        pass

def render_stat(surface, label, value, pos):
    # Label
    render_text(surface, label + ":", pos, size=14, color=(160, 160, 180))
    # Value (aligned right relative to label)
    render_text(surface, str(value), (pos[0] + 40, pos[1]), size=14, bold=True)

def get_dominant_trait(genome: SlimeGenome) -> str:
    traits = {
        "Curious": genome.curiosity,
        "Energetic": genome.energy,
        "Affectionate": genome.affection,
        "Shy": genome.shyness
    }
    # Return the trait with highest value
    return max(traits, key=traits.get)

def render_slime_portrait(surface, genome, rect):
    # Simplified rendering for small portrait
    center = rect.center
    radius = rect.width // 3
    
    color = genome.base_color
    p_color = genome.pattern_color
    shape = genome.shape
    
    # 1. Base Shape
    if shape == "round":
        pygame.draw.circle(surface, color, center, radius)
    elif shape == "cubic":
        s_rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
        pygame.draw.rect(surface, color, s_rect)
    elif shape == "elongated":
        s_rect = pygame.Rect(center[0] - int(radius * 1.5), center[1] - radius, radius * 3, radius * 2)
        pygame.draw.ellipse(surface, color, s_rect)
    else: # Fallback or crystalline/amorphous simplified
        pygame.draw.circle(surface, color, center, radius)

    # 2. Pattern (Simplified)
    pattern = genome.pattern
    if pattern == "spotted":
        pygame.draw.circle(surface, p_color, (center[0] - radius//3, center[1] - radius//3), radius//6)
    elif pattern == "striped":
        pygame.draw.line(surface, p_color, (center[0]-radius+2, center[1]), (center[0]+radius-2, center[1]), 2)
        
    # 3. Eyes
    eye_color = (0, 0, 0)
    eye_off = radius // 3
    pygame.draw.circle(surface, eye_color, (center[0] - eye_off, center[1] - eye_off), 2)
    pygame.draw.circle(surface, eye_color, (center[0] + eye_off, center[1] - eye_off), 2)
