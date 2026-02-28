"""Procedural race track generation for slimes.
Adapted from TurboShells.
"""

import random

TRACK_LENGTH_LOGIC = 1500
SEGMENT_LENGTH = 10

def generate_track(length: int = TRACK_LENGTH_LOGIC):
    """Generate a simple terrain track as a list of terrain types.
    Probabilities: 60% Grass, 20% Water, 20% Rock.
    """
    segment_count = int(length / SEGMENT_LENGTH) + 10
    track = []
    for _ in range(segment_count):
        r = random.random()
        if r < 0.6:
            track.append("grass")
        elif r < 0.8:
            track.append("water")
        else:
            track.append("rock")
    return track

def get_terrain_at(track: list[str], distance: float) -> str:
    """Return terrain type for a given logical race distance."""
    if not track:
        return "grass"
    idx = int(distance / SEGMENT_LENGTH)
    idx = max(0, min(idx, len(track) - 1))
    return track[idx]
