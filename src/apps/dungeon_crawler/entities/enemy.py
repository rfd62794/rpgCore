from src.shared.items.loot_table import LootTable
from src.shared.items.item import Item

class Enemy:
    def __init__(self, id_str: str, name: str, tier: str, stats: dict[str, int], loot_table: LootTable):
        self.id = id_str
        self.name = name
        self.tier = tier  # mindless | tactical
        self.stats = stats.copy()
        
        # Ensure current hp/mp exist if only max was provided, or vice versa
        if "hp" in self.stats and "max_hp" not in self.stats:
            self.stats["max_hp"] = self.stats["hp"]
            
        self.loot_table = loot_table

    def is_alive(self) -> bool:
        return self.stats.get("hp", 0) > 0

    def get_loot(self, depth: int = 1) -> Item | None:
        """Returns instantiated Item from the loot table, or None."""
        return self.loot_table.roll(depth)
