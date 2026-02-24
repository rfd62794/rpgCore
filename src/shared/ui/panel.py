from typing import List, Optional, Tuple
import pygame
from src.shared.ui.base import UIComponent

class Panel(UIComponent):
    """A container component that can hold and render children."""
    
    def __init__(
        self, 
        rect: pygame.Rect, 
        bg_color: Tuple[int, int, int] = (20, 20, 30),
        border_color: Tuple[int, int, int] = (100, 100, 120),
        border_width: int = 2,
        border_radius: int = 5,
        title: Optional[str] = None,
        z_order: int = 0
    ):
        super().__init__(rect, z_order)
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.title = title
        
        self.children: List[UIComponent] = []
        
        # Simple font for title if provided
        if self.title:
            try:
                self.title_font = pygame.font.Font(None, 24)
            except:
                self.title_font = None

    def add_child(self, component: UIComponent) -> None:
        if component not in self.children:
            self.children.append(component)
            self.children.sort(key=lambda c: c.z_order)

    def remove_child(self, component: UIComponent) -> None:
        if component in self.children:
            self.children.remove(component)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Propagate events to children in reverse z-order. Returns True if consumed."""
        if not self.visible:
            return False
            
        # Panels usually don't consume events themselves (unless they have a background click handler)
        # but they MUST pass them to children.
        for child in reversed(self.children):
            if hasattr(child, "handle_event") and child.handle_event(event):
                return True
        return False

    def update(self, dt_ms: int) -> None:
        if not self.visible:
            return
        for child in self.children:
            child.update(dt_ms)

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
            
        # Draw background
        if self.bg_color:
            pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
            
        # Draw border
        if self.border_width > 0 and self.border_color:
            pygame.draw.rect(surface, self.border_color, self.rect, width=self.border_width, border_radius=self.border_radius)
            
        # Draw title
        if self.title and self.title_font:
            title_surf = self.title_font.render(self.title, True, self.border_color)
            surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))
            
        # Render children
        for child in self.children:
            child.render(surface)
