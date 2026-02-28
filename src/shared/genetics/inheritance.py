import random
from typing import List, Tuple, Optional
from .genome import SlimeGenome
from .cultural_base import CulturalBase, CULTURAL_PARAMETERS

SHAPES = ["round", "cubic", "elongated", "crystalline", "amorphous"]
SIZES = ["tiny", "small", "medium", "large", "massive"]
PATTERNS = ["solid", "spotted", "striped", "marbled", "iridescent"]
ACCESSORIES = ["none", "crown", "scar", "glow", "shell", "crystals"]

def generate_random(culture: Optional[CulturalBase] = None) -> SlimeGenome:
    """Generate a SlimeGenome, optionally influenced by a CulturalBase."""
    if culture is None:
        culture = random.choice([cb for cb in CulturalBase if cb != CulturalBase.MIXED])
    
    params = CULTURAL_PARAMETERS[culture]
    
    # Helpers for ranging
    def r_range(r): return random.uniform(r[0], r[1])
    
    # Adjust primary hue to RGB
    import colorsys
    h = r_range(params.primary_hue_range) / 360.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.7, 0.9)
    base_color = (int(r * 255), int(g * 255), int(b * 255))
    
    # Map roundness to shape
    roundness = r_range(params.body_roundness_range)
    if roundness < 0.4: shape = random.choice(["cubic", "crystalline"])
    elif roundness > 0.7: shape = "round"
    else: shape = random.choice(["elongated", "amorphous"])

    return SlimeGenome(
        shape=shape,
        size=random.choice(SIZES),
        base_color=base_color,
        pattern=random.choice(PATTERNS),
        pattern_color=(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)),
        accessory=random.choice(ACCESSORIES),
        curiosity=random.random(),
        energy=random.random(),
        affection=random.random(),
        shyness=random.random(),
        cultural_base=culture
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

    # Cultural inheritance
    new_culture = CulturalBase.MIXED
    if parent_a.cultural_base == parent_b.cultural_base:
        new_culture = parent_a.cultural_base
    else:
        # 20% chance to inherit from either parent instead of mixed
        r = random.random()
        if r < 0.1: new_culture = parent_a.cultural_base
        elif r < 0.2: new_culture = parent_b.cultural_base

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
        shyness=inherit(parent_a.shyness, parent_b.shyness, True),
        cultural_base=new_culture
    )
