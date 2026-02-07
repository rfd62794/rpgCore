"""
World Engine Module - The World Pillar

Deterministic world generation with the Chaos-Seed Protocol.
The World Engine provides the mathematical foundation for the game world
while the LLM Chronicler provides the narrative interpretation.

Key Features:
- PermutationTable-based noise generation
- Deterministic Interest Point generation
- Chunk-based world loading
- Background pre-generation
- Facade pattern interface
"""

from .world_engine import (
    WorldEngine, PermutationTable, Chunk,
    WorldEngineFactory, WorldEngineSync
)

__all__ = [
    "WorldEngine", "PermutationTable", "Chunk",
    "WorldEngineFactory", "WorldEngineSync"
]
