#!/usr/bin/env python3
"""Simple test to verify racing scene works"""

import pygame
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.shared.engine.scene_manager import SceneManager
from src.shared.ui.spec import SPEC_720
from src.apps.slime_breeder.scenes.race_scene import RaceScene

def main():
    pygame.init()
    
    # Create a simple scene manager
    manager = SceneManager(SPEC_720)
    
    # Register the racing scene
    manager.register("racing", RaceScene)
    
    # Create a surface to render on
    surface = pygame.display.set_mode((SPEC_720.screen_width, SPEC_720.screen_height))
    pygame.display.set_caption("Race Scene Test")
    
    # Switch to racing scene
    manager.switch_to("racing")
    
    # Simple event loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    # Forward events to scene
                    if hasattr(manager, '_active_scene') and manager._active_scene:
                        manager._active_scene.handle_event(event)
        
        # Update and render
        if hasattr(manager, '_active_scene') and manager._active_scene:
            manager._active_scene.update(dt)
            manager._active_scene.render(surface)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
