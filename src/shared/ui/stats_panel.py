import pygame
from typing import Tuple, Optional
from src.shared.ui.base import UIComponent
from src.shared.teams.roster import RosterSlime
from src.shared.teams.stat_calculator import calculate_hp, calculate_attack, calculate_speed

class StatsPanel(UIComponent):
    """
    Unified stats panel to be reused in Profile, Breeding, and Racing scenes.
    """
    def __init__(self, slime: RosterSlime, position: Tuple[int, int], width: int = 200):
        self.WIDTH = width
        self.HEIGHT = 120
        self.PADDING = 10
        
        rect = pygame.Rect(position[0], position[1], self.WIDTH, self.HEIGHT)
        super().__init__(rect)
        self.slime = slime
        self.position = position

    def update(self, dt_ms: int):
        """No periodic updates needed for this static panel."""
        pass

    def render(self, surface: pygame.Surface):
        x, y = self.position
        
        # Panel Background
        panel_rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(surface, (40, 45, 55), panel_rect, border_radius=6)
        pygame.draw.rect(surface, (100, 110, 130), panel_rect, width=1, border_radius=6)
        
        # Calculate stats
        hp  = calculate_hp(self.slime.genome, self.slime.level)
        atk = calculate_attack(self.slime.genome, self.slime.level)
        spd = calculate_speed(self.slime.genome, self.slime.level)
        
        self._render_stat(surface, "HEALTH", hp,  (x + self.PADDING, y + self.PADDING), (200, 100, 100))
        self._render_stat(surface, "ATTACK", atk, (x + self.PADDING, y + self.PADDING + 30), (220, 140, 60))
        self._render_stat(surface, "SPEED",  spd, (x + self.PADDING, y + self.PADDING + 60), (100, 180, 220))
        
        # Genetic dominance hint
        dominance = self._get_dominance_text()
        self._render_text(surface, f"DNA: {dominance}", (x + self.PADDING, y + self.HEIGHT - 20), size=12, color=(140, 140, 160))

    def _render_stat(self, surface, label, value, pos, color):
        # Stat Label
        self._render_text(surface, label, pos, size=14, color=(160, 160, 180))
        
        # Bar Placeholder
        bar_x = pos[0] + 60
        bar_w = self.WIDTH - 80
        pygame.draw.rect(surface, (30, 30, 40), (bar_x, pos[1] + 4, bar_w, 8))
        
        # Calculate cultural max (at Lv.10 reference)
        # HP: ~200-300, ATK: ~40-60, SPD: ~15-20
        # We'll use a safer relative mapping
        cultural_max = 100 # Default
        culture = self.slime.genome.cultural_base
        from src.shared.genetics.cultural_base import CULTURAL_PARAMETERS
        params = CULTURAL_PARAMETERS[culture]
        
        if label == "HEALTH":
            cultural_max = 200 * params.hp_modifier
        elif label == "ATTACK":
            cultural_max = 40 * params.attack_modifier
        elif label == "SPEED":
            cultural_max = 15 * params.speed_modifier
            
        fill_w = int(bar_w * (min(1.0, value / cultural_max)))
        if fill_w > 0:
            pygame.draw.rect(surface, color, (bar_x, pos[1] + 4, fill_w, 8))
            
        # Value Text
        self._render_text(surface, str(value), (bar_x + bar_w + 5, pos[1]), size=14, bold=True)

    def _render_text(self, surface, text, pos, size=14, color=(255, 255, 255), bold=False):
        try:
            font = pygame.font.Font(None, size)
            if bold: font.set_bold(True)
            img = font.render(text, True, color)
            surface.blit(img, pos)
        except: pass

    def _get_dominance_text(self) -> str:
        traits = {
            "C": self.slime.genome.curiosity,
            "E": self.slime.genome.energy,
            "A": self.slime.genome.affection,
            "S": self.slime.genome.shyness
        }
        # Get highest
        top = max(traits, key=traits.get)
        return f"{top} ({int(traits[top]*100)}%)"
