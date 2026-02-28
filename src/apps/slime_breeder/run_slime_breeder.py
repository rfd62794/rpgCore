import pygame
from loguru import logger
from src.apps.slime_breeder.ui.scene_garden import GardenScene
from src.apps.slime_breeder.scenes.team_scene import TeamScene
from src.shared.engine.scene_manager import SceneManager

def create_app() -> SceneManager:
    """Create and configure the Slime Breeder app."""
    manager = SceneManager(
        width=1024,
        height=768,
        title="Slime Breeder — Creation Aspect",
        fps=60
    )
    manager.register("garden", GardenScene)
    manager.register("teams", TeamScene)
    return manager

def main():
    logger.info("🚀 Launching Slime Breeder...")
    app = create_app()
    app.run("garden")

if __name__ == "__main__":
    main()
