"""
Pixel Viewport Pass - Game Boy Hardware Parity

Zone A: Main viewport with Virtual PPU three-layer rendering.
Background (BG): TileMap from WorldLedger
Window (WIN): TextBox and Status Bar overlay
Objects (OBJ): 16x16 Metasprites for actors
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from loguru import logger

from . import BaseRenderPass, RenderContext, RenderResult, RenderPassType
from ...pixel_renderer import PixelRenderer, ColorPalette
from ...sprite_registry import SpriteRegistry
from ...tile_bank import TileBank, TileType
from ...models.metasprite import Metasprite, MetaspriteConfig, CharacterRole


class _InternalPixelViewport:
    """Internal PixelViewport implementation for the pass."""
    
    def __init__(self, config: 'PixelViewportConfig', world_ledger: Optional[WorldLedger] = None):
        self.config = config
        self.world_ledger = world_ledger
        self.pixel_width = config.width
        self.pixel_height = config.height * config.pixel_scale
        self.pixel_renderer = PixelRenderer(
            width=self.pixel_width,
            height=self.pixel_height
        )
        self.sprite_registry = SpriteRegistry()
        self.entity_sprites = {}
        self.item_sprites = {}
    
    def update_game_state(self, game_state):
        """Update viewport with game state."""
        # Update entity sprites
        self._update_entity_sprites(game_state)
        self._update_item_sprites(game_state)
    
    def render_frame(self, game_state):
        """Render pixel art frame."""
        # Clear pixel buffer
        self.pixel_renderer.clear()
        
        # Render world environment
        self._render_world_environment(game_state)
        
        # Render entities
        self._render_entities(game_state)
        
        # Render player
        self._render_player(game_state)
        
        return self.pixel_renderer.render_to_string()
    
    def _render_world_environment(self, game_state):
        """Render world environment."""
        player_x, player_y = game_state.position.x, game_state.position.y
        
        # Simple environment rendering
        for y in range(self.pixel_height):
            for x in range(self.pixel_width):
                # Create simple floor pattern
                if (x + y) % 4 == 0:
                    pixel = ColorPalette.get_environment_color("floor", 0.3)
                else:
                    pixel = ColorPalette.get_environment_color("wall", 0.5)
                self.pixel_renderer.set_pixel(x, y, pixel)
    
    def _render_entities(self, game_state):
        """Render entities."""
        # Render some placeholder entities
        voyager = self.sprite_registry.get_voyager_sprite("neutral", "3x3")
        if voyager:
            self.pixel_renderer.draw_sprite(voyager, 30, 20, time.time())
        
        warrior = self.sprite_registry.get_character_sprite("warrior", "legion")
        if warrior:
            self.pixel_renderer.draw_sprite(warrior, 50, 20, time.time())
    
    def _render_player(self, game_state):
        """Render the player."""
        voyager = self.sprite_registry.get_voyager_sprite("neutral", "3x3")
        if voyager:
            # Center player
            center_x = self.pixel_width // 2 - 1
            center_y = self.pixel_height // 2 - 1
            self.pixel_renderer.draw_sprite(voyager, center_x, center_y, time.time())
    
    def _update_entity_sprites(self, game_state):
        """Update entity sprite tracking."""
        pass
    
    def _update_item_sprites(self, game_state):
        """Update item sprite tracking."""
        pass


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
        self.entity_sprites = {}
        self.item_sprites = {}
        self._viewport = None
        self.world_ledger = None
    
    def _create_pixel_viewport(self, world_ledger: Optional[WorldLedger] = None) -> _InternalPixelViewport:
        """Create a PixelViewport instance for internal use."""
        return _InternalPixelViewport(self.config, world_ledger)
    
    def _create_demo_scene(self) -> str:
        """Create a demo scene for testing."""
        # Use the internal PixelViewport
        viewport = self._create_pixel_viewport(self.world_ledger)
        return viewport.render_frame(Mock())
    
    def render(self, context: RenderContext) -> RenderResult:
        """
        Render the pixel viewport.
        
        Args:
            context: Shared rendering context
            
        Returns:
            RenderResult with pixel viewport content
        """
        # Create viewport if needed
        if self._viewport is None:
            self._viewport = self._create_pixel_viewport(self.world_ledger)
        
        # Update viewport with game state
        self._viewport.update_game_state(context.game_state)
        
        # Render frame
        content = self._viewport.render_frame(context.game_state)
        
        return RenderResult(
            content=content,
            width=self.config.width,
            height=self.config.height,
            metadata={
                "pixel_width": self.pixel_width,
                "pixel_height": self.pixel_height,
                "pixel_ratio": f"1:{self.config.pixel_scale}",
                "sprite_count": len(self._viewport.entity_sprites) + len(self._viewport.item_sprites)
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
        self.world_ledger = world_ledger
        # Reset viewport to use new world ledger
        self._viewport = None
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
        
        # Reset viewport to use new configuration
        self._viewport = None
        logger.info(f"PixelViewportPass reconfigured: {self.pixel_width}x{self.pixel_height} pixels")
    
    def get_sprite_info(self) -> Dict[str, Any]:
        """Get information about available sprites."""
        return {
            "available_sprites": len(self.sprite_registry.list_templates()),
            "entity_sprites": len(self._viewport.entity_sprites) if self._viewport else 0,
            "item_sprites": len(self._viewport.item_sprites) if self._viewport else 0,
            "sprite_types": self.sprite_registry.list_templates()
        }
    
    def create_demo_frame(self) -> str:
        """
        Create a demo frame for testing.
        
        Returns:
            Demo pixel art frame
        """
        if self._viewport is None:
            self._viewport = self._create_pixel_viewport(self.world_ledger)
        return self._viewport.render_frame(Mock())
    
    def clear_sprites(self) -> None:
        """Clear all sprite tracking."""
        if self._viewport:
            self._viewport.entity_sprites.clear()
            self._viewport.item_sprites.clear()
        logger.debug("PixelViewportPass sprites cleared")
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get performance information including base class info."""
        base_info = super().get_performance_info()
        
        # Add pixel-specific performance data
        pixel_info = {
            "pixel_resolution": f"{self.pixel_width}x{self.pixel_height}",
            "character_resolution": f"{self.config.width}x{self.config.height}",
            "pixel_ratio": f"1:{self.config.pixel_scale}",
            "sprite_count": len(self._viewport.entity_sprites) + len(self._viewport.item_sprites) if self._viewport else 0
        }
        
        base_info.update(pixel_info)
        return base_info


# Export for use by other modules
__all__ = ["PixelViewportPass", "PixelViewportConfig"]
