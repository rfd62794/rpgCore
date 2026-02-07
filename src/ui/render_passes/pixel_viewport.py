"""
Pixel Viewport Pass - Half-Block Pixel Art Rendering

Zone A: Main viewport with 2:1 pixel ratio.
Provides solid 8-bit sprites for the Voyager and entities with Game Boy/NES visual parity.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from loguru import logger

from .. import BaseRenderPass, RenderContext, RenderResult, RenderPassType
from ...pixel_renderer import PixelRenderer, ColorPalette
from ...sprite_registry import SpriteRegistry
from ...pixel_viewport import PixelViewport, ViewportConfig


@dataclass
class PixelViewportConfig:
    """Configuration for the pixel viewport pass."""
    width: int = 60      # Character width (leaves room for other zones)
    height: int = 24     # Character height
    pixel_scale: int = 2  # 2:1 pixel ratio (half-block technique)
    show_sprites: bool = True
    show_environment: bool = True
    animation_speed: float = 1.0
    faction_colors: bool = True


class PixelViewportPass(BaseRenderPass):
    """
    Pixel art rendering pass for the main viewport zone.
    
    Uses half-block Unicode characters to achieve 2:1 pixel ratio,
    providing solid 8-bit sprite rendering with Game Boy/NES visual parity.
    """
    
    def __init__(self, config: Optional[PixelViewportConfig] = None):
        """
        Initialize the pixel viewport pass.
        
        Args:
            config: Optional viewport configuration
        """
        super().__init__(RenderPassType.PIXEL_VIEWPORT)
        self.config = config or PixelViewportConfig()
        
        # Calculate pixel dimensions (2:1 ratio)
        self.pixel_width = self.config.width
        self.pixel_height = self.config.height * self.config.pixel_scale
        
        # Initialize pixel renderer
        self.pixel_renderer = PixelRenderer(
            width=self.pixel_width,
            height=self.pixel_height
        )
        
        # Initialize sprite registry
        self.sprite_registry = SpriteRegistry()
        
        # Create viewport for integration
        viewport_config = ViewportConfig(
            pixel_width=self.pixel_width,
            pixel_height=self.pixel_height,
            show_grid=False,
            animation_speed=self.config.animation_speed
        )
        self.viewport = PixelViewport(None, viewport_config)  # No world ledger needed for pass
        
        logger.info(f"PixelViewportPass initialized: {self.pixel_width}x{self.pixel_height} pixels")
    
    def render(self, context: RenderContext) -> RenderResult:
        """
        Render the pixel viewport.
        
        Args:
            context: Shared rendering context
            
        Returns:
            RenderResult with pixel viewport content
        """
        # Update viewport with game state
        self.viewport.update_game_state(context.game_state)
        
        # Render frame
        content = self.viewport.render_frame(context.game_state)
        
        return RenderResult(
            content=content,
            width=self.config.width,
            height=self.config.height,
            metadata={
                "pixel_width": self.pixel_width,
                "pixel_height": self.pixel_height,
                "pixel_ratio": f"1:{self.config.pixel_scale}",
                "sprite_count": len(self.viewport.entity_sprites) + len(self.viewport.item_sprites)
            }
        )
    
    def get_optimal_size(self, context: RenderContext) -> Tuple[int, int]:
        """Get optimal size for pixel viewport."""
        return (self.config.width, self.config.height)
    
    def set_world_ledger(self, world_ledger) -> None:
        """
        Set the world ledger for the viewport.
        
        Args:
            world_ledger: World ledger instance
        """
        self.viewport.world_ledger = world_ledger
        logger.debug("PixelViewportPass world ledger updated")
    
    def update_config(self, config: PixelViewportConfig) -> None:
        """
        Update viewport configuration.
        
        Args:
            config: New configuration
        """
        self.config = config
        
        # Recalculate pixel dimensions
        self.pixel_width = config.width
        self.pixel_height = config.height * config.pixel_scale
        
        # Reinitialize components
        self.pixel_renderer = PixelRenderer(
            width=self.pixel_width,
            height=self.pixel_height
        )
        
        viewport_config = ViewportConfig(
            pixel_width=self.pixel_width,
            pixel_height=self.pixel_height,
            show_grid=False,
            animation_speed=config.animation_speed
        )
        self.viewport = PixelViewport(self.viewport.world_ledger, viewport_config)
        
        logger.info(f"PixelViewportPass reconfigured: {self.pixel_width}x{self.pixel_height} pixels")
    
    def get_sprite_info(self) -> Dict[str, Any]:
        """Get information about available sprites."""
        return {
            "available_sprites": len(self.sprite_registry.list_templates()),
            "entity_sprites": len(self.viewport.entity_sprites),
            "item_sprites": len(self.viewport.item_sprites),
            "sprite_types": self.sprite_registry.list_templates()
        }
    
    def create_demo_frame(self) -> str:
        """
        Create a demo frame for testing.
        
        Returns:
            Demo pixel art frame
        """
        return self.viewport.create_demo_scene()
    
    def clear_sprites(self) -> None:
        """Clear all sprite tracking."""
        self.viewport.entity_sprites.clear()
        self.viewport.item_sprites.clear()
        logger.debug("PixelViewportPass sprites cleared")
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get performance information including base class info."""
        base_info = super().get_performance_info()
        
        # Add pixel-specific performance data
        pixel_info = {
            "pixel_resolution": f"{self.pixel_width}x{self.pixel_height}",
            "character_resolution": f"{self.config.width}x{self.config.height}",
            "pixel_ratio": f"1:{self.config.pixel_scale}",
            "sprite_count": len(self.viewport.entity_sprites) + len(self.viewport.item_sprites)
        }
        
        base_info.update(pixel_info)
        return base_info


# Export for use by other modules
__all__ = ["PixelViewportPass", "PixelViewportConfig"]
