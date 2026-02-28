"""Procedural race track generation for slimes.
Adapted from TurboShells.
"""

import random
from enum import Enum

TRACK_LENGTH_LOGIC = 1500
SEGMENT_LENGTH = 10

class TerrainType(Enum):
    GRASS = "grass"        # normal speed
    WATER = "water"        # slow, Coastal advantage
    ROCK = "rock"          # rough, Ember advantage  
    MUD = "mud"           # slow, Moss advantage
    HURDLE = "hurdle"      # jump required (future)
    PUSHBLOCK = "push_block"  # interactive (future)
    VOID = "void"          # shortcut/hazard (future)

# Speed modifiers per terrain
TERRAIN_SPEED_MOD = {
    TerrainType.GRASS: 1.0,
    TerrainType.WATER: 0.65,
    TerrainType.ROCK: 0.75,
    TerrainType.MUD: 0.55,
    TerrainType.HURDLE: 1.0,  # No speed penalty, jump required
    TerrainType.PUSHBLOCK: 1.0,  # No speed penalty, interactive
    TerrainType.VOID: 1.0,  # No speed penalty, hazard
}

# Cultural advantage — double the modifier benefit
CULTURAL_TERRAIN_BONUS = {
    "coastal": TerrainType.WATER,
    "ember": TerrainType.ROCK,
    "moss": TerrainType.MUD,
    "crystal": None,  # no terrain advantage
    "void": None,  # random advantage each race
    "mixed": None,  # no terrain advantage
}

def generate_track(length: int = TRACK_LENGTH_LOGIC):
    """Generate a simple terrain track as a list of terrain types.
    Probabilities: 50% Grass, 20% Water, 20% Rock, 10% Mud.
    """
    segment_count = int(length / SEGMENT_LENGTH) + 10
    track = []
    for _ in range(segment_count):
        r = random.random()
        if r < 0.5:
            track.append("grass")
        elif r < 0.7:
            track.append("water")
        elif r < 0.9:
            track.append("rock")
        else:
            track.append("mud")
    return track

def get_terrain_at(track: list[str], distance: float) -> str:
    """Return terrain type for a given logical race distance."""
    if not track:
        return "grass"
    idx = int(distance / SEGMENT_LENGTH)
    idx = max(0, min(idx, len(track) - 1))
    return track[idx]

def get_terrain_speed_modifier(terrain: str, cultural_base: str = None) -> float:
    """Get speed modifier for terrain, applying cultural advantage if applicable."""
    terrain_type = TerrainType(terrain)
    base_mod = TERRAIN_SPEED_MOD.get(terrain_type, 1.0)
    
    # Apply cultural advantage
    if cultural_base and cultural_base in CULTURAL_TERRAIN_BONUS:
        bonus_terrain = CULTURAL_TERRAIN_BONUS[cultural_base]
        if bonus_terrain == terrain_type:
            # Double the benefit (less penalty = faster)
            if base_mod < 1.0:
                return min(1.0, base_mod + (1.0 - base_mod) * 0.5)
    
    return base_mod
