import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.apps.slime_clan.auto_battle import SlimeUnit, Shape, Hat, create_slime, TileState

@dataclass
class Colony:
    id: str
    name: str
    x: int
    y: int
    coord: tuple[int, int]
    node_type: Any # NodeType enum
    connections: List[str]
    faction: Optional[str] = None
    original_faction: Optional[str] = None
    population: int = 10
    morale: int = 100
    relations: Dict[str, int] = field(default_factory=lambda: {"CLAN_BLUE": 0, "CLAN_RED": 0, "CLAN_YELLOW": 0, "ASTRONAUT": 20})
    units: List[SlimeUnit] = field(default_factory=list)
    map_seed: int = field(default_factory=lambda: random.randint(0, 999999))
    history: List[str] = field(default_factory=list)

class ColonyManager:
    def __init__(self, node_type_enum):
        self.colonies: Dict[str, Colony] = {}
        self.node_type_enum = node_type_enum
        self.name_pool = ["Mire", "Fenwick", "Ashroot", "Bramble", "Gust", "Ember", "Tide", "Cinder", "Reed", "Moss"]

    def create_colony(self, id: str, name: str, x: int, y: int, coord: tuple[int, int], node_type: Any, connections: List[str], faction: Optional[str] = None) -> Colony:
        colony = Colony(
            id=id,
            name=name,
            x=x,
            y=y,
            coord=coord,
            node_type=node_type,
            connections=connections,
            faction=faction,
            original_faction=faction
        )
        self.colonies[id] = colony
        
        # Generate named units for Unbound tribes
        if faction == "CLAN_YELLOW":
            self._generate_tribal_units(colony)
            
        return colony

    def _generate_tribal_units(self, colony: Colony):
        # Generate 3 named units
        available_names = list(self.name_pool)
        random.shuffle(available_names)
        
        for i in range(3):
            name = available_names.pop()
            shape = random.choice(list(Shape))
            hat = random.choice(list(Hat))
            unit = create_slime(f"{colony.id}_{name}", name, TileState.BLUE, shape, hat, is_player=True)
            # Astronaut sympathy starts at 20
            setattr(unit, "sympathy", 20)
            colony.units.append(unit)
        colony.history.append(f"Colony founded by {colony.original_faction}. Tribal units gathered.")

    def get_colony(self, id: str) -> Optional[Colony]:
        return self.colonies.get(id)

    def get_owner(self, coord: tuple[int, int]) -> Optional[str]:
        for colony in self.colonies.values():
            if colony.coord == coord:
                return colony.faction
        return None

    def set_owner(self, coord: tuple[int, int], faction: Optional[str]):
        for colony in self.colonies.values():
            if colony.coord == coord:
                colony.faction = faction
                break

    def keys(self):
        return self.colonies.keys()

    def values(self):
        return self.colonies.values()

    def items(self):
        return self.colonies.items()

    def __iter__(self):
        return iter(self.colonies)

    def __getitem__(self, key):
        return self.colonies[key]

    def __contains__(self, key):
        return key in self.colonies

    def __len__(self):
        return len(self.colonies)
