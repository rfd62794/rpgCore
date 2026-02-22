"""
Asteroids Player Controller
"""
import pygame
from src.apps.asteroids.entities.ship import Ship

class Controller:
    """Handles human input for the ship"""
    
    def __init__(self):
        self.keys_pressed = set()
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)

    def apply_input(self, ship: Ship, dt: float):
        """Apply held keys to ship kinetics"""
        if not ship.alive: return
        
        thrust = 0.0
        rotation = 0.0
        fire = False
        
        # Thrust Forward
        if any(k in self.keys_pressed for k in [pygame.K_w, pygame.K_UP, pygame.K_KP8]):
            thrust = 1.0
        # Thrust Reverse
        if any(k in self.keys_pressed for k in [pygame.K_s, pygame.K_DOWN, pygame.K_KP2]):
            thrust = -1.0
        # Rotate Left
        if any(k in self.keys_pressed for k in [pygame.K_a, pygame.K_LEFT, pygame.K_KP4]):
            rotation = -1.0
        # Rotate Right
        if any(k in self.keys_pressed for k in [pygame.K_d, pygame.K_RIGHT, pygame.K_KP6]):
            rotation = 1.0
        # Fire
        if any(k in self.keys_pressed for k in [pygame.K_SPACE, pygame.K_KP5, pygame.K_KP0]):
            fire = True
            
        if thrust != 0:
            ship.kinetics.apply_thrust(thrust, dt)
        if rotation != 0:
            ship.kinetics.apply_rotation(rotation, dt)
            
        return fire
