"""
Asteroids Simulation Physics
SRP: Coordinates toroidal wrap and movement scaling
"""
from src.shared.entities.kinetics import KineticBody, Vector2D

def update_kinetics(body: KineticBody, dt: float, bounds: tuple = (160, 144)):
    """Update body with bounds awareness"""
    body.bounds = bounds
    body.update(dt)

def set_toroidal_wrap(body: KineticBody, bounds: tuple):
    """Ensure body uses correct wrap bounds"""
    body.bounds = bounds
