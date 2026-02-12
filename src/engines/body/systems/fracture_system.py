"""
FractureSystem - Asteroid Splitting Logic with Cascading Cleanup
SRP: Handles 1 -> 2 -> 4 rock splitting logic and debris generation
"""

import math
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from foundation.types import Result
from engines.body.components.kinetic_body import KineticBody, create_asteroid


@dataclass
class AsteroidFragment:
    """Represents a piece of a fractured asteroid"""
    kinetic_body: KineticBody
    size: int  # 1 = small, 2 = medium, 3 = large
    health: int
    radius: float
    color: Tuple[int, int, int]
    point_value: int
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position"""
        return self.kinetic_body.get_position_tuple()
    
    def take_damage(self, damage: float) -> bool:
        """Apply damage and return True if destroyed"""
        self.health -= damage
        return self.health <= 0


class FractureSystem:
    """
    Handles asteroid splitting with cascading cleanup logic.
    Implements the classic 1->2->4 fracture pattern.
    """
    
    def __init__(self):
        """Initialize fracture system with size configurations"""
        # Size configurations: size -> (radius, health, points, color)
        self.size_configs = {
            3: {  # Large asteroid
                'radius': 8.0,
                'health': 3,
                'points': 20,
                'color': (170, 170, 170),  # Grey
                'split_count': 2,
                'split_into_size': 2
            },
            2: {  # Medium asteroid
                'radius': 4.0,
                'health': 2,
                'points': 50,
                'color': (192, 192, 192),  # Light grey
                'split_count': 2,
                'split_into_size': 1
            },
            1: {  # Small asteroid
                'radius': 2.0,
                'health': 1,
                'points': 100,
                'color': (224, 224, 224),  # Very light grey
                'split_count': 0,  # Small asteroids don't split
                'split_into_size': 0
            }
        }
        
        # Physics parameters for fragment behavior
        self.fragment_speed_range = (15.0, 40.0)  # Speed range for new fragments
        self.scatter_angle_range = math.pi / 3  # 60 degree scatter cone
        
    def fracture_asteroid(self, 
                          asteroid: AsteroidFragment,
                          impact_angle: Optional[float] = None) -> Result[List[AsteroidFragment]]:
        """
        Fracture an asteroid into smaller pieces
        
        Args:
            asteroid: The asteroid to fracture
            impact_angle: Angle of impact (affects scatter direction)
            
        Returns:
            Result containing list of new fragments or error
        """
        config = self.size_configs.get(asteroid.size)
        
        if config['split_count'] == 0:
            # Small asteroid - no fragments, just destroy
            return Result(success=True, value=[])
        
        # Create fragments
        fragments = []
        parent_pos = asteroid.get_position()
        parent_velocity = asteroid.kinetic_body.state.velocity
        
        # Determine scatter direction
        if impact_angle is not None:
            base_angle = impact_angle
        else:
            base_angle = random.uniform(0, 2 * math.pi)
        
        # Generate fragments
        for i in range(config['split_count']):
            # Calculate scatter angle for this fragment
            angle_offset = (i - config['split_count'] / 2) * (self.scatter_angle_range / config['split_count'])
            scatter_angle = base_angle + angle_offset
            
            # Calculate fragment velocity
            speed = random.uniform(*self.fragment_speed_range)
            fragment_velocity = parent_velocity * 0.5  # Inherit some parent momentum
            
            # Add scatter velocity
            scatter_velocity_x = math.cos(scatter_angle) * speed
            scatter_velocity_y = math.sin(scatter_angle) * speed
            
            final_velocity_x = fragment_velocity.x + scatter_velocity_x
            final_velocity_y = fragment_velocity.y + scatter_velocity_y
            
            # Create fragment
            fragment = self._create_fragment(
                size=config['split_into_size'],
                x=parent_pos[0],
                y=parent_pos[1],
                vx=final_velocity_x,
                vy=final_velocity_y
            )
            
            fragments.append(fragment)
        
        return Result(success=True, value=fragments)
    
    def _create_fragment(self, 
                        size: int, 
                        x: float, 
                        y: float, 
                        vx: float, 
                        vy: float) -> AsteroidFragment:
        """Create a new asteroid fragment"""
        config = self.size_configs[size]
        
        # Add slight position offset to prevent overlap
        offset_x = random.uniform(-2, 2)
        offset_y = random.uniform(-2, 2)
        
        kinetic_body = create_asteroid(x + offset_x, y + offset_y, vx, vy)
        
        return AsteroidFragment(
            kinetic_body=kinetic_body,
            size=size,
            health=config['health'],
            radius=config['radius'],
            color=config['color'],
            point_value=config['points']
        )
    
    def create_initial_asteroids(self, count: int, 
                                safe_zone: Optional[Tuple[float, float, float]] = None) -> List[AsteroidFragment]:
        """
        Create initial asteroids for a wave
        
        Args:
            count: Number of asteroids to create
            safe_zone: (x, y, radius) - area to avoid spawning asteroids
            
        Returns:
            List of created asteroids
        """
        asteroids = []
        
        for _ in range(count):
            # Random position (avoiding safe zone if specified)
            if safe_zone:
                x, y = self._find_safe_position(safe_zone)
            else:
                x = random.uniform(20, 140)  # SOVEREIGN_WIDTH - 20
                y = random.uniform(20, 124)  # SOVEREIGN_HEIGHT - 20
            
            # Random velocity
            vx = random.uniform(-30, 30)
            vy = random.uniform(-30, 30)
            
            # Random size (favor larger asteroids initially)
            size_weights = [3, 3, 2, 2, 1]  # More large/medium asteroids
            size = random.choice(size_weights)
            
            asteroid = self._create_fragment(size, x, y, vx, vy)
            asteroids.append(asteroid)
        
        return asteroids
    
    def _find_safe_position(self, safe_zone: Tuple[float, float, float]) -> Tuple[float, float]:
        """Find a position outside the safe zone"""
        safe_x, safe_y, safe_radius = safe_zone
        max_attempts = 50
        
        for _ in range(max_attempts):
            x = random.uniform(20, 140)
            y = random.uniform(20, 124)
            
            # Check if position is outside safe zone
            distance = math.sqrt((x - safe_x)**2 + (y - safe_y)**2)
            if distance > safe_radius + 10:  # Add buffer
                return x, y
        
        # Fallback: spawn at edge of screen
        edge_positions = [
            (20, random.uniform(20, 124)),
            (140, random.uniform(20, 124)),
            (random.uniform(20, 140), 20),
            (random.uniform(20, 140), 124)
        ]
        return random.choice(edge_positions)
    
    def update_asteroids(self, asteroids: List[AsteroidFragment], dt: float) -> None:
        """
        Update physics for all asteroids
        
        Args:
            asteroids: List of asteroids to update
            dt: Time delta in seconds
        """
        for asteroid in asteroids:
            asteroid.kinetic_body.update(dt)
    
    def get_total_points(self, asteroids: List[AsteroidFragment]) -> int:
        """Calculate total point value of all asteroids"""
        return sum(asteroid.point_value for asteroid in asteroids)
    
    def get_size_distribution(self, asteroids: List[AsteroidFragment]) -> Dict[int, int]:
        """Get distribution of asteroid sizes"""
        distribution = {1: 0, 2: 0, 3: 0}
        for asteroid in asteroids:
            distribution[asteroid.size] += 1
        return distribution
    
    def should_spawn_new_wave(self, asteroids: List[AsteroidFragment]) -> bool:
        """Check if all asteroids are destroyed (wave complete)"""
        return len(asteroids) == 0
    
    def calculate_wave_difficulty(self, wave_number: int) -> Dict[str, Any]:
        """
        Calculate difficulty parameters for a wave
        
        Args:
            wave_number: Current wave number (1-based)
            
        Returns:
            Dictionary with difficulty parameters
        """
        # Progressive difficulty
        base_asteroids = 4
        asteroids_per_wave = 2
        
        asteroid_count = min(base_asteroids + (wave_number - 1) * asteroids_per_wave, 12)
        
        # Increase speed with waves
        speed_multiplier = 1.0 + (wave_number - 1) * 0.1
        
        # Favor smaller asteroids in later waves
        size_weights = [
            [3, 3, 2, 2, 1],      # Wave 1-2
            [3, 2, 2, 1, 1],      # Wave 3-4
            [2, 2, 1, 1, 1],      # Wave 5-6
            [2, 1, 1, 1, 1],      # Wave 7+
        ]
        
        weight_index = min((wave_number - 1) // 2, len(size_weights) - 1)
        
        return {
            'asteroid_count': asteroid_count,
            'speed_multiplier': speed_multiplier,
            'size_weights': size_weights[weight_index]
        }


# Factory functions for common configurations
def create_classic_fracture_system() -> FractureSystem:
    """Create classic arcade fracture system"""
    return FractureSystem()


def create_hard_fracture_system() -> FractureSystem:
    """Create harder fracture system with more fragments"""
    system = FractureSystem()
    system.fragment_speed_range = (25.0, 60.0)  # Faster fragments
    return system
