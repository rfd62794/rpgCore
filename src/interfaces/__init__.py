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
)

import sys
from pathlib import Path

# Add src to path for absolute imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from abc.base import (
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
    
    # Abstract Base Classes
    "BaseEngine",
    "BaseRenderer",
    "BaseStateManager",
]
