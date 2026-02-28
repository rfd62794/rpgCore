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
from src.shared.ui.stats_panel import StatsPanel

from src.shared.ui.spec import UISpec

class ProfileCard(UIComponent):
    def __init__(self, slime: RosterSlime, position: Tuple[int, int], spec: UISpec):
        # Card dimensions: respect parent panel boundaries
        side_panel_width = spec.screen_width * 0.35  # HubLayout side panel width
        self.WIDTH = min(spec.card_width, int(side_panel_width - spec.padding_md * 2))
        self.HEIGHT = spec.card_height
        self.PADDING = spec.padding_sm
        
        # Calculate inner dimensions
        self.CARD_INNER_WIDTH = self.WIDTH - (self.PADDING * 2)
        self.PORTRAIT_SIZE = 60
        self.TEXT_AREA_WIDTH = self.CARD_INNER_WIDTH - self.PORTRAIT_SIZE - (self.PADDING * 3)
        
        rect = pygame.Rect(position[0], position[1], self.WIDTH, self.HEIGHT)
        super().__init__(rect)
        self.slime = slime
        self.position = position
        self.spec = spec
        
        # Add StatsPanel with proper width constraint for right side
        stats_x = position[0] + self.PORTRAIT_SIZE + self.PADDING * 2
        stats_y = position[1] + self.PORTRAIT_SIZE + self.PADDING
        self.stats_panel = StatsPanel(slime, (stats_x, stats_y), width=100)  # Smaller width for right side

    def update(self, dt_ms: int):
        """No periodic updates needed for the card itself."""
        pass

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle click events on the profile card."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.contains_point(event.pos[0], event.pos[1]):
                # Card was clicked - you can add custom behavior here
                # For now, just return True to consume the event
                return True
        return False

    def render(self, surface: pygame.Surface):
        x, y = self.position
        
        # Background
        card_rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        bg_color = self.spec.color_surface_alt if self.slime.is_elder else self.spec.color_surface
        border_color = self.spec.color_accent if self.slime.is_elder else self.spec.color_border
        border_w = 2
        
        pygame.draw.rect(surface, bg_color, card_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, card_rect, width=border_w, border_radius=8)
        
        # Slime portrait (left side)
        portrait_rect = pygame.Rect(x + self.PADDING, y + self.PADDING, self.PORTRAIT_SIZE, self.PORTRAIT_SIZE)
        render_slime_portrait(surface, self.slime.genome, portrait_rect)
        
        # Name, Level & Generation (in text area)
        text_x = x + self.PORTRAIT_SIZE + self.PADDING * 2
        render_text(surface, self.slime.name, 
                   (text_x, y + 12), size=16, bold=True)
        render_text(surface, f"Lv.{self.slime.level}",
                   (text_x, y + 26), size=14, color=(200, 200, 100))
        render_text(surface, f"Gen {self.slime.generation}",
                    (text_x, y + 40), size=12, color=(160, 160, 180))
        
        # XP Bar (constrained to text area)
        xp_rect = pygame.Rect(text_x, y + 50, self.TEXT_AREA_WIDTH // 2, 4)
        pygame.draw.rect(surface, (40, 40, 50), xp_rect)
        xp_pct = min(1.0, self.slime.experience / self.slime.xp_to_next_level)
        if xp_pct > 0:
            fill_rect = pygame.Rect(xp_rect.x, xp_rect.y, int(xp_rect.width * xp_pct), xp_rect.height)
            pygame.draw.rect(surface, (100, 200, 100), fill_rect)

        # Team & Culture badges (below XP bar)
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
                    (text_x, y + 60), team_color)
        
        # Culture badge
        culture_color = {
            "ember":   (200, 80, 40),
            "crystal": (140, 200, 255),
            "moss":    (80, 180, 80),
            "coastal": (80, 140, 180),
            "void":    (100, 40, 140),
            "mixed":   (140, 140, 140)
        }.get(self.slime.genome.cultural_base.value, (140, 140, 140))
        
        render_badge(surface, self.slime.genome.cultural_base.value.upper(),
                    (text_x + 70, y + 60), culture_color)
        
        # Stats panel on the right side
        stats_x = x + self.WIDTH - 120  # Position stats on the right side
        stats_y = y + 12  # Align with name
        self.stats_panel.position = (stats_x, stats_y)
        self.stats_panel.render(surface)
        
        # Genetic trait hint (bottom) - render as separate badges
        trait_hint = get_dominant_trait(self.slime.genome)
        breeding_status = "" if self.slime.can_breed else "Young"
        
        # Trait badge
        trait_color = (120, 100, 180)  # Purple for traits
        render_badge(surface, trait_hint, 
                    (x + self.PADDING, y + self.HEIGHT - 20), trait_color)
        
        # Age badge if not breedable
        if breeding_status:
            age_color = (200, 140, 60)  # Orange for young
            trait_width = len(trait_hint) * 8 + 16  # Approximate badge width
            render_badge(surface, breeding_status, 
                        (x + self.PADDING + trait_width + 8, y + self.HEIGHT - 20), age_color)

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
