from src.shared.genetics.genome import SlimeGenome
from src.shared.genetics.cultural_base import CULTURAL_PARAMETERS

def calculate_hp(genome: SlimeGenome, level: int = 1) -> int:
    """Body size = tankiness. High roundness = more HP."""
    base = 20
    
    size_map = {
        "tiny": 0,
        "small": 5,
        "medium": 15,
        "large": 30,
        "massive": 50
    }
    size_bonus = size_map.get(genome.size, 15)
    
    # Shape bonus
    shape_bonus = 10 if genome.shape == "round" else 0
    raw_hp = base + size_bonus + shape_bonus
    
    # Cultural & Level Modifiers
    cultural_mod = CULTURAL_PARAMETERS[genome.cultural_base].hp_modifier
    level_mod = 1.0 + (level - 1) * 0.1
    
    return int(raw_hp * cultural_mod * level_mod)

def calculate_attack(genome: SlimeGenome, level: int = 1) -> int:
    """Energy driving aggression."""
    base = 5
    energy_bonus = int(genome.energy * 10)
    raw_attack = base + energy_bonus
    
    # Cultural & Level Modifiers
    cultural_mod = CULTURAL_PARAMETERS[genome.cultural_base].attack_modifier
    level_mod = 1.0 + (level - 1) * 0.1
    
    return int(raw_attack * cultural_mod * level_mod)

def calculate_speed(genome: SlimeGenome, level: int = 1) -> int:
    """Small body = faster. High energy = faster."""
    base = 5
    
    size_penalty_map = {
        "tiny": 0,
        "small": 1,
        "medium": 3,
        "large": 5,
        "massive": 8
    }
    size_penalty = size_penalty_map.get(genome.size, 3)
    
    energy_bonus = int(genome.energy * 5)
    raw_speed = max(1, base - size_penalty + energy_bonus)
    
    # Cultural & Level Modifiers
    cultural_mod = CULTURAL_PARAMETERS[genome.cultural_base].speed_modifier
    # Speed grows slower with level than HP/ATK
    level_mod = 1.0 + (level - 1) * 0.05
    
    return int(raw_speed * cultural_mod * level_mod)
