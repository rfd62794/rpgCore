"""
StatBlock - Computed stats layer between raw genome values and gameplay.

Provides culture modifiers, equipment bonuses, and stage scaling.
Scenes and systems should read from StatBlock, not raw genome fields.
"""

from dataclasses import dataclass
from typing import Dict

from src.shared.genetics.genome import SlimeGenome


@dataclass
class StatBlock:
    """
    Computed stats layer between raw genome values and final values used in gameplay.
    Scenes and systems read from StatBlock, never from raw genome fields directly.
    """

    # Base values (from genome)
    base_hp: float
    base_atk: float
    base_spd: float

    # Modifier layers (additive floats)
    culture_hp: float = 0.0
    culture_atk: float = 0.0
    culture_spd: float = 0.0

    equipment_hp: float = 0.0
    equipment_atk: float = 0.0
    equipment_spd: float = 0.0

    stage_modifier: float = 1.0

    # Computed finals (read-only properties)
    @property
    def hp(self) -> int:
        return max(1, int(
            (self.base_hp
             + self.culture_hp
             + self.equipment_hp)
            * self.stage_modifier))

    @property
    def atk(self) -> int:
        return max(1, int(
            (self.base_atk
             + self.culture_atk
             + self.equipment_atk)
            * self.stage_modifier))

    @property
    def spd(self) -> int:
        return max(1, int(
            (self.base_spd
             + self.culture_spd
             + self.equipment_spd)
            * self.stage_modifier))

    @classmethod
    def from_genome(cls, genome: SlimeGenome) -> 'StatBlock':
        """
        Build StatBlock from genome alone.
        Equipment modifiers default to 0.
        Culture modifiers derived from culture_expression weights.
        Stage modifier from lifecycle stage.
        """

        # Culture modifier constants
        # Per unit of culture expression weight
        CULTURE_WEIGHTS = {
            'ember':   {'atk': 3.0, 'hp': 0.5,  'spd': 0.5},
            'gale':    {'atk': 0.5, 'hp': 0.5,  'spd': 3.0},
            'marsh':   {'atk': 0.5, 'hp': 3.0,  'spd': 0.5},
            'crystal': {'atk': 1.0, 'hp': 1.0,  'spd': 1.0},
            'tundra':  {'atk': 0.5, 'hp': 2.0,  'spd': -1.0},
            'tide':    {'atk': 2.0, 'hp': 0.5,  'spd': 2.0},
        }

        # Compute culture modifiers
        culture_hp = 0.0
        culture_atk = 0.0
        culture_spd = 0.0

        expr = genome.culture_expression or {}
        for culture, weight in expr.items():
            weights = CULTURE_WEIGHTS.get(culture, {})
            culture_hp  += weight * weights.get('hp',  0.0)
            culture_atk += weight * weights.get('atk', 0.0)
            culture_spd += weight * weights.get('spd', 0.0)

        # Stage modifier from genome.level
        stage_mod = cls._stage_modifier(genome.level)

        return cls(
            base_hp=genome.base_hp,
            base_atk=genome.base_atk,
            base_spd=genome.base_spd,
            culture_hp=culture_hp,
            culture_atk=culture_atk,
            culture_spd=culture_spd,
            stage_modifier=stage_mod,
        )

    @staticmethod
    def _stage_modifier(level: int) -> float:
        """Calculate stage modifier based on slime level"""
        if level <= 1:   return 0.6  # Hatchling
        elif level <= 3: return 0.8  # Juvenile
        elif level <= 5: return 1.0  # Young
        elif level <= 7: return 1.2  # Prime
        elif level <= 9: return 1.1  # Veteran
        else:            return 1.0  # Elder (10+)

    def with_equipment(self,
                       hp: float = 0.0,
                       atk: float = 0.0,
                       spd: float = 0.0
                       ) -> 'StatBlock':
        """
        Return new StatBlock with equipment modifiers applied.
        Does not mutate original.
        """
        from dataclasses import replace
        return replace(self,
            equipment_hp=hp,
            equipment_atk=atk,
            equipment_spd=spd)

    def to_dict(self) -> dict:
        """Serialize for debugging/display."""
        return {
            'hp':  self.hp,
            'atk': self.atk,
            'spd': self.spd,
            'base_hp':  self.base_hp,
            'base_atk': self.base_atk,
            'base_spd': self.base_spd,
            'culture_hp':  self.culture_hp,
            'culture_atk': self.culture_atk,
            'culture_spd': self.culture_spd,
            'stage_modifier': self.stage_modifier,
        }
