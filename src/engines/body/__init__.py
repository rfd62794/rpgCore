"""
Body Engine Module - The Body Pillar (Tri-Modal Display Suite)

ADR 120: Tri-Modal Rendering Bridge - Universal Display Interface
The Body Engine transforms the Mind's state into visual representation through three lenses:
- Terminal: High-speed, low-overhead console monitoring
- Cockpit: Modular dashboards for IT Management and complex Sim stats  
- PPU: 60Hz dithered Game Boy-style rendering for visual immersion

Key Features:
- Stateless render engine with Universal Packet format
- Tri-modal display dispatcher with automatic mode switching
- SOLID architecture with pluggable display bodies
- Performance-optimized rendering (10Hz/30Hz/60Hz per mode)
- Rust-powered sprite analysis and dithering engine
"""

# Legacy Graphics Engine (maintained for backward compatibility)
from .graphics_engine import (
    GraphicsEngine, RenderFrame, TileBank, Viewport, RenderLayer,
    GraphicsEngineFactory, GraphicsEngineSync
)

# Tri-Modal Display Suite
try:
    # Try absolute imports first
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    from body.dispatcher import DisplayDispatcher, DisplayMode, RenderPacket
    from body.terminal import TerminalBody, create_terminal_body
    from body.cockpit import CockpitBody, create_cockpit_body
    from body.ppu import PPUBody, create_ppu_body
    
    TRI_MODAL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Tri-Modal Display Suite import failed: {e}")
    TRI_MODAL_AVAILABLE = False
    DisplayDispatcher = None
    DisplayMode = None
    RenderPacket = None
    TerminalBody = None
    CockpitBody = None
    PPUBody = None
    create_terminal_body = None
    create_cockpit_body = None
    create_ppu_body = None

# Unified Tri-Modal Engine
from .tri_modal_engine import (
    TriModalEngine, BodyEngine, EngineConfig,
    create_tri_modal_engine, create_legacy_engine
)

__all__ = [
    # Legacy Graphics Engine
    "GraphicsEngine", "RenderFrame", "TileBank", "Viewport", "RenderLayer",
    "GraphicsEngineFactory", "GraphicsEngineSync",
    
    # Tri-Modal Display Suite (if available)
    "DisplayDispatcher", "DisplayMode", "RenderPacket",
    "TerminalBody", "CockpitBody", "PPUBody",
    "create_terminal_body", "create_cockpit_body", "create_ppu_body",
    
    # Unified Engine
    "TriModalEngine", "BodyEngine", "EngineConfig",
    "create_tri_modal_engine", "create_legacy_engine",
    
    # Availability flags
    "TRI_MODAL_AVAILABLE"
]
