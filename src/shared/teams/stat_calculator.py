from src.shared.genetics.genome import SlimeGenome
from src.shared.genetics.cultural_base import CULTURAL_PARAMETERS

def calculate_hp(genome: SlimeGenome, level: int = 1) -> int:
    """HP = base_hp * cultural_mod * level_mod."""
    # Cultural & Level Modifiers
    cultural_mod = CULTURAL_PARAMETERS[genome.cultural_base].hp_modifier
    level_mod = 1.0 + (level - 1) * 0.1
    
    return int(genome.base_hp * cultural_mod * level_mod)

def calculate_attack(genome: SlimeGenome, level: int = 1) -> int:
    """Attack = base_atk * cultural_mod * level_mod."""
    # Cultural & Level Modifiers
    cultural_mod = CULTURAL_PARAMETERS[genome.cultural_base].attack_modifier
    level_mod = 1.0 + (level - 1) * 0.1
    
    return int(genome.base_atk * cultural_mod * level_mod)

def calculate_speed(genome: SlimeGenome, level: int = 1) -> int:
    """Speed = base_spd * cultural_mod * level_mod."""
    # Cultural & Level Modifiers
    cultural_mod = CULTURAL_PARAMETERS[genome.cultural_base].speed_modifier
    # Speed grows slower with level than HP/ATK
    level_mod = 1.0 + (level - 1) * 0.05
    
    return int(genome.base_spd * cultural_mod * level_mod)
