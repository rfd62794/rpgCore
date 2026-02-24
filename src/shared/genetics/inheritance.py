import random
from typing import List, Tuple
from .genome import SlimeGenome

SHAPES = ["round", "cubic", "elongated", "crystalline", "amorphous"]
SIZES = ["tiny", "small", "medium", "large", "massive"]
PATTERNS = ["solid", "spotted", "striped", "marbled", "iridescent"]
ACCESSORIES = ["none", "crown", "scar", "glow", "shell", "crystals"]

def generate_random() -> SlimeGenome:
    """Generate a completely random SlimeGenome."""
    return SlimeGenome(
        shape=random.choice(SHAPES),
        size=random.choice(SIZES),
        base_color=(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)),
        pattern=random.choice(PATTERNS),
        pattern_color=(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)),
        accessory=random.choice(ACCESSORIES),
        curiosity=random.random(),
        energy=random.random(),
        affection=random.random(),
        shyness=random.random()
    )

def breed(parent_a: SlimeGenome, parent_b: SlimeGenome, mutation_chance: float = 0.05) -> SlimeGenome:
    """Breed two SlimeGenomes with a chance of mutation."""
    
    def inherit(trait_a, trait_b, is_float=False):
        # 50/50 inheritance
        result = random.choice([trait_a, trait_b])
        
        # Mutation
        if random.random() < mutation_chance:
            if is_float:
                # Slight nudge for floats
                result = max(0.0, min(1.0, result + random.uniform(-0.1, 0.1)))
            else:
                # Random choice for categorical/tuples (simple mutation)
                if isinstance(result, str):
                    if result in SHAPES: result = random.choice(SHAPES)
                    elif result in SIZES: result = random.choice(SIZES)
                    elif result in PATTERNS: result = random.choice(PATTERNS)
                    elif result in ACCESSORIES: result = random.choice(ACCESSORIES)
                elif isinstance(result, tuple):
                    result = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        return result

    return SlimeGenome(
        shape=inherit(parent_a.shape, parent_b.shape),
        size=inherit(parent_a.size, parent_b.size),
        base_color=inherit(parent_a.base_color, parent_b.base_color),
        pattern=inherit(parent_a.pattern, parent_b.pattern),
        pattern_color=inherit(parent_a.pattern_color, parent_b.pattern_color),
        accessory=inherit(parent_a.accessory, parent_b.accessory),
        curiosity=inherit(parent_a.curiosity, parent_b.curiosity, True),
        energy=inherit(parent_a.energy, parent_b.energy, True),
        affection=inherit(parent_a.affection, parent_b.affection, True),
        shyness=inherit(parent_a.shyness, parent_b.shyness, True)
    )
