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
from src.shared.state.entity_registry import EntityRegistry
from src.shared.state.roster_sync import RosterSyncService
from src.shared.teams.roster_save import load_roster
from src.shared.session.game_session import GameSession
from src.shared.dispatch.dispatch_system import DispatchSystem

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
    
    # Try to load existing save
    from src.shared.persistence.save_manager import SaveManager
    save_result = SaveManager.load()
    
    if save_result:
        # Load from save file
        roster_data, session_data = save_result
        roster = Roster.from_dict(roster_data)
        game_session = GameSession.from_dict(session_data)
        logger.info(f"Loaded save: {len(roster.entries)} slimes, {len(game_session.resources)} resources")
    else:
        # Create new game
        game_session = GameSession.new_game()
        roster = load_roster()  # Fallback to existing roster.json
        logger.info("Starting new game")
    
    # Create shared systems
    dispatch_system = DispatchSystem()
    
    # Create shared entity registry from roster
    entity_registry = EntityRegistry.from_roster(roster)
    
    # Create RosterSyncService to keep both systems in sync
    roster_sync = RosterSyncService(roster, entity_registry)
    
    # Sync registry from roster (ensure consistency)
    roster_sync.sync_from_roster()
    
    # Register scenes
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
    
    return manager, entity_registry, game_session, dispatch_system, roster, roster_sync

def main():
    logger.info("🚀 Launching Slime Breeder...")
    app, entity_registry, game_session, dispatch_system, roster, roster_sync = create_app()
    
    # Set shared state that gets passed to all scenes
    app.set_shared_state(
        entity_registry=entity_registry,
        game_session=game_session,
        dispatch_system=dispatch_system,
        roster=roster,
        roster_sync=roster_sync
    )
    
    app.run("garden")

if __name__ == "__main__":
    main()
