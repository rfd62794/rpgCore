"""
Legacy Graphics Engine - Frozen Artifact
Maintained for backward compatibility with ADR 122: Universal Packet Enforcement

This is the original GraphicsEngine from the DGT project, preserved as a frozen artifact.
The Tri-Modal Engine uses the LegacyGraphicsEngineAdapter to interface with this code
without modifying it.
"""

import time
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from loguru import logger

# Import core state (if available)
try:
    from ...core.state import (
        GameState, TileType, BiomeType, SubtitleEvent,
        VIEWPORT_WIDTH_PIXELS, VIEWPORT_HEIGHT_PIXELS,
        TILE_SIZE_PIXELS, VIEWPORT_TILES_X, VIEWPORT_TILES_Y,
        RENDER_LAYERS, COLOR_PALETTE
    )
except ImportError:
    # Fallback constants
    VIEWPORT_WIDTH_PIXELS = 160
    VIEWPORT_HEIGHT_PIXELS = 144
    TILE_SIZE_PIXELS = 8
    VIEWPORT_TILES_X = 20
    VIEWPORT_TILES_Y = 18
    RENDER_LAYERS = None
    COLOR_PALETTE = None

from ...core.constants import TARGET_FPS, FRAME_DELAY_MS


class RenderLayer(Enum):
    """Rendering layers for composition"""
    BACKGROUND = 0
    TERRAIN = 1
    ENTITIES = 2
    EFFECTS = 3
    UI = 4
    SUBTITLES = 5


@dataclass
class RenderFrame:
    """Complete frame with all layers"""
    width: int
    height: int
    layers: Dict[RenderLayer, np.ndarray]
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        # Ensure all layers exist
        if RENDER_LAYERS:
            for layer in RENDER_LAYERS:
                if layer not in self.layers:
                    self.layers[layer] = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        else:
            # Fallback layers
            for layer in RenderLayer:
                if layer not in self.layers:
                    self.layers[layer] = np.zeros((self.height, self.width, 3), dtype=np.uint8)


@dataclass
class TileBank:
    """Tile bank for different environments"""
    environment: str
    tiles: Dict[Any, np.ndarray]
    palette: Dict[str, Tuple[int, int, int]]
    
    def get_tile(self, tile_type: Any) -> np.ndarray:
        """Get tile sprite for type"""
        return self.tiles.get(tile_type, self.tiles.get(TileType.GRASS))


@dataclass
class Viewport:
    """Camera viewport for world rendering"""
    center_x: int
    center_y: int
    width_tiles: int
    height_tiles: int
    
    def get_world_bounds(self) -> Tuple[int, int, int, int]:
        """Get world coordinates bounds"""
        half_width = self.width_tiles // 2
        half_height = self.height_tiles // 2
        
        min_x = max(0, self.center_x - half_width)
        max_x = min(50, self.center_x + half_width)
        min_y = max(0, self.center_y - half_height)
        max_y = min(50, self.center_y + half_height)
        
        return min_x, min_y, max_x, max_y
    
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.center_x) * TILE_SIZE_PIXELS + VIEWPORT_WIDTH_PIXELS // 2
        screen_y = (world_y - self.center_y) * TILE_SIZE_PIXELS + VIEWPORT_HEIGHT_PIXELS // 2
        return screen_x, screen_y


