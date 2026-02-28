# Agent Memory

## Racing Stat System - Mass, Strength, and Heft Mechanics

### Core Concept
Slime racing uses **mass** and **strength** as derived stats that create meaningful gameplay variety. Different body sizes and strength combinations create distinct racing styles and terrain specializations.

### Mass Mechanics
**Formula**: `mass = body_size ** 1.5`

- **Non-linear scaling** - Big slimes are disproportionately heavy
- **body_size 0.3** → **mass 0.16** (light, agile)
- **body_size 0.6** → **mass 0.46** (medium, balanced)  
- **body_size 1.0** → **mass 1.0** (heavy, powerful)

### Jump Physics
**Formula**: `jump_distance = (jump_force / mass) * body_size`

- **Heavy slimes** - Slow bounds, more ground coverage per jump
- **Light slimes** - Rapid hops, less distance per jump
- **Jump frequency**: `jump_cooldown = 0.2 + (mass * 0.4)`
- **Light slimes**: 0.2s cooldown - rapid hopping
- **Heavy slimes**: 0.6s cooldown - slow bounding

### Strength and Heft
**Formula**: `heft_power = mass * (1.0 + strength * 0.5)`

- **Strength** derived from `genome.attack_base / 100.0`
- **High strength** - Punch above weight class, move obstacles
- **Low strength** - Gets pushed back, struggles with blocks

### Terrain Interaction Matrix

| Terrain Type | Small Slime | Large Slime | Notes |
|-------------|-------------|-------------|-------|
| **Flat grass** | ✓ Fast hops, frequent | ~ Slow bounds, infrequent | Recovery vs distance trade-off |
| **Water pond** | ~ Partial sink, speed penalty | ✗ Sinks deep, heavy penalty | Mass affects sink depth |
| **Rock field** | ✗ Bounced, no grip | ✓ Crashes through, momentum | Mass carries through obstacles |
| **Mud patch** | ✓ Light skip, barely sinks | ✗ Gets stuck, sinks fully | Mass determines sink resistance |
| **Push block** | ✗ Bounces back (unless high strength) | ✓ Moves block, mass carries | Heft power > resistance = success |
| **Hurdle** | ✓ Easy clear, natural arc | ~ Must time jump, low arc | Mass affects jump height |

### Racing Specializations

**Small High Strength Slime** (All-rounder):
- Rapid hops + heft power
- Clears hurdles easily
- Can move blocks when needed
- Good on most terrain

**Large High Strength Slime** (Specialist):
- Powerful bounds + unstoppable force
- Demolishes rock fields
- Excellent on push blocks
- Terrible in mud/water
- Build track to suit

**Large Low Strength Slime** (Weak):
- Heavy but ineffective
- Gets stuck everywhere
- Loses badly unless terrain matches
- Poor racing performance

### Breeding Implications
Different selection pressures than dungeon:
- **Racing**: Small body + high speed + medium strength
- **Dungeon**: Large body + high attack + high defense
- Same genetic system, different optimization goals
- Creates purpose for specialized breeding programs

### Implementation Plan
Add to `src/shared/genetics/genome.py`:
```python
def calculate_race_stats(genome) -> dict:
    mass = genome.body_size ** 1.5
    strength = genome.attack_base / 100.0
    heft_power = mass * (1.0 + strength * 0.5)
    
    jump_force = 50.0 * (1.0 + strength * 0.3)
    jump_distance = (jump_force / mass) * genome.body_size
    jump_cooldown = 0.2 + (mass * 0.4) * (1.0 - strength * 0.2)
    jump_height = (jump_force / mass) * 18
    
    return {
        "mass": mass,
        "heft_power": heft_power,
        "jump_distance": jump_distance,
        "jump_cooldown": jump_cooldown,
        "jump_height": jump_height,
    }
```

This system creates meaningful team selection decisions based on track composition and creates depth in both racing and breeding mechanics.

---

## Scene Standardization — Planned Next Infrastructure Session

Current state:
  534 passing, 0 failures, 0 errors
  All scenes satisfy abstract contract via stubs
  
Problem remaining:
  Stubs are scattered across legacy scenes
  BaseScene does not exist yet
  Boilerplate duplicated in every scene
  
Planned:
  BaseScene — extract shared boilerplate
  BaseComponent — UI component contract
  SceneManager stack — clean navigation
  
When to build:
  After Racing track feels right
  After Dungeon auto-battle prototype
  One dedicated session
  
Payoff:
  Adding abstract method to BaseScene
  with default impl = 0 cascade errors
  New scenes = 20 lines not 80
  Navigation = manager.push/pop only
