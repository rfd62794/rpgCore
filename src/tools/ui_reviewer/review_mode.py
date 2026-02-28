import pygame
import sys
import time
from src.shared.engine.scene_manager import SceneManager
from src.shared.ui.spec import UISpec
from .mock_data import generate_mock_roster
from .screenshot_tool import save_screenshot

def run_review(scene_name: str):
    """Launches a scene for review, takes a screenshot, and exits."""
    pygame.init()
    
    # Use standard UISpec
    spec = UISpec(screen_width=1280, screen_height=720)
    screen = pygame.display.set_mode((spec.screen_width, spec.screen_height))
    pygame.display.set_caption(f"UI Review: {scene_name}")
    
    roster = generate_mock_roster()
    
    # Specialized SceneManager that doesn't loop forever
    manager = SceneManager(screen, spec)
    
    # We need to manually register the scenes we want to review
    from src.apps.slime_breeder.ui.scene_garden import GardenScene
    
    scene_classes = {
        "garden": GardenScene
    }
    
    if scene_name not in scene_classes:
        print(f"Error: Scene '{scene_name}' not supported for review yet.")
        pygame.quit()
        return

    # Initialize scene
    scene = scene_classes[scene_name](manager, spec, roster=roster)
    
    # Force selection of one slime for the profile card review
    if scene_name == "garden" and roster.slimes:
        # Simulate picking the first slime
        s = scene.garden_state.slimes[0]
        scene.selected_entities = [s]
        scene.on_selection_changed()
    
    # Brief render loop (enough to layout)
    for _ in range(5):
        scene.update(0.016)
        scene.render(screen)
        pygame.display.flip()
        time.sleep(0.1)
        
    # Capture
    save_screenshot(screen, scene_name)
    
    pygame.quit()
