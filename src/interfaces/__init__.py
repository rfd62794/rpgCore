"""
DGT Platform - Interface Definitions

This package contains all Protocol definitions and abstract base classes
that enforce the Three-Tier Architecture and enable dependency injection.

All components must implement the appropriate Protocol before
any concrete implementation can be added.

Phase 1 Priority: Interface Definition & Hardening
"""

from .protocols import (
    EngineProtocol,
    RenderProtocol,
    StateProtocol,
    DIProtocol,
    PPUProtocol,
    PhysicsProtocol,
    SpaceEntityProtocol,
    ScrapProtocol,
    TerminalHandshakeProtocol,
)

from ..dgt_core.foundation.base import (
    BaseEngine,
    BaseRenderer,
    BaseStateManager,
)

__all__ = [
    # Protocol Definitions
    "EngineProtocol",
    "RenderProtocol", 
    "StateProtocol",
    "DIProtocol",
    "PPUProtocol",
    "PhysicsProtocol",
    "SpaceEntityProtocol",
    "ScrapProtocol",
    "TerminalHandshakeProtocol",
    
    # Abstract Base Classes
    "BaseEngine",
    "BaseRenderer",
    "BaseStateManager",
]
