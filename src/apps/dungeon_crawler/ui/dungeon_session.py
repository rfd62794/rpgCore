import random
from typing import List, Optional
from loguru import logger

from src.apps.dungeon_crawler.entities.hero import Hero
from src.apps.dungeon_crawler.world.floor import Floor
from src.apps.dungeon_crawler.world.room_generator import RoomGenerator
from src.apps.dungeon_crawler.hub.the_room import TheRoom
from src.shared.combat.turn_order import TurnOrderManager
from src.shared.teams.roster import Roster, TeamRole
from src.shared.teams.roster_save import load_roster, save_roster
from src.shared.teams.stat_calculator import calculate_hp, calculate_attack, calculate_speed

FIRST_NAMES = ["Aldric", "Maren", "Thorn", "Vex", "Sable", "Dusk"]
LAST_NAMES  = ["the Bold", "the Unlucky", "of the Deep", 
              "the Forgotten", "Ironhands", "of Ashfall"]

class DungeonSession:
    """
    Orchestrates the lifecycle of a Dungeon Crawler run.
    Mirrors the SpaceTraderSession pattern.
    """
    def __init__(self):
        logger.info("Creating DungeonSession...")
        self.hub = TheRoom()
        self.hero: Optional[Hero] = None
        self.floor: Optional[Floor] = None
        self.turn_manager: Optional[TurnOrderManager] = None
        self.ancestors: List[dict] = [] # List of {name, class, floor, kills}
        
        # Team Roster Integration
        logger.info("Loading roster...")
        self.roster = load_roster()
        self.party_slimes = [] # List of RosterSlime
        logger.info(f"DungeonSession created: {self}")

    def generate_hero_name(self) -> str:
        return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

    def start_run(self, class_type: str = "fighter") -> None:
        name = self.generate_hero_name()
        self.hero = Hero(name, class_type)
        logger.info(f"🚀 Starting run with {self.hero.name} ({class_type})")
        
        # Initialize floor 1
        gen = RoomGenerator()
        self.floor = gen.generate(depth=1)
        self.floor.move_to("entrance")
        
        self.turn_manager = TurnOrderManager()
        
        self.party_slimes = [] # Reset for new run
        self._initialize_party_from_roster()

    def _initialize_party_from_roster(self):
        team = self.roster.get_dungeon_team()
        for slime in team.members:
            if slime.alive:
                slime.locked = True
                self.party_slimes.append(slime)
        save_roster(self.roster)

    def descend(self) -> Floor:
        if not self.floor:
            self.start_run()
            return self.floor
        
        new_depth = self.floor.depth + 1
        logger.info(f"🔽 Descending to floor {new_depth}")
        gen = RoomGenerator()
        self.floor = gen.generate(depth=new_depth)
        self.floor.move_to("entrance")
        return self.floor

    def end_run(self, cause: str = "extraction") -> None:
        if not self.hero:
            return

        logger.info(f"Dungeon run ended: {cause}")
        # Unlock slimes and handle deaths
        team = self.roster.get_dungeon_team()
        for rs in self.party_slimes:
            # Check if slime died (HP in combat unit or similar)
            # In current demo, if hero dies, entire run fails or specific slimes die.
            # We'll assume casualties are registered via cause or specific result calls.
            rs.locked = False
        
        save_roster(self.roster)
        
        # Record ancestor
        ancestor_record = {
            "name": self.hero.name,
            "class": self.hero.class_type,
            "floor": self.floor.depth if self.floor else 1,
            "kills": 0, # Could be expanded later
            "cause": cause
        }
        self.ancestors.append(ancestor_record)
        
        # Reset but keep ancestors list
        self.hero = None
        self.floor = None
        self.turn_manager = None

    def get_ancestor_list(self) -> List[str]:
        return [f"{a['name']} ({a['class']}) - Floor {a['floor']} ({a['cause']})" for a in self.ancestors]
