"""
DGT Body - Tri-Modal Display Suite
Unified Display Interface (UDI) for Terminal, Cockpit, and PPU rendering
ADR 120: Tri-Modal Rendering Bridge
ADR 122: Universal Packet Enforcement
"""

from typing import Optional

# Tri-Modal Display Suite
from .dispatcher import DisplayDispatcher, DisplayMode, RenderPacket
from .ppu import PPUBody, create_ppu_body
from .terminal import TerminalBody, create_terminal_body
from .cockpit import CockpitBody, create_cockpit_body

# Unified Engine with Legacy Adapter
from .tri_modal_engine import TriModalEngine, BodyEngine, EngineConfig
from .legacy_adapter import LegacyGraphicsEngineAdapter, create_legacy_engine

# Factory functions
def create_tri_modal_engine(config: Optional[EngineConfig] = None) -> TriModalEngine:
    """Create Tri-Modal Engine with default configuration"""
    return TriModalEngine(config)

# Legacy Graphics Engine (frozen artifact)
from .graphics_engine import GraphicsEngine, RenderFrame, TileBank, Viewport, RenderLayer, GraphicsEngineFactory, GraphicsEngineSync

# Availability flag
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from body.dispatcher import TRI_MODAL_AVAILABLE as _TRI_MODAL_AVAILABLE
except ImportError:
    _TRI_MODAL_AVAILABLE = False

TRI_MODAL_AVAILABLE = _TRI_MODAL_AVAILABLE

__all__ = [
    # Unified Engine
    'TriModalEngine', 'BodyEngine', 'EngineConfig',
    
    # Display Bodies
    'DisplayDispatcher', 'DisplayMode', 'RenderPacket',
    'PPUBody', 'TerminalBody', 'CockpitBody',
    
    # Factory Functions
    'create_ppu_body', 'create_terminal_body', 'create_cockpit_body',
    'create_legacy_engine',
    
    # Legacy Adapter
    'LegacyGraphicsEngineAdapter',
    
    # Legacy Graphics Engine (frozen artifact)
    'GraphicsEngine', 'RenderFrame', 'TileBank', 'Viewport', 'RenderLayer', 'GraphicsEngineFactory', 'GraphicsEngineSync',
    
    # Status
    'TRI_MODAL_AVAILABLE'
]
