"""
Render Adapter Contract — Abstraction for different rendering backends.
"""

from abc import ABC, abstractmethod
from typing import Any


class RenderAdapter(ABC):
    """
    Abstract base class for rendering adapters.
    Allows the engine to swap between PyGame, Terminal, or other backends.
    """

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the rendering backend."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up the rendering backend."""
        pass

    @abstractmethod
    def clear(self, color: Any) -> None:
        """Clear the screen/surface with a background color."""
        pass

    @abstractmethod
    def present(self) -> None:
        """Present the rendered frame to the screen."""
        pass
