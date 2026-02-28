from src.shared.genetics.genome import SlimeGenome

def calculate_hp(genome: SlimeGenome) -> int:
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
    return base + size_bonus + shape_bonus

def calculate_attack(genome: SlimeGenome) -> int:
    """Energy driving aggression."""
    base = 5
    energy_bonus = int(genome.energy * 10)
    return base + energy_bonus

def calculate_speed(genome: SlimeGenome) -> int:
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
    
    return max(1, base - size_penalty + energy_bonus)
