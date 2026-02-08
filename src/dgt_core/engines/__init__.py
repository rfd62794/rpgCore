"""
DGT Core Engines Package
Unified display and simulation engines
"""

from .body import (
    TriModalEngine, BodyEngine, EngineConfig,
    DisplayDispatcher, DisplayMode, RenderPacket,
    TerminalBody, CockpitBody, PPUBody,
    create_tri_modal_engine, create_legacy_engine,
    GraphicsEngine, RenderFrame, TileBank, Viewport, RenderLayer,
    TRI_MODAL_AVAILABLE
)

from .space import space_voyager_engine, space_physics, ship_genetics
from .shells import shell_engine, shell_wright

__all__ = [
    # Body engines (display)
    "TriModalEngine", "BodyEngine", "EngineConfig",
    "DisplayDispatcher", "DisplayMode", "RenderPacket",
    "TerminalBody", "CockpitBody", "PPUBody",
    "create_tri_modal_engine", "create_legacy_engine",
    "GraphicsEngine", "RenderFrame", "TileBank", "Viewport", "RenderLayer",
    "TRI_MODAL_AVAILABLE",
    
    # Space engines (Star-Fleet)
    "space_voyager_engine", "space_physics", "ship_genetics",
    
    # Shell engines (TurboShells)
    "shell_engine", "shell_wright"
]
