import pygame
from loguru import logger
from src.apps.slime_breeder.ui.scene_garden import GardenScene
from src.apps.slime_breeder.scenes.team_scene import TeamScene
from src.apps.slime_breeder.scenes.breeding_scene import BreedingScene
from src.apps.slime_breeder.scenes.race_scene import RaceScene
from src.apps.slime_breeder.scenes.scene_tower_defense import TowerDefenseScene
from src.apps.dungeon_crawler.ui.scene_the_room import TheRoomScene
from src.apps.dungeon_crawler.ui.scene_dungeon_room import DungeonRoomScene
from src.apps.slime_breeder.scenes.scene_dungeon_path import DungeonPathScene
from src.apps.dungeon_crawler.ui.scene_dungeon_combat import DungeonCombatScene
from src.apps.dungeon_crawler.ui.scene_inventory import InventoryOverlay
from src.shared.engine.scene_manager import SceneManager
from src.shared.ui.spec import SPEC_720

def create_app() -> SceneManager:
    """Create and configure the Slime Breeder app."""
    # Initialize Manager with Standard Spec
    manager = SceneManager(
        width=SPEC_720.screen_width,
        height=SPEC_720.screen_height,
        title="Slime Breeder — Core Pass",
        fps=60,
        spec=SPEC_720
    )
    
    manager.register("garden", GardenScene)
    manager.register("teams", TeamScene)
    manager.register("breeding", BreedingScene)
    manager.register("racing", RaceScene)
    manager.register("tower_defense", TowerDefenseScene)
    manager.register("dungeon", TheRoomScene)
    manager.register("dungeon_room", DungeonRoomScene)
    manager.register("dungeon_path", DungeonPathScene)
    manager.register("dungeon_combat", DungeonCombatScene)
    manager.register("inventory", InventoryOverlay)
    
    return manager

def main():
    logger.info("🚀 Launching Slime Breeder...")
    app = create_app()
    app.run("garden")

if __name__ == "__main__":
    main()
