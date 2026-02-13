"""
Interface Renderers - ADR 193 Sidecar Components

Phase 2: Component Consolidation with Sovereign Viewport Protocol

This package contains the sidecar components that render in the left and right
wings of the sovereign viewport. These components are designed to work
with the ViewportManager's responsive layout system.

Components:
- PhosphorTerminal: Narrative "Story Drips" and logs (Left Wing)
- GlassCockpit: Resource management and ship health (Right Wing)
"""

from .phosphor_terminal import PhosphorTerminal
from .glass_cockpit import GlassCockpit

__all__ = [
    "PhosphorTerminal",
    "GlassCockpit"
]
