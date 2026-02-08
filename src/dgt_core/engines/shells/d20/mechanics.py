"""
D20 Mechanics Core - Dice, DCs, and Death Saves
ADR 173: D20 Mechanical Core for Permadeath System
"""

import random
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from loguru import logger


class DiceType(int, Enum):
    """Standard D&D dice types"""
    D4 = 4
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12
    D20 = 20
    D100 = 100


class SaveType(str, Enum):
    """Types of saving throws"""
    FORTITUDE = "fortitude"
    REFLEX = "reflex"
    WILL = "will"
    DEATH = "death"


class SkillCheckType(str, Enum):
    """Types of skill checks"""
    ATHLETICS = "athletics"
    ACROBATICS = "acrobatics"
    STEALTH = "stealth"
    ARCANA = "arcana"
    HISTORY = "history"
    INVESTIGATION = "investigation"
    NATURE = "nature"
    RELIGION = "religion"
    ANIMAL_HANDLING = "animal_handling"
    INSIGHT = "insight"
    MEDICINE = "medicine"
    PERCEPTION = "perception"
    SURVIVAL = "survival"
    DECEPTION = "deception"
    INTIMIDATION = "intimidation"
    PERFORMANCE = "performance"
    PERSUASION = "persuasion"


@dataclass
class DiceRoll:
    """Result of a dice roll"""
    dice_type: DiceType
    rolls: List[int]
    total: int
    modifier: int
    natural_20: bool = False
    natural_1: bool = False
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical hit"""
        return self.natural_20 and self.dice_type == DiceType.D20
    
    @property
    def is_fumble(self) -> bool:
        """Check if this is a critical fumble"""
        return self.natural_1 and self.dice_type == DiceType.D20


@dataclass
class SkillCheck:
    """Result of a skill check"""
    skill_type: SkillCheckType
    roll: DiceRoll
    difficulty_class: int
    success: bool
    margin: int  # How much succeeded/failed by
    
    @property
    def degree_of_success(self) -> str:
        """Get degree of success/failure"""
        if self.margin >= 10:
            return "Critical Success"
        elif self.margin >= 5:
            return "Success"
        elif self.margin >= 0:
            return "Marginal Success"
        elif self.margin >= -5:
            return "Failure"
        else:
            return "Critical Failure"


@dataclass
class SavingThrow:
    """Result of a saving throw"""
    save_type: SaveType
    roll: DiceRoll
    difficulty_class: int
    success: bool
    damage_resisted: Optional[int] = None  # For half damage saves


class D20Core:
    """Core D20 mechanics engine for the Shell engine"""
    
    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)
            logger.debug(f"🎲 D20Core initialized with seed: {random_seed}")
        else:
            logger.debug("🎲 D20Core initialized with random seed")
    
    def roll_dice(self, dice_type: DiceType, num_dice: int = 1, modifier: int = 0) -> DiceRoll:
        """Roll dice with modifier"""
        rolls = [random.randint(1, int(dice_type)) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        # Check for natural 20/1 on d20
        natural_20 = dice_type == DiceType.D20 and any(roll == 20 for roll in rolls)
        natural_1 = dice_type == DiceType.D20 and any(roll == 1 for roll in rolls)
        
        return DiceRoll(
            dice_type=dice_type,
            rolls=rolls,
            total=total,
            modifier=modifier,
            natural_20=natural_20,
            natural_1=natural_1
        )
    
    def roll_skill_check(self, skill_type: SkillCheckType, 
                        ability_modifier: int, 
                        proficiency_bonus: int = 0,
                        difficulty_class: int = 10) -> SkillCheck:
        """Perform a skill check"""
        roll = self.roll_dice(DiceType.D20, modifier=ability_modifier + proficiency_bonus)
        
        success = roll.total >= difficulty_class
        margin = roll.total - difficulty_class
        
        return SkillCheck(
            skill_type=skill_type,
            roll=roll,
            difficulty_class=difficulty_class,
            success=success,
            margin=margin
        )
    
    def roll_saving_throw(self, save_type: SaveType, 
                         ability_modifier: int, 
                         proficiency_bonus: int = 0,
                         difficulty_class: int = 10) -> SavingThrow:
        """Perform a saving throw"""
        roll = self.roll_dice(DiceType.D20, modifier=ability_modifier + proficiency_bonus)
        
        success = roll.total >= difficulty_class
        
        return SavingThrow(
            save_type=save_type,
            roll=roll,
            difficulty_class=difficulty_class,
            success=success
        )
    
    def roll_death_save(self, modifier: int = 0, advantage: bool = False, disadvantage: bool = False) -> Tuple[DiceRoll, bool]:
        """
        The 'Systemic Fix' for Permadeath. 
        Returns (roll, survived) - False if the pilot is scrubbed.
        Standard D&D 5e death save rules:
        - Roll 1-9: Two failures
        - Roll 10-19: One success  
        - Roll 20: Conscious + 1 HP
        """
        # Handle advantage/disadvantage
        if advantage and not disadvantage:
            roll1 = self.roll_dice(DiceType.D20, modifier)
            roll2 = self.roll_dice(DiceType.D20, modifier)
            roll = roll1 if roll1.total >= roll2.total else roll2
        elif disadvantage and not advantage:
            roll1 = self.roll_dice(DiceType.D20, modifier)
            roll2 = self.roll_dice(DiceType.D20, modifier)
            roll = roll1 if roll1.total <= roll2.total else roll2
        else:
            roll = self.roll_dice(DiceType.D20, modifier)
        
        # Determine outcome
        if roll.natural_1:
            # Natural 1 = Two failures
            survived = False
            logger.critical(f"⚰️ DEATH SAVE: Natural 1! Immediate permadeath.")
        elif roll.natural_20:
            # Natural 20 = Stabilized + 1 HP
            survived = True
            logger.info(f"💀 DEATH SAVE: Natural 20! Stabilized with 1 HP.")
        elif roll.total >= 10:
            # 10-19 = One success
            survived = True
            logger.debug(f"💀 DEATH SAVE: Success ({roll.total} >= 10)")
        else:
            # 2-9 = Two failures
            survived = False
            logger.warning(f"⚰️ DEATH SAVE: Failure ({roll.total} < 10)")
        
        return roll, survived
    
    def roll_initiative(self, dexterity_modifier: int) -> DiceRoll:
        """Roll initiative for combat"""
        return self.roll_dice(DiceType.D20, modifier=dexterity_modifier)
    
    def roll_attack(self, attack_bonus: int, advantage: bool = False, disadvantage: bool = False) -> DiceRoll:
        """Roll attack with advantage/disadvantage"""
        if advantage and not disadvantage:
            roll1 = self.roll_dice(DiceType.D20, modifier=attack_bonus)
            roll2 = self.roll_dice(DiceType.D20, modifier=attack_bonus)
            return roll1 if roll1.total >= roll2.total else roll2
        elif disadvantage and not advantage:
            roll1 = self.roll_dice(DiceType.D20, modifier=attack_bonus)
            roll2 = self.roll_dice(DiceType.D20, modifier=attack_bonus)
            return roll1 if roll1.total <= roll2.total else roll2
        else:
            return self.roll_dice(DiceType.D20, modifier=attack_bonus)
    
    def roll_damage(self, dice_type: DiceType, num_dice: int = 1, modifier: int = 0, 
                   critical: bool = False) -> DiceRoll:
        """Roll damage with critical hit support"""
        base_dice = num_dice * (2 if critical else 1)
        return self.roll_dice(dice_type, base_dice, modifier)
    
    def calculate_armor_class(self, base_ac: int, armor_bonus: int = 0, 
                            shield_bonus: int = 0, dexterity_modifier: int = 0,
                            max_dex: Optional[int] = None) -> int:
        """Calculate armor class"""
        dex_bonus = dexterity_modifier
        if max_dex is not None:
            dex_bonus = min(dex_bonus, max_dex)
        
        return base_ac + armor_bonus + shield_bonus + dex_bonus
    
    def calculate_hit_points(self, hit_dice: DiceType, num_dice: int, 
                           constitution_modifier: int) -> int:
        """Calculate hit points"""
        base_hp = sum(random.randint(1, int(hit_dice)) for _ in range(num_dice))
        return base_hp + (constitution_modifier * num_dice)
    
    def roll_random_treasure(self, cr: int) -> Dict[str, Any]:
        """Roll random treasure based on Challenge Rating"""
        # Simplified treasure table
        treasure_tables = {
            1: {"coins": {"gp": random.randint(5, 20)}, "items": []},
            2: {"coins": {"gp": random.randint(20, 100)}, "items": []},
            3: {"coins": {"gp": random.randint(100, 500)}, "items": ["potion"]},
            4: {"coins": {"gp": random.randint(500, 2000)}, "items": ["scroll", "potion"]},
            5: {"coins": {"gp": random.randint(2000, 10000)}, "items": ["magic_item", "scroll"]},
        }
        
        cr_tier = min(max(cr // 2, 1), 5)
        treasure = treasure_tables[cr_tier].copy()
        
        logger.debug(f"💰 Rolled treasure for CR {cr}: {treasure}")
        return treasure
    
    def get_ability_modifier(self, ability_score: int) -> int:
        """Convert ability score to modifier"""
        return (ability_score - 10) // 2
    
    def roll_encounter(self, difficulty: str = "medium") -> Dict[str, Any]:
        """Roll random encounter"""
        encounter_difficulties = {
            "easy": {"cr": random.randint(1, 3), "num_enemies": random.randint(1, 2)},
            "medium": {"cr": random.randint(2, 5), "num_enemies": random.randint(2, 4)},
            "hard": {"cr": random.randint(4, 7), "num_enemies": random.randint(3, 6)},
            "deadly": {"cr": random.randint(6, 10), "num_enemies": random.randint(4, 8)}
        }
        
        encounter = encounter_difficulties.get(difficulty, encounter_difficulties["medium"])
        encounter["difficulty"] = difficulty
        
        logger.debug(f"⚔️ Rolled {difficulty} encounter: CR {encounter['cr']}, {encounter['num_enemies']} enemies")
        return encounter
    
    def simulate_combat_round(self, attacker: Dict[str, Any], defender: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a single combat round"""
        # Roll initiative
        attacker_init = self.roll_initiative(attacker.get("dexterity", 10))
        defender_init = self.roll_initiative(defender.get("dexterity", 10))
        
        results = {
            "attacker_initiative": attacker_init.total,
            "defender_initiative": defender_init.total,
            "attacks": []
        }
        
        # Determine order
        if attacker_init.total >= defender_init.total:
            # Attacker goes first
            attack_roll = self.roll_attack(attacker.get("attack_bonus", 0))
            target_ac = defender.get("armor_class", 10)
            
            if attack_roll.total >= target_ac:
                damage_roll = self.roll_damage(DiceType.D8, 1, attacker.get("strength", 10) // 2, attack_roll.is_critical)
                results["attacks"].append({
                    "attacker": "attacker",
                    "hit": True,
                    "damage": damage_roll.total,
                    "critical": attack_roll.is_critical
                })
            else:
                results["attacks"].append({
                    "attacker": "attacker",
                    "hit": False,
                    "damage": 0,
                    "critical": False
                })
        
        return results
    
    def export_state(self) -> Dict[str, Any]:
        """Export D20 core state for serialization"""
        return {
            "random_seed": random.getstate()[1][0] if hasattr(random, 'getstate') else None,
            "timestamp": time.time()
        }
    
    def import_state(self, state: Dict[str, Any]):
        """Import D20 core state from serialization"""
        if "random_seed" in state and state["random_seed"]:
            random.seed(state["random_seed"])
            logger.debug(f"🎲 D20Core imported state with seed: {state['random_seed']}")


# Factory function for easy initialization
def create_d20_core(random_seed: Optional[int] = None) -> D20Core:
    """Create a D20Core instance"""
    return D20Core(random_seed)


# Global instance
d20_core = create_d20_core()
