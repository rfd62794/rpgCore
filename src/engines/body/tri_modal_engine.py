"""
Tri-Modal Engine - Unified Body Engine with Legacy Compatibility
Integrates the Tri-Modal Display Suite with the existing DGT architecture
"""

import time
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import sys

# Add parent directories for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from loguru import logger

# Import tri-modal components
try:
    from src.body.dispatcher import DisplayDispatcher, DisplayMode, RenderPacket
    from src.body.terminal import create_terminal_body
    from src.body.cockpit import create_cockpit_body
    from src.body.ppu import create_ppu_body
    TRI_MODAL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Tri-Modal Display Suite not available: {e}")
    TRI_MODAL_AVAILABLE = False
    # Define fallback types to prevent NameError
    DisplayDispatcher = None
    DisplayMode = None
    RenderPacket = None
    create_terminal_body = None
    create_cockpit_body = None
    create_ppu_body = None

# Import legacy graphics engine
from .graphics_engine import GraphicsEngine, RenderFrame, TileBank, Viewport

@dataclass
class EngineConfig:
    """Configuration for Tri-Modal Engine"""
    default_mode: Optional[DisplayMode] = None
    enable_legacy: bool = True
    auto_register_bodies: bool = True
    performance_tracking: bool = True
    
    def __post_init__(self):
        # Set default mode if not specified
        if self.default_mode is None and TRI_MODAL_AVAILABLE:
            self.default_mode = DisplayMode.TERMINAL

