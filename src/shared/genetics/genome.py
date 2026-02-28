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
