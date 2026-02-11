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

Lazy-loading __init__: world_engine is only imported when its
symbols are actually accessed, preventing cascading dependency
failures when importing sibling modules (e.g. apps.rpg.logic).
"""

_WORLD_EXPORTS = {
    "WorldEngine", "PermutationTable", "Chunk",
    "WorldEngineFactory", "WorldEngineSync",
}

__all__ = sorted(_WORLD_EXPORTS)


def __getattr__(name: str):
    """Lazy-load world_engine symbols on first access."""
    if name in _WORLD_EXPORTS:
        from . import world_engine as _mod
        return getattr(_mod, name)

    raise AttributeError(f"module 'apps.rpg' has no attribute {name!r}")
