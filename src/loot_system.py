"""
Quartermaster: Procedural Loot Generation

The Quartermaster handles item drops from investigate actions.
Triggered when Arbiter succeeds on 'investigate' or 'force' intents.
"""

import random
from pydantic import BaseModel, Field
from loguru import logger


class Item(BaseModel):
    """A loot item with stats."""
    
    name: str = Field(description="Item name")
    description: str = Field(description="Flavorful description")
    stat_bonus: str = Field(default="", description="Stat modifier (e.g., '+1 Pierce', '+5 HP')")
    value: int = Field(default=0, ge=0, description="Gold value")


class LootSystem:
    """
    Procedural loot generator.
    
    Design:
    - Deterministic (no AI) for speed
    - Context-aware (tavern items vs dungeon items)
    - Rarity-based (common, uncommon, rare)
    """
    
    def __init__(self):
        """Initialize loot tables."""
        self.tavern_loot = [
            Item(name="Dull Dirk", description="A rusty dagger with a chipped blade", stat_bonus="+1 Pierce", value=5),
            Item(name="Ale-Soaked Rag", description="It smells terrible but might be useful", stat_bonus="", value=1),
            Item(name="Copper Coins", description="A small handful of tarnished copper", stat_bonus="", value=3),
            Item(name="Lucky Die", description="A six-sided die that always rolls 6", stat_bonus="+1 Luck", value=10),
            Item(name="Bent Fork", description="Surprisingly sharp", stat_bonus="+1 Stab", value=2),
            Item(name="Half-Eaten Cheese", description="Still good? Probably?", stat_bonus="+2 HP", value=1),
        ]
        
        self.dungeon_loot = [
            Item(name="Iron Key", description="Rusty but functional", stat_bonus="", value=5),
            Item(name="Torch Stub", description="Burns for about 10 minutes", stat_bonus="", value=2),
            Item(name="Skull Fragment", description="Creepy memento", stat_bonus="", value=1),
        ]
    
    def generate_loot(self, location: str = "tavern", intent: str = "investigate") -> Item | None:
        """
        Generate a random loot item.
        
        Args:
            location: Current location (tavern, dungeon, etc.)
            intent: Action intent (investigate, force)
        
        Returns:
            Item if successful, None if no loot found
        """
        # 60% chance of finding something when investigating
        # 30% chance when using force (you break it)
        drop_chance = 0.6 if intent == "investigate" else 0.3
        
        if random.random() > drop_chance:
            logger.debug("No loot found")
            return None
        
        # Select loot table
        loot_table = self.tavern_loot if "tavern" in location.lower() else self.dungeon_loot
        
        item = random.choice(loot_table)
        logger.info(f"Loot generated: {item.name}")
        return item
