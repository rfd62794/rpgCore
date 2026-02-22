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
        
        if pygame.K_w in self.keys_pressed or pygame.K_UP in self.keys_pressed:
            thrust = 1.0
        if pygame.K_s in self.keys_pressed or pygame.K_DOWN in self.keys_pressed:
            thrust = -1.0
        if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
            rotation = -1.0
        if pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
            rotation = 1.0
        if pygame.K_SPACE in self.keys_pressed:
            fire = True
            
        if thrust != 0:
            ship.kinetics.apply_thrust(thrust, dt)
        if rotation != 0:
            ship.kinetics.apply_rotation(rotation, dt)
            
        return fire
