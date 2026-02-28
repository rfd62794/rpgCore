from abc import ABC, abstractmethod
import pygame

class UIComponent(ABC):
    """Base class for all shared UI components."""
    
    def __init__(self, rect: pygame.Rect, z_order: int = 0):
        self.rect = rect
        self.visible: bool = True
        self.z_order: int = z_order

    @abstractmethod
    def update(self, dt_ms: int) -> None:
        """Update component state."""
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Render component to the target surface."""
        pass

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within the component's rect."""
        return self.rect.collidepoint(x, y)

    def set_visible(self, v: bool) -> None:
        """Set component visibility."""
        self.visible = v

    def add_to(self, container: list):
        """Helper to add this component to a list and return self."""
        if self not in container:
            container.append(self)
        return self