class GraphicsEngine:
    """160x144 PPU rendering engine with Game Boy parity
    
    This is the original GraphicsEngine, preserved as a frozen artifact.
    Use TriModalEngine with LegacyGraphicsEngineAdapter for new development.
    """
    
    def __init__(self, width: int = VIEWPORT_WIDTH_PIXELS, height: int = VIEWPORT_HEIGHT_PIXELS):
        self.width = width
        self.height = height
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.fps_history: List[float] = []
        self.max_fps_history = 60
        self.frame_count = 0
        
        # Viewport
        self.viewport = Viewport(10, 10, VIEWPORT_TILES_X, VIEWPORT_TILES_Y)
        
        # Tile banks
        self.tile_banks: Dict[str, TileBank] = {}
        self._create_default_tile_banks()
        
        # Current frame
        self.current_frame: Optional[RenderFrame] = None
        
        # Subtitle system
        self.subtitle_queue: List[SubtitleEvent] = []
        self.subtitle_display_time = 3.0  # seconds
        
        logger.info("🎮 Legacy GraphicsEngine initialized (frozen artifact)")
    
    def _create_default_tile_banks(self):
        """Create default tile banks for different environments"""
        try:
            import numpy as np
            
            # Create basic tiles
            grass_tile = np.full((TILE_SIZE_PIXELS, TILE_SIZE_PIXELS, 3), [34, 139, 34], dtype=np.uint8)
            stone_tile = np.full((TILE_SIZE_PIXELS, TILE_SIZE_PIXELS, 3), [128, 128, 128], dtype=np.uint8)
            water_tile = np.full((TILE_SIZE_PIXELS, TILE_SIZE_PIXELS, 3), [0, 100, 200], dtype=np.uint8)
            dirt_tile = np.full((TILE_SIZE_PIXELS, TILE_SIZE_PIXELS, 3), [139, 69, 19], dtype=np.uint8)
            
            # Create forest tile bank
            forest_tiles = {
                TileType.GRASS: grass_tile,
                TileType.STONE: stone_tile,
                TileType.WATER: water_tile,
                TileType.DIRT: dirt_tile,
            }
            
            forest_palette = {
                'grass': (34, 139, 34),
                'stone': (128, 128, 128),
                'water': (0, 100, 200),
                'dirt': (139, 69, 19)
            }
            
            self.tile_banks['forest'] = TileBank('forest', forest_tiles, forest_palette)
            
        except Exception as e:
            logger.error(f"❌ Failed to create tile banks: {e}")
    
    def render_frame(self, frame: RenderFrame) -> bool:
        """Render a complete frame"""
        try:
            self.current_frame = frame
            
            # Update performance tracking
            current_time = time.time()
            frame_time = current_time - self.last_frame_time
            self.fps_history.append(frame_time)
            if len(self.fps_history) > self.max_fps_history:
                self.fps_history.pop(0)
            self.last_frame_time = current_time
            self.frame_count += 1
            
            # Process subtitles
            self._process_subtitles(frame)
            
            # Frame rendering would happen here in a real implementation
            # For now, just track the frame
            return True
            
        except Exception as e:
            logger.error(f"❌ Frame rendering failed: {e}")
            return False
    
    def _process_subtitles(self, frame: RenderFrame):
        """Process subtitle events"""
        try:
            if RENDER_LAYERS and RenderLayer.SUBTITLES in frame.layers:
                subtitle_layer = frame.layers[RenderLayer.SUBTITLES]
                
                # Add subtitle text to frame (simplified)
                if self.subtitle_queue:
                    subtitle = self.subtitle_queue[0]
                    # Add subtitle text to the frame (simplified rendering)
                    if subtitle.text:
                        # This would render text in a real implementation
                        pass
                    
                    # Remove expired subtitles
                    if time.time() - subtitle.timestamp > self.subtitle_display_time:
                        self.subtitle_queue.pop(0)
            
        except Exception as e:
            logger.debug(f"⚠️ Subtitle processing failed: {e}")
    
    def add_subtitle(self, text: str, duration: float = 3.0):
        """Add subtitle to display queue"""
        try:
            subtitle = SubtitleEvent(text=text, duration=duration, timestamp=time.time())
            self.subtitle_queue.append(subtitle)
            
            # Limit subtitle queue size
            if len(self.subtitle_queue) > 10:
                self.subtitle_queue.pop(0)
                
        except Exception as e:
            logger.error(f"❌ Failed to add subtitle: {e}")
    
    def set_viewport_center(self, x: int, y: int):
        """Set viewport center position"""
        self.viewport.center_x = x
        self.viewport.center_y = y
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if self.fps_history:
            avg_frame_time = sum(self.fps_history) / len(self.fps_history)
            avg_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        else:
            avg_fps = 0
        
        return {
            'engine_type': 'legacy_graphics_engine',
            'frame_count': self.frame_count,
            'avg_fps': avg_fps,
            'fps_history_size': len(self.fps_history),
            'viewport_center': (self.viewport.center_x, self.viewport.center_y),
            'tile_banks': list(self.tile_banks.keys()),
            'subtitle_queue_size': len(self.subtitle_queue)
        }
    
    def cleanup(self):
        """Cleanup engine resources"""
        self.current_frame = None
        self.subtitle_queue.clear()
        self.fps_history.clear()
        logger.info("🧹 Legacy GraphicsEngine cleaned up")

# Factory class for creating engines
class GraphicsEngineFactory:
    """Factory for creating GraphicsEngine instances"""
    
    @staticmethod
    def create_default() -> GraphicsEngine:
        """Create default GraphicsEngine"""
        return GraphicsEngine()
    
    @staticmethod
    def create_with_viewport(center_x: int, center_y: int) -> GraphicsEngine:
        """Create GraphicsEngine with custom viewport"""
        engine = GraphicsEngine()
        engine.set_viewport_center(center_x, center_y)
        return engine

# Synchronization wrapper for async operations
class GraphicsEngineSync:
    """Synchronization wrapper for GraphicsEngine"""
    
    def __init__(self, engine: Optional[GraphicsEngine] = None):
        self.engine = engine or GraphicsEngine()
        self._lock = asyncio.Lock()
    
    async def render_frame_async(self, frame: RenderFrame) -> bool:
        """Async frame rendering"""
        async with self._lock:
            return self.engine.render_frame(frame)
    
    async def add_subtitle_async(self, text: str, duration: float = 3.0):
        """Async subtitle addition"""
        async with self._lock:
            self.engine.add_subtitle(text, duration)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance stats (thread-safe)"""
        return self.engine.get_performance_stats()

# Legacy compatibility exports
__all__ = [
    "GraphicsEngine", "RenderFrame", "TileBank", "Viewport", "RenderLayer",
    "GraphicsEngineFactory", "GraphicsEngineSync"
]
