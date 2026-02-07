"""
D&D Engine - The Mind Pillar

Deterministic D20 logic, state mutation, and rule enforcement.
Single Source of Truth for all game state.
"""

from .dd_engine import DD_Engine, GameState, MovementIntent, InteractionIntent, ValidationResult

__all__ = [
    'DD_Engine',
    'GameState', 
    'MovementIntent',
    'InteractionIntent',
    'ValidationResult'
]
