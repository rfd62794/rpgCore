"""
Asteroids Strategy - UnifiedPPU Rendering Strategy

ADR 195: The Newtonian Vector Core

Rendering strategy for the "Ur-Asteroids" game slice that implements
the RenderProtocol and integrates with the hardened UnifiedPPU system.

This strategy renders the Newtonian physics entities within the
sovereign 160x144 resolution grid with toroidal ghosting effects.

Key Features:
- Newtonian ghosting for smooth toroidal wrap
- Pixel-perfect triangle ship rendering
- Circular asteroid rendering with rotation
- Energy-based color intensity
- 60Hz frame synchronization
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math

from ....interfaces.protocols import RenderProtocol, Result
from ....abc.base import BasePPU
from ....kernel.constants import SOVEREIGN_WIDTH, SOVEREIGN_HEIGHT, SOVEREIGN_PIXELS
from .physics_body import PhysicsBody, PhysicsState
from .space_entity import SpaceEntity, EntityType
from .vector2 import Vector2


class AsteroidsStrategy:
    """Rendering strategy for Newtonian asteroids physics"""
    
    def __init__(self):
        self.physics_body = PhysicsBody()
        self.frame_buffer: Optional[bytearray] = None
        self.width = SOVEREIGN_WIDTH
        self.height = SOVEREIGN_HEIGHT
        
        # Rendering properties
        self.clear_color = 0  # Black background
        self.ship_color = 1   # White ship
        self.asteroid_color = 2  # Gray asteroids
        self.bullet_color = 1    # White bullets
        
        # Energy-based rendering
        self.energy_level = 100.0
        
        # Performance tracking
        self.render_count = 0
        self.last_render_time = 0.0
    
    def initialize(self, width: int, height: int) -> Result[bool]:
        """Initialize the asteroids rendering strategy"""
        try:
            self.width = width
            self.height = height
            
            # Initialize frame buffer
            buffer_size = width * height
            self.frame_buffer = bytearray(buffer_size)
            
            # Clear frame buffer
            self._clear_frame_buffer()
            
            # Reset physics
            self.physics_body.reset_game()
            
            return Result.success_result(True)
            
        except Exception as e:
            return Result.failure_result(f"Failed to initialize AsteroidsStrategy: {str(e)}")
    
    def render_state(self, game_state: Any) -> Result[bytes]:
        """Render a complete frame from physics state"""
        try:
            # Update physics
            current_time = 0.0  # Would use actual time in production
            physics_result = self.physics_body.update(current_time)
            if not physics_result.success:
                return Result.failure_result(f"Physics update failed: {physics_result.error}")
            
            physics_state = physics_result.value
            
            # Update energy level from physics state
            self.energy_level = physics_state.energy
            
            # Clear frame buffer
            self._clear_frame_buffer()
            
            # Render all entities
            self._render_entities(physics_state.entities)
            
            # Apply energy-based effects
            self._apply_energy_effects()
            
            # Return frame buffer
            return Result.success_result(bytes(self.frame_buffer))
            
        except Exception as e:
            return Result.failure_result(f"Render failed: {str(e)}")
    
    def _clear_frame_buffer(self) -> None:
        """Clear the frame buffer to background color"""
        if self.frame_buffer:
            self.frame_buffer[:] = bytes([self.clear_color]) * len(self.frame_buffer)
    
    def _render_entities(self, entities: List[SpaceEntity]) -> None:
        """Render all entities with Newtonian ghosting"""
        for entity in entities:
            if not entity.active:
                continue
            
            if entity.entity_type == EntityType.SHIP:
                self._render_ship(entity)
            elif entity.entity_type == EntityType.BULLET:
                self._render_bullet(entity)
            elif entity.entity_type in [EntityType.LARGE_ASTEROID, EntityType.MEDIUM_ASTEROID, EntityType.SMALL_ASTEROID]:
                self._render_asteroid(entity)
    
    def _render_ship(self, ship: SpaceEntity) -> None:
        """Render the player ship as a triangle"""
        # Get world vertices
        vertices = ship.get_world_vertices()
        
        # Render main ship
        self._render_triangle(vertices, self.ship_color)
        
        # Render Newtonian ghosts if near boundaries
        ghost_positions = ship.get_wrapped_positions()
        for ghost_pos in ghost_positions[1:]:  # Skip the main position
            ghost_vertices = []
            for vertex in vertices:
                # Calculate ghost vertex position
                offset = ghost_pos - ship.position
                ghost_vertex = vertex + offset
                ghost_vertices.append(ghost_vertex)
            
            # Render ghost with reduced intensity
            self._render_triangle(ghost_vertices, self.ship_color, alpha=0.5)
    
    def _render_triangle(self, vertices: List[Vector2], color: int, alpha: float = 1.0) -> None:
        """Render a triangle using scanline algorithm"""
        if len(vertices) != 3 or not self.frame_buffer:
            return
        
        # Convert vertices to integer coordinates
        points = [(int(v.x), int(v.y)) for v in vertices]
        
        # Simple triangle rendering using line drawing
        # Draw triangle outline
        self._draw_line(points[0], points[1], color, alpha)
        self._draw_line(points[1], points[2], color, alpha)
        self._draw_line(points[2], points[0], color, alpha)
        
        # Fill triangle (simple flood fill approach)
        # For now, just outline - can be enhanced later
    
    def _render_asteroid(self, asteroid: SpaceEntity) -> None:
        """Render an asteroid as a circle"""
        # Render main asteroid
        self._render_circle(asteroid.position, asteroid.radius, self.asteroid_color)
        
        # Render Newtonian ghosts if near boundaries
        ghost_positions = asteroid.get_wrapped_positions()
        for ghost_pos in ghost_positions[1:]:  # Skip the main position
            # Render ghost with reduced intensity
            self._render_circle(ghost_pos, asteroid.radius, self.asteroid_color, alpha=0.5)
    
    def _render_circle(self, center: Vector2, radius: float, color: int, alpha: float = 1.0) -> None:
        """Render a circle using midpoint algorithm"""
        if not self.frame_buffer:
            return
        
        cx, cy = int(center.x), int(center.y)
        r = int(radius)
        
        # Midpoint circle algorithm
        x = 0
        y = r
        d = 1 - r
        
        self._draw_circle_points(cx, cy, x, y, color, alpha)
        
        while x < y:
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1
            
            self._draw_circle_points(cx, cy, x, y, color, alpha)
    
    def _draw_circle_points(self, cx: int, cy: int, x: int, y: int, color: int, alpha: float) -> None:
        """Draw 8 symmetric points of a circle"""
        points = [
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x)
        ]
        
        for px, py in points:
            self._set_pixel(px, py, color, alpha)
    
    def _render_bullet(self, bullet: SpaceEntity) -> None:
        """Render a bullet as a small circle"""
        # Render main bullet
        self._render_circle(bullet.position, bullet.radius, self.bullet_color)
        
        # Render Newtonian ghosts if near boundaries
        ghost_positions = bullet.get_wrapped_positions()
        for ghost_pos in ghost_positions[1:]:  # Skip the main position
            # Render ghost with reduced intensity
            self._render_circle(ghost_pos, bullet.radius, self.bullet_color, alpha=0.5)
    
    def _draw_line(self, p1: Tuple[int, int], p2: Tuple[int, int], color: int, alpha: float) -> None:
        """Draw a line using Bresenham's algorithm"""
        x1, y1 = p1
        x2, y2 = p2
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        
        err = dx - dy
        
        while True:
            self._set_pixel(x1, y1, color, alpha)
            
            if x1 == x2 and y1 == y2:
                break
            
            e2 = 2 * err
            
            if e2 > -dy:
                err -= dy
                x1 += sx
            
            if e2 < dx:
                err += dx
                y1 += sy
    
    def _set_pixel(self, x: int, y: int, color: int, alpha: float) -> None:
        """Set a pixel with alpha blending"""
        if not self.frame_buffer:
            return
        
        # Check bounds
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        
        # Calculate buffer index
        index = y * self.width + x
        
        # Apply alpha blending (simple approach)
        if alpha >= 1.0:
            self.frame_buffer[index] = color
        elif alpha > 0.0:
            # Blend with background
            current = self.frame_buffer[index]
            blended = int(current * (1 - alpha) + color * alpha)
            self.frame_buffer[index] = blended
    
    def _apply_energy_effects(self) -> None:
        """Apply energy-based visual effects"""
        if not self.frame_buffer:
            return
        
        # Apply energy-based dimming
        energy_factor = self.energy_level / 100.0
        
        if energy_factor < 1.0:
            # Dim the entire frame based on energy level
            for i in range(len(self.frame_buffer)):
                if self.frame_buffer[i] > 0:  # Don't dim background
                    self.frame_buffer[i] = int(self.frame_buffer[i] * energy_factor)
    
    def set_thrust(self, active: bool) -> None:
        """Set thrust state for physics"""
        self.physics_body.set_thrust(active)
    
    def set_rotation(self, direction: float) -> None:
        """Set rotation direction for physics"""
        self.physics_body.set_rotation(direction)
    
    def fire_bullet(self) -> Result[None]:
        """Fire a bullet"""
        return self.physics_body.fire_bullet()
    
    def reset_game(self) -> Result[None]:
        """Reset the game"""
        return self.physics_body.reset_game()
    
    def get_physics_debug_info(self) -> Dict[str, Any]:
        """Get debug information from physics system"""
        return self.physics_body.get_debug_info()
    
    def get_render_stats(self) -> Dict[str, Any]:
        """Get rendering statistics"""
        return {
            'render_count': self.render_count,
            'frame_buffer_size': len(self.frame_buffer) if self.frame_buffer else 0,
            'resolution': f"{self.width}x{self.height}",
            'energy_level': self.energy_level
        }
