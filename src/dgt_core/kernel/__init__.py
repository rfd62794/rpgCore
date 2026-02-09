"""
DGT Core Kernel - System Components and Models

Phase 2: Component Consolidation with Sovereign Architecture
"""

from .models import (
    # Legacy models (ADR 166)
    MaterialAsset, EntityBlueprint, StoryFragment, AssetRegistry,
    # Viewport models (ADR 193)
    ViewportLayout, ViewportLayoutMode, Rectangle, Point,
    ScaleBucket, STANDARD_SCALE_BUCKETS, OverlayComponent
)
from .viewport_manager import ViewportManager, create_viewport_manager, create_overlay_manager

__all__ = [
    # Legacy models
    "MaterialAsset",
    "EntityBlueprint", 
    "StoryFragment",
    "AssetRegistry",
    "create_asset_registry",
    
    # Viewport models (ADR 193)
    "ViewportLayout",
    "ViewportLayoutMode",
    "Rectangle",
    "Point",
    "ScaleBucket",
    "STANDARD_SCALE_BUCKETS",
    "OverlayComponent",
    
    # Viewport management
    "ViewportManager",
    "create_viewport_manager",
    "create_overlay_manager"
]
