import pygame
from src.shared.rendering.font_manager import FontManager

STANCE_COLORS = {
    "PROFESSIONAL": (200, 200, 212), # #C8C8D4
    "WEARY": (136, 153, 170),        # #8899AA
    "CURIOUS": (136, 187, 204),      # #88BBCC
    "RELUCTANT": (204, 153, 68),     # #CC9944
    "MOVED": (170, 136, 187)         # #AA88BB
}
BG_COLOR = (18, 18, 30)              # #12121E
SELECTED_BG_COLOR = (30, 30, 46)     # #1E1E2E
NUMBER_COLOR = (102, 102, 128)       # #666680

class DialogueCard:
    def __init__(self, number: int, text: str, stance: str, rect: pygame.Rect):
        self.number = number
        self.text = text
        self.stance = stance
        
        # We need a copy of the rect since we might shift it visually on hover, 
        # but the logical rect for collision should probably stay stable.
        self.logical_rect = rect.copy()
        self.visual_rect = rect.copy()
        
        self.hover_state = False
        self.selected_state = False
        self.fade_alpha = 0  # 0 to 255
        
        self.color = STANCE_COLORS.get(stance.upper(), (200, 200, 200))
        
        # Pre-render text surfaces if font manager is ready
        self._font_mgr = FontManager()
        self.num_font = self._font_mgr.get_font("Arial", 14)
        self.text_font = self._font_mgr.get_font("Arial", 20)
        
        self.num_sur = self.num_font.render(str(self.number), True, NUMBER_COLOR) if self.num_font != "DummyFont" else pygame.Surface((1, 1))
        self.text_sur = self.text_font.render(self.text, True, self.color) if self.text_font != "DummyFont" else pygame.Surface((1, 1))
        
        # Render a brighter text for hover
        bright_color = tuple(min(255, int(c * 1.2)) for c in self.color)
        self.hover_text_sur = self.text_font.render(self.text, True, bright_color) if self.text_font != "DummyFont" else pygame.Surface((1, 1))

    def handle_hover(self, mouse_pos: tuple[int, int]) -> bool:
        """Updates hover state based on mouse position. Returns True if hovered."""
        if self.logical_rect.collidepoint(mouse_pos):
            if not self.hover_state:
                self.hover_state = True
                self.visual_rect.y = self.logical_rect.y - 3 # 3px shift
            return True
        else:
            if self.hover_state:
                self.hover_state = False
                self.visual_rect.y = self.logical_rect.y
            return False

    def select(self) -> None:
        self.selected_state = True

    def render(self, surface: pygame.Surface) -> None:
        if self.fade_alpha <= 0:
            return

        # Create a surface for the card that supports alpha
        card_surface = pygame.Surface((self.visual_rect.width, self.visual_rect.height), pygame.SRCALPHA)
        
        # Fill background
        if self.selected_state:
            card_surface.fill((*SELECTED_BG_COLOR, self.fade_alpha))
        else:
            card_surface.fill((*BG_COLOR, self.fade_alpha))
        
        # Borders and fill depending on state
        if self.selected_state:
            # Full border, lightened background
            border_alpha = min(255, self.fade_alpha)
            pygame.draw.rect(card_surface, (*self.color, border_alpha), card_surface.get_rect(), 2)
        elif self.hover_state:
            # 90% opacity border
            border_alpha = min(int(0.9 * 255), self.fade_alpha)
            pygame.draw.rect(card_surface, (*self.color, border_alpha), card_surface.get_rect(), 2)
        else:
            # 50% opacity border
            border_alpha = min(int(0.5 * 255), self.fade_alpha)
            pygame.draw.rect(card_surface, (*self.color, border_alpha), card_surface.get_rect(), 2)
            
        # Draw number (left aligned, vertically centered)
        num_pos = (16, (self.visual_rect.height - self.num_sur.get_height()) // 2)
        if hasattr(self.num_sur, "set_alpha"):
            self.num_sur.set_alpha(self.fade_alpha)
        card_surface.blit(self.num_sur, num_pos)
        
        # Draw text (centered vertically, padded horizontally)
        t_sur = self.hover_text_sur if self.hover_state else self.text_sur
        if hasattr(t_sur, "set_alpha"):
            t_sur.set_alpha(self.fade_alpha)
            
        # Text starts 40px from left edge (room for number + padding)
        text_x = 40 
        text_y = (self.visual_rect.height - t_sur.get_height()) // 2
        card_surface.blit(t_sur, (text_x, text_y))
        
        # Blit the compiled card onto the main surface
        surface.blit(card_surface, self.visual_rect.topleft)
