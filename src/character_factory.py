"""
Character Factory: Archetype Generation

Handles character archetype generation with D&D stat arrays.
Maps personality types to stat distributions and skill proficiencies.

Responsibilities:
- Stat array generation (10/18/12/16/12/10 pattern)
- Skill proficiency assignment
- Personality-based archetype creation
"""

from typing import Dict, List

from loguru import logger
from pydantic import BaseModel

from game_state import PlayerStats
from loot_system import Item


class Archetype(BaseModel):
    """Character archetype template."""
    name: str
    description: str
    stat_array: Dict[str, int]  # strength, dexterity, intelligence, charisma
    skill_proficiencies: List[str]
    starting_inventory: List[str]
    personality_traits: List[str]


class CharacterFactory:
    """
    Factory for creating D&D-style character archetypes.
    
    Generates characters with balanced stat arrays and appropriate skills
    based on their personality archetype.
    """
    
    def __init__(self):
        """Initialize factory with archetype definitions."""
        self.archetypes = self._load_archetypes()
        self.skill_items = self._load_skill_items()
        logger.info("Character Factory initialized with archetypes")
    
    def _load_archetypes(self) -> Dict[str, Archetype]:
        """Load archetype definitions."""
        return {
            "curious": Archetype(
                name="The Explorer",
                description="Driven by insatiable curiosity, always seeking knowledge and new experiences.",
                stat_array={
                    "strength": 10,
                    "dexterity": 12,
                    "intelligence": 16,
                    "charisma": 12
                },
                skill_proficiencies=["investigate", "perception", "search"],
                starting_inventory=["magnifying glass", "journal", "quill pen"],
                personality_traits=["inquisitive", "observant", "knowledge-seeking"]
            ),
            
            "aggressive": Archetype(
                name="The Warrior",
                description="Fierce and direct, prefers action over words. Lives for combat and challenge.",
                stat_array={
                    "strength": 18,
                    "dexterity": 12,
                    "intelligence": 10,
                    "charisma": 10
                },
                skill_proficiencies=["combat", "athletics", "force"],
                starting_inventory=["iron sword", "leather armor", "shield"],
                personality_traits=["bold", "direct", "combat-ready"]
            ),
            
            "tactical": Archetype(
                name="The Strategist",
                description="Methodical and calculating, always thinking several steps ahead.",
                stat_array={
                    "strength": 12,
                    "dexterity": 14,
                    "intelligence": 14,
                    "charisma": 12
                },
                skill_proficiencies=["finesse", "perception", "stealth"],
                starting_inventory=["dagger", "leather armor", "tactical map"],
                personality_traits=["analytical", "patient", "strategic"]
            ),
            
            "chaotic": Archetype(
                name="The Wildcard",
                description="Unpredictable and impulsive, thrives in chaos and confusion.",
                stat_array={
                    "strength": 14,
                    "dexterity": 16,
                    "intelligence": 10,
                    "charisma": 12
                },
                skill_proficiencies=["distract", "acrobatics", "stealth"],
                starting_inventory=["juggling balls", "disguise kit", "lockpicks"],
                personality_traits=["impulsive", "adaptable", "unpredictable"]
            ),
            
            "cunning": Archetype(
                name="The Rogue",
                description="Sly and manipulative, excels at deception and stealth. Always has an angle.",
                stat_array={
                    "strength": 10,
                    "dexterity": 18,
                    "intelligence": 12,
                    "charisma": 12
                },
                skill_proficiencies=["stealth", "finesse", "charm"],
                starting_inventory=["lockpicks", "black hood", "dagger"],
                personality_traits=["sly", "opportunistic", "deceptive"]
            ),
            
            "diplomatic": Archetype(
                name="The Diplomat",
                description="Charismatic and persuasive, excels at negotiation and social manipulation.",
                stat_array={
                    "strength": 10,
                    "dexterity": 12,
                    "intelligence": 12,
                    "charisma": 18
                },
                skill_proficiencies=["charm", "persuade", "social"],
                starting_inventory=["formal clothes", "signet ring", "diplomatic papers"],
                personality_traits=["charming", "persuasive", "diplomatic"]
            )
        }
    
    def _load_skill_items(self) -> Dict[str, Item]:
        """Load items that provide skill bonuses."""
        return {
            "magnifying glass": Item(
                name="Magnifying Glass",
                description="A polished lens that helps with detailed investigation.",
                target_stat="intelligence",
                modifier_value=2
            ),
            "iron sword": Item(
                name="Iron Sword",
                description="A well-balanced blade suitable for combat.",
                target_stat="strength",
                modifier_value=3
            ),
            "dagger": Item(
                name="Dagger",
                description="A sharp blade ideal for finesse attacks.",
                target_stat="dexterity",
                modifier_value=2
            ),
            "lockpicks": Item(
                name="Lockpicks",
                description="A set of fine tools for manipulating locks.",
                target_stat="dexterity",
                modifier_value=2
            ),
            "formal clothes": Item(
                name="Formal Clothes",
                description="Elegant attire that improves social interactions.",
                target_stat="charisma",
                modifier_value=2
            ),
            "signet ring": Item(
                name="Signet Ring",
                description="A ring that signifies authority and breeding.",
                target_stat="charisma",
                modifier_value=1
            )
        }
    
    def create(self, personality: str) -> PlayerStats:
        """
        Create a character based on personality archetype.
        
        Args:
            personality: Archetype identifier
            
        Returns:
            PlayerStats object with archetype-appropriate attributes
        """
        archetype = self.archetypes.get(personality.lower())
        if not archetype:
            logger.warning(f"Unknown archetype: {personality}. Using default.")
            archetype = self.archetypes["curious"]
        
        logger.info(f"Creating {archetype.name} archetype")
        
        # Create inventory items
        inventory = []
        for item_name in archetype.starting_inventory:
            item = self.skill_items.get(item_name)
            if item:
                inventory.append(item)
            else:
                # Create basic item if not in skill items
                from loot_system import Item
                basic_item = Item(
                    name=item_name,
                    description="A basic item",
                    target_stat="luck",
                    modifier_value=0
                )
                inventory.append(basic_item)
        
        # Create player stats
        player = PlayerStats(
            name=f"The {archetype.name}",
            attributes=archetype.stat_array,
            inventory=inventory,
            hp=100,
            max_hp=100,
            gold=50
        )
        
        # Store archetype info for reference
        player.archetype_name = archetype.name
        player.personality_traits = archetype.personality_traits
        player.skill_proficiencies = archetype.skill_proficiencies
        
        logger.info(f"Created {archetype.name} with stats: {archetype.stat_array}")
        
        return player
    
    def get_archetype_info(self, personality: str) -> Archetype:
        """Get archetype information without creating character."""
        return self.archetypes.get(personality.lower(), self.archetypes["curious"])
    
    def list_archetypes(self) -> List[str]:
        """List all available archetypes."""
        return list(self.archetypes.keys())
    
    def validate_stat_array(self, stats: Dict[str, int]) -> bool:
        """
        Validate that a stat array follows D&D balancing rules.
        
        Args:
            stats: Dictionary of stat names to values
            
        Returns:
            True if stats are valid and balanced
        """
        # Check for required stats
        required_stats = ["strength", "dexterity", "intelligence", "charisma"]
        if not all(stat in stats for stat in required_stats):
            return False
        
        # Check stat ranges (assuming 1-20 scale)
        for stat_name, stat_value in stats.items():
            if not (1 <= stat_value <= 20):
                return False
        
        # Check total point balance (adjust based on your point buy system)
        total_points = sum(stats.values())
        if not (40 <= total_points <= 80):  # Adjust range as needed
            return False
        
        return True


# Export for use by engine
__all__ = ["CharacterFactory"]
