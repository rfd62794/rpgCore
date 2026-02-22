import pygame
from typing import Callable, Tuple, Optional
from src.shared.ui.base import UIComponent
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label

class Button(Panel):
    """Interactive clickable region with states."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        text: str = "",
        on_click: Optional[Callable[[], None]] = None,
        on_hover: Optional[Callable[[], None]] = None,
        keyboard_index: Optional[int] = None,
        bg_color_normal: Tuple[int, int, int] = (30, 30, 40),
        bg_color_hover: Tuple[int, int, int] = (50, 50, 70),
        bg_color_pressed: Tuple[int, int, int] = (20, 20, 30),
        bg_color_disabled: Tuple[int, int, int] = (15, 15, 20),
        border_color: Tuple[int, int, int] = (100, 100, 120),
        border_width: int = 2,
        z_order: int = 0
    ):
        super().__init__(
            rect=rect, 
            bg_color=bg_color_normal, 
            border_color=border_color, 
            border_width=border_width, 
            z_order=z_order
        )
        
        self.text = text
        self.on_click = on_click
        self.on_hover = on_hover
        self.keyboard_index = keyboard_index
        
        self.bg_color_normal = bg_color_normal
        self.bg_color_hover = bg_color_hover
        self.bg_color_pressed = bg_color_pressed
        self.bg_color_disabled = bg_color_disabled
        
        self.state = "normal"  # normal, hover, pressed, disabled
        self.enabled = True
        
        # Center the label inside the button by default
        label_rect = pygame.Rect(rect.x + border_width, rect.y + border_width, rect.width - border_width*2, rect.height - border_width*2)
        self.label = Label(label_rect, text=text, align="center")
        self.add_child(self.label)
        
        self._was_hovered = False

    def set_enabled(self, v: bool) -> None:
        self.enabled = v
        if not v:
            self.state = "disabled"
            self.bg_color = self.bg_color_disabled
        else:
            self.state = "normal"
            self.bg_color = self.bg_color_normal

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process Pygame events to manage click states. Returns True if event was consumed."""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            is_hovered = self.contains_point(event.pos[0], event.pos[1])
            if is_hovered:
                if self.state != "pressed":
                    self.state = "hover"
                    self.bg_color = self.bg_color_hover
                if not self._was_hovered:
                    if self.on_hover:
                        self.on_hover()
                    self._was_hovered = True
                return True
            else:
                self.state = "normal"
                self.bg_color = self.bg_color_normal
                self._was_hovered = False
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains_point(event.pos[0], event.pos[1]):
                self.state = "pressed"
                self.bg_color = self.bg_color_pressed
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.state == "pressed":
                self.state = "hover" if self.contains_point(event.pos[0], event.pos[1]) else "normal"
                self.bg_color = self.bg_color_hover if self.state == "hover" else self.bg_color_normal
                if self.contains_point(event.pos[0], event.pos[1]) and self.on_click:
                    self.on_click()
                return True
                
        # Optional keyboard number trigger
        elif event.type == pygame.KEYDOWN and self.keyboard_index is not None:
            # Shift indices maps 1->K_1
            target_key = getattr(pygame, f"K_{self.keyboard_index}", None)
            if event.key == target_key and self.on_click:
                self.on_click()
                return True
                
        return False
