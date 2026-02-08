"""
Core Foundation - GameState, Intent Dataclasses, and System Constants
LEGACY SHIM - Delegates to src.dgt_core.kernel.state

The immutable foundation of the DGT Autonomous Movie System.
All data structures and constants that define the system's behavior.
"""

from src.dgt_core.kernel.state import *

# Ensure common types are available directly
from src.dgt_core.kernel.state import (
    GameState, TileType, BiomeType, InterestType, VoyagerState, 
    IntentType, ValidationResult
)
