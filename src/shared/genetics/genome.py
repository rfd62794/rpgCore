from dataclasses import dataclass, field
from typing import Tuple

from .cultural_base import CulturalBase

@dataclass
class SlimeGenome:
    # Visual traits
    shape: str        # round, cubic, elongated, crystalline, amorphous
    size: str         # tiny, small, medium, large, massive
    base_color: Tuple[int, int, int] # RGB
    pattern: str      # solid, spotted, striped, marbled, iridescent
    pattern_color: Tuple[int, int, int] # RGB
    accessory: str    # none, crown, scar, glow, shell, crystals
    
    # Personality traits (0.0-1.0)
    curiosity: float  # moves toward new things
    energy: float     # movement speed and frequency
    affection: float  # moves toward player cursor
    shyness: float    # retreats from sudden input
    
    # Base Stats (Inherited Genetics)
    base_hp: float = 20.0
    base_atk: float = 5.0
    base_spd: float = 5.0
    generation: int = 1

    # Cultural identity
    cultural_base: CulturalBase = CulturalBase.MIXED

def calculate_race_stats(genome) -> dict:
    """Calculate racing-specific stats from genome."""
    # Convert size string to numeric value
    size_values = {
        "tiny": 0.3, "small": 0.5, "medium": 0.7, 
        "large": 0.9, "massive": 1.0
    }
    body_size = size_values.get(genome.size, 0.7)
    
    # Mass mechanics - non-linear scaling
    mass = body_size ** 1.5
    
    # Strength derived from attack stat
    strength = genome.base_atk / 100.0  # normalize 0-1
    
    # Heft power for obstacle interaction
    heft_power = mass * (1.0 + strength * 0.5)
    
    # Jump force and distance
    jump_force = 50.0 * (1.0 + strength * 0.3)
    jump_distance = (jump_force / mass) * body_size
    jump_cooldown = 0.2 + (mass * 0.4) * (1.0 - strength * 0.2)
    jump_height = (jump_force / mass) * 14  # Reduced from 18 to 14px max
    
    return {
        "mass": mass,
        "heft_power": heft_power,
        "jump_distance": jump_distance,
        "jump_cooldown": jump_cooldown,
        "jump_height": jump_height,
        "body_size": body_size,
        "strength": strength,
    }
