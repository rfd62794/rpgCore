from typing import Tuple, Optional, Callable
import pygame
from src.shared.ui.button import Button
from src.shared.ui.label import Label

class Card(Button):
    """Specialized action/dialogue button with stance coloring and animations."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        number: int,
        text: str,
        stance_color: Tuple[int, int, int] = (100, 100, 120),
        on_click: Optional[Callable[[], None]] = None,
        on_hover: Optional[Callable[[], None]] = None,
        z_order: int = 0
    ):
        # Base colors adjusted for the Card style
        bg_normal = (18, 18, 30)
        bg_hover = (25, 25, 40)
        bg_pressed = (30, 30, 45)
        
        super().__init__(
            rect=rect,
            text="",  # We handle text custom
            on_click=on_click,
            on_hover=on_hover,
            keyboard_index=number,
            bg_color_normal=bg_normal,
            bg_color_hover=bg_hover,
            bg_color_pressed=bg_pressed,
            border_color=stance_color,  # Border is colored by stance
            border_width=2,
            z_order=z_order
        )
        
        self.number = number
        self.raw_text = text
        self.stance_color = stance_color
        
        # Override the button's auto-centered label
        self.remove_child(self.label)
        
        # Number Label (Left aligned)
        num_rect = pygame.Rect(rect.x + 15, rect.y, 30, rect.height)
        self.num_label = Label(num_rect, text=f"{number}.", font_size=24, color=(100, 100, 128))
        self.add_child(self.num_label)
        
        # Text Label (Indented)
        text_rect = pygame.Rect(rect.x + 50, rect.y + 10, rect.width - 60, rect.height - 20)
        self.text_label = Label(text_rect, text=text, font_size=24, color=(220, 220, 220), wrap_width=text_rect.width)
        self.add_child(self.text_label)
        
        # Animation properties
        self.fade_alpha = 0.0
        self.base_y = rect.y
        self.shift_y = 0

    def update(self, dt_ms: int) -> None:
        if not self.visible:
            return
            
        super().update(dt_ms)
        
        # Hover animation (3px shift up)
        target_shift = -3 if self.state in ("hover", "pressed") else 0
        if self.shift_y != target_shift:
            # Snap for simplicity, could lerp
            self.shift_y = target_shift
            self.rect.y = self.base_y + self.shift_y
            
            # Sync children y-positions
            self.num_label.rect.y = self.rect.y
            self.text_label.rect.y = self.rect.y + 10
            self.num_label._cache_text()
            self.text_label._cache_text()

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible or self.fade_alpha <= 0:
            return
            
        # Draw background
        fill_color = self.bg_color
        if self.state == "pressed": # Simulate selected light background
            fill_color = (30, 30, 46)
            
        pygame.draw.rect(surface, fill_color, self.rect, border_radius=self.border_radius)
        
        # Draw stance border (opacity varies by state)
        if self.border_width > 0:
            border_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            
            alpha = 100 # Normal 40%
            if self.state == "hover":
                alpha = 200 # Hover 80%
            elif self.state == "pressed":
                alpha = 255 # Selected 100%
                
            color_with_alpha = (*self.stance_color, alpha)
            pygame.draw.rect(border_surface, color_with_alpha, border_surface.get_rect(), width=self.border_width, border_radius=self.border_radius)
            
            # Master fade alpha over the whole card
            border_surface.set_alpha(int(self.fade_alpha))
            surface.blit(border_surface, self.rect.topleft)
            
        # Text rendering would ideally respect fade_alpha here as well
        # Note: Pygame font rendering doesn't natively support alpha without blazing to a temp surface.
        # For this component baseline, we just render children if alpha > 0
        if self.fade_alpha > 0:
            for child in self.children:
                child.render(surface)
