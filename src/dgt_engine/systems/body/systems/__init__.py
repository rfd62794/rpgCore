"""
Game Systems - Tier 2 Engine Components (DEPRECATED - Use game_engine.systems.body)

Reusable systems for entity management, spawning, and collision detection.

BACKWARD COMPATIBILITY SHIM: This module has been migrated to src/game_engine/systems/body/
Old imports continue to work via this shim layer.
"""

# Backward compatibility: redirect to new location
from game_engine.systems.body import (
    EntityManager,
    Entity,
    EntityComponent,
    ObjectPool,
    SpaceEntity,
    RPGEntity,
    TycoonEntity,
)

__all__ = [
    'EntityManager',
    'Entity',
    'EntityComponent',
    'ObjectPool',
    'SpaceEntity',
    'RPGEntity',
    'TycoonEntity',
]