class TriModalEngine:
    """
    Unified Body Engine combining Tri-Modal Display Suite with legacy GraphicsEngine
    
    This engine provides:
    - Backward compatibility with existing GraphicsEngine API
    - Modern tri-modal display capabilities
    - Seamless migration path for legacy code
    - Performance optimization and resource management
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.legacy_engine: Optional[GraphicsEngine] = None
        self.dispatcher: Optional[DisplayDispatcher] = None
        self.is_initialized = False
        self.performance_stats: Dict[str, Any] = {}
        
        # Initialize based on configuration
        if self.config.enable_legacy:
            self._init_legacy_engine()
        
        if TRI_MODAL_AVAILABLE:
            self._init_tri_modal_dispatcher()
        
        logger.info(f"🎭 Tri-Modal Engine initialized (Legacy: {self.config.enable_legacy}, Tri-Modal: {TRI_MODAL_AVAILABLE})")
    
    def _init_legacy_engine(self):
        """Initialize legacy GraphicsEngine for backward compatibility"""
        try:
            self.legacy_engine = GraphicsEngine()
            logger.info("📊 Legacy GraphicsEngine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize legacy engine: {e}")
            self.legacy_engine = None
    
    def _init_tri_modal_dispatcher(self):
        """Initialize tri-modal display dispatcher"""
        if not TRI_MODAL_AVAILABLE or not DisplayMode:
            return
        
        try:
            self.dispatcher = DisplayDispatcher(default_mode=self.config.default_mode)
            
            if self.config.auto_register_bodies:
                # Register display bodies
                terminal_body = create_terminal_body()
                if terminal_body:
                    self.dispatcher.register_body(DisplayMode.TERMINAL, terminal_body)
                
                cockpit_body = create_cockpit_body()
                if cockpit_body:
                    self.dispatcher.register_body(DisplayMode.COCKPIT, cockpit_body)
                
                ppu_body = create_ppu_body()
                if ppu_body:
                    self.dispatcher.register_body(DisplayMode.PPU, ppu_body)
            
            logger.info("🎭 Tri-Modal Display Dispatcher initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize tri-modal dispatcher: {e}")
            self.dispatcher = None
    
    def render(self, game_state: Dict[str, Any], mode: Optional[DisplayMode] = None) -> bool:
        """
        Render game state using appropriate engine
        
        Args:
            game_state: Game state data
            mode: Target display mode (uses default if None)
        
        Returns:
            True if rendering successful
        """
        if not self.is_initialized:
            self.is_initialized = True
        
        # Use tri-modal dispatcher if available
        if self.dispatcher:
            return self._render_tri_modal(game_state, mode)
        
        # Fallback to legacy engine
        elif self.legacy_engine:
            return self._render_legacy(game_state)
        
        logger.error("❌ No rendering engine available")
        return False
    
    def _render_tri_modal(self, game_state: Dict[str, Any], mode: Optional[DisplayMode] = None) -> bool:
        """Render using tri-modal display dispatcher"""
        try:
            target_mode = mode or self.config.default_mode
            
            # Convert game state to render packet
            packet = self._game_state_to_packet(game_state, target_mode)
            
            # Render packet
            return self.dispatcher.render(packet)
            
        except Exception as e:
            logger.error(f"❌ Tri-modal rendering failed: {e}")
            return False
    
    def _render_legacy(self, game_state: Dict[str, Any]) -> bool:
        """Render using legacy GraphicsEngine"""
        try:
            # Convert game state to legacy format
            if hasattr(self.legacy_engine, 'render_frame'):
                # Create render frame from game state
                frame = self._game_state_to_frame(game_state)
                return self.legacy_engine.render_frame(frame)
            else:
                logger.warning("⚠️ Legacy engine doesn't have render_frame method")
                return False
                
        except Exception as e:
            logger.error(f"❌ Legacy rendering failed: {e}")
            return False
    
    def _game_state_to_packet(self, game_state: Dict[str, Any], mode: DisplayMode) -> RenderPacket:
        """Convert game state to tri-modal render packet"""
        # Extract entities from game state
        layers = []
        
        if 'entities' in game_state:
            for i, entity in enumerate(game_state['entities']):
                layer = {
                    'depth': entity.get('depth', i),
                    'type': entity.get('type', 'dynamic'),
                    'id': entity.get('id', f'entity_{i}'),
                    'x': entity.get('x'),
                    'y': entity.get('y'),
                    'effect': entity.get('effect'),
                    'metadata': entity
                }
                layers.append(layer)
        
        # Add background layer
        if 'background' in game_state:
            bg = game_state['background']
            layers.insert(0, {
                'depth': -1,
                'type': 'baked',
                'id': bg.get('id', 'background'),
                'x': 0, 'y': 0,
                'metadata': bg
            })
        
        # Extract HUD data
        hud_data = game_state.get('hud', {})
        
        return RenderPacket(
            mode=mode,
            layers=layers,
            hud=hud_data,
            metadata=game_state
        )
    
    def _game_state_to_frame(self, game_state: Dict[str, Any]) -> RenderFrame:
        """Convert game state to legacy RenderFrame"""
        # This is a simplified conversion - in practice would need more sophisticated mapping
        width = game_state.get('width', 160)
        height = game_state.get('height', 144)
        
        # Create basic frame (would need proper layer composition in real implementation)
        frame = RenderFrame(width=width, height=height, layers={})
        
        return frame
    
    def set_mode(self, mode: DisplayMode) -> bool:
        """Switch display mode"""
        if self.dispatcher:
            return self.dispatcher.set_mode(mode)
        else:
            logger.warning("⚠️ Tri-modal dispatcher not available")
            return False
    
    def get_mode(self) -> Optional[DisplayMode]:
        """Get current display mode"""
        if self.dispatcher:
            return self.dispatcher.current_mode
        return None
    
    def update_performance_stats(self) -> Dict[str, Any]:
        """Update and return performance statistics"""
        stats = {
            'engine_type': 'tri-modal' if self.dispatcher else 'legacy',
            'tri_modal_available': TRI_MODAL_AVAILABLE,
            'legacy_available': self.legacy_engine is not None,
            'current_mode': self.dispatcher.current_mode.value if self.dispatcher else None,
            'timestamp': time.time()
        }
        
        # Get dispatcher stats
        if self.dispatcher:
            dispatcher_stats = self.dispatcher.get_performance_stats()
            stats['dispatcher'] = dispatcher_stats
        
        # Get legacy engine stats
        if self.legacy_engine:
            try:
                legacy_stats = getattr(self.legacy_engine, 'get_performance_stats', lambda: {})()
                stats['legacy'] = legacy_stats
            except:
                stats['legacy'] = {}
        
        self.performance_stats = stats
        return stats
    
    def cleanup(self):
        """Cleanup engine resources"""
        if self.dispatcher:
            self.dispatcher.cleanup()
        
        if self.legacy_engine:
            try:
                if hasattr(self.legacy_engine, 'cleanup'):
                    self.legacy_engine.cleanup()
            except:
                pass
        
        logger.info("🧹 Tri-Modal Engine cleaned up")

# Factory functions for easy migration
def create_tri_modal_engine(config: Optional[EngineConfig] = None) -> TriModalEngine:
    """Create Tri-Modal Engine with default configuration"""
    return TriModalEngine(config)

def create_legacy_engine() -> GraphicsEngine:
    """Create legacy GraphicsEngine for backward compatibility"""
    return GraphicsEngine()

# Compatibility layer for existing code
class BodyEngine(TriModalEngine):
    """Backward-compatible BodyEngine class"""
    
    def __init__(self, use_tri_modal: bool = True):
        config = EngineConfig(
            enable_legacy=True,
            auto_register_bodies=use_tri_modal
        )
        super().__init__(config)

# Export main components
__all__ = [
    'TriModalEngine', 'BodyEngine', 'EngineConfig',
    'create_tri_modal_engine', 'create_legacy_engine',
    'TRI_MODAL_AVAILABLE'
]
