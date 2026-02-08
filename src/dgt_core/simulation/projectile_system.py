"""
DGT Projectile System - ADR 130 Implementation
High-speed projectile system with circle-based collision detection

Supports kinetic projectiles, laser beams, and missile systems
Integrates with Rust collision detection for performance
"""

import math
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field
from loguru import logger

from .space_physics import SpaceShip


class ProjectileType(str, Enum):
    """Projectile type classifications"""
    KINETIC = "kinetic"         # Solid projectile
    LASER = "laser"             # Energy beam
    PLASMA = "plasma"           # Plasma bolt
    MISSILE = "missile"         # Guided missile
    PARTICLE = "particle"       # Particle beam


class ImpactType(str, Enum):
    """Impact type classifications"""
    HULL = "hull"               # Direct hull impact
    SHIELD = "shield"           # Shield impact
    GLANCING = "glancing"       # Glancing blow
    CRITICAL = "critical"       # Critical hit
    MISS = "miss"               # Complete miss


@dataclass
class Projectile:
    """Individual projectile with physics properties"""
    projectile_id: str
    owner_id: str
    projectile_type: ProjectileType
    
    # Position and velocity
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    
    # Properties
    damage: float
    range_remaining: float
    lifetime: float = 5.0
    age: float = 0.0
    
    # Visual properties
    color: Tuple[int, int, int] = (255, 255, 0)
    size: float = 2.0
    trail_particles: bool = True
    
    # Collision properties
    collision_radius: float = 2.0
    has_impacted: bool = False
    
    def update(self, dt: float) -> bool:
        """Update projectile position and lifetime"""
        # Update position
        self.x += self.velocity_x * dt * 60  # 60 FPS normalization
        self.y += self.velocity_y * dt * 60
        
        # Update age and range
        self.age += dt
        distance_traveled = math.sqrt((self.velocity_x * dt * 60)**2 + (self.velocity_y * dt * 60)**2)
        self.range_remaining -= distance_traveled
        
        # Check if projectile should expire
        return self.age < self.lifetime and self.range_remaining > 0 and not self.has_impacted
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position"""
        return (self.x, self.y)
    
    def get_velocity_magnitude(self) -> float:
        """Get velocity magnitude"""
        return math.sqrt(self.velocity_x**2 + self.velocity_y**2)


@dataclass
class ImpactResult:
    """Result of projectile impact"""
    projectile_id: str
    target_id: str
    impact_type: ImpactType
    damage_dealt: float
    impact_position: Tuple[float, float]
    kinetic_energy: float
    
    def __post_init__(self):
        """Calculate kinetic energy"""
        self.kinetic_energy = self.damage_dealt * 0.5  # Simplified KE calculation


class CollisionDetector:
    """High-speed circle-based collision detection"""
    
    def __init__(self):
        self.collision_checks = 0
        self.collision_hits = 0
        
    def check_projectile_ship_collision(self, projectile: Projectile, ship: SpaceShip) -> Optional[ImpactResult]:
        """Check collision between projectile and ship"""
        self.collision_checks += 1
        
        # Skip if projectile belongs to ship or already impacted
        if projectile.owner_id == ship.ship_id or projectile.has_impacted or ship.is_destroyed():
            return None
        
        # Calculate distance between centers
        dx = projectile.x - ship.x
        dy = projectile.y - ship.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check collision (ship radius + projectile radius)
        ship_radius = 15.0  # Default ship collision radius
        collision_distance = ship_radius + projectile.collision_radius
        
        if distance <= collision_distance:
            self.collision_hits += 1
            
            # Determine impact type
            impact_type = self._determine_impact_type(projectile, ship, distance)
            
            # Calculate damage
            damage_dealt = self._calculate_damage(projectile, ship, impact_type)
            
            return ImpactResult(
                projectile_id=projectile.projectile_id,
                target_id=ship.ship_id,
                impact_type=impact_type,
                damage_dealt=damage_dealt,
                impact_position=(projectile.x, projectile.y),
                kinetic_energy=0.0  # Will be calculated in __post_init__
            )
        
        return None
    
    def _determine_impact_type(self, projectile: Projectile, ship: SpaceShip, distance: float) -> ImpactType:
        """Determine type of impact"""
        # Check for shield impact
        if ship.shield_strength > 0:
            shield_radius = 20.0  # Shield collision radius
            if distance <= shield_radius:
                return ImpactType.SHIELD
        
        # Check for critical hit (center mass)
        if distance <= 5.0:
            return ImpactType.CRITICAL
        
        # Check for glancing blow (edge hit)
        ship_radius = 15.0
        if distance >= ship_radius * 0.8:
            return ImpactType.GLANCING
        
        # Default to hull impact
        return ImpactType.HULL
    
    def _calculate_damage(self, projectile: Projectile, ship: SpaceShip, impact_type: ImpactType) -> float:
        """Calculate damage based on impact type and projectile properties"""
        base_damage = projectile.damage
        
        # Apply impact type modifiers
        damage_multipliers = {
            ImpactType.HULL: 1.0,
            ImpactType.SHIELD: 0.7,  # Shields absorb 30% damage
            ImpactType.GLANCING: 0.5,  # Glancing blows deal 50% damage
            ImpactType.CRITICAL: 2.0,  # Critical hits deal double damage
            ImpactType.MISS: 0.0
        }
        
        damage = base_damage * damage_multipliers.get(impact_type, 1.0)
        
        # Apply projectile type modifiers
        if projectile.projectile_type == ProjectileType.LASER:
            # Lasers bypass shields partially
            if impact_type == ImpactType.SHIELD:
                damage = base_damage * 0.85  # Only 15% shield absorption
        elif projectile.projectile_type == ProjectileType.PLASMA:
            # Plasma has area effect
            damage *= 1.2
        elif projectile.projectile_type == ProjectileType.MISSILE:
            # Missiles have high damage but slow
            damage *= 1.5
        
        return max(0, damage)
    
    def get_collision_stats(self) -> Dict[str, Any]:
        """Get collision detection statistics"""
        hit_rate = (self.collision_hits / self.collision_checks * 100) if self.collision_checks > 0 else 0
        return {
            'collision_checks': self.collision_checks,
            'collision_hits': self.collision_hits,
            'hit_rate_percent': hit_rate
        }


class ProjectileSystem:
    """Main projectile management system"""
    
    def __init__(self, collision_detector: Optional[CollisionDetector] = None):
        self.projectiles: Dict[str, Projectile] = {}
        self.collision_detector = collision_detector or CollisionDetector()
        
        # Projectile ID counter
        self.projectile_counter = 0
        
        # Performance tracking
        self.projectiles_fired = 0
        self.projectiles_impacted = 0
        
        # Projectile templates
        self.projectile_templates = self._initialize_templates()
        
        logger.info("🚀 Projectile System initialized")
    
    def _initialize_templates(self) -> Dict[ProjectileType, Dict[str, Any]]:
        """Initialize projectile templates"""
        return {
            ProjectileType.KINETIC: {
                'damage': 10.0,
                'range': 400.0,
                'speed': 8.0,
                'color': (255, 255, 0),  # Yellow
                'size': 2.0,
                'collision_radius': 2.0
            },
            ProjectileType.LASER: {
                'damage': 15.0,
                'range': 600.0,
                'speed': 20.0,  # Lasers travel at light speed (scaled)
                'color': (255, 0, 0),  # Red
                'size': 1.0,
                'collision_radius': 1.0
            },
            ProjectileType.PLASMA: {
                'damage': 20.0,
                'range': 300.0,
                'speed': 6.0,
                'color': (255, 150, 0),  # Orange
                'size': 3.0,
                'collision_radius': 3.0
            },
            ProjectileType.MISSILE: {
                'damage': 30.0,
                'range': 500.0,
                'speed': 4.0,
                'color': (200, 200, 200),  # Silver
                'size': 4.0,
                'collision_radius': 4.0
            },
            ProjectileType.PARTICLE: {
                'damage': 8.0,
                'range': 350.0,
                'speed': 12.0,
                'color': (255, 0, 255),  # Magenta
                'size': 1.5,
                'collision_radius': 1.5
            }
        }
    
    def fire_projectile(self, owner: SpaceShip, target: Optional[SpaceShip] = None, 
                       projectile_type: ProjectileType = ProjectileType.KINETIC,
                       aim_offset: Tuple[float, float] = (0.0, 0.0)) -> Optional[str]:
        """Fire a projectile from a ship"""
        if not owner.can_fire(time.time()):
            return None
        
        # Get projectile template
        template = self.projectile_templates.get(projectile_type, self.projectile_templates[ProjectileType.KINETIC])
        
        # Generate projectile ID
        self.projectile_counter += 1
        projectile_id = f"proj_{owner.ship_id}_{self.projectile_counter}"
        
        # Calculate initial position (front of ship)
        spawn_distance = 20.0  # Spawn projectiles in front of ship
        spawn_x = owner.x + math.cos(math.radians(owner.heading)) * spawn_distance
        spawn_y = owner.y + math.sin(math.radians(owner.heading)) * spawn_distance
        
        # Calculate velocity towards target or straight ahead
        if target:
            # Aim at target with prediction
            dx = target.x - spawn_x
            dy = target.y - spawn_y
            distance = math.sqrt(dx**2 + dy**2)
            
            # Predict target position
            time_to_target = distance / template['speed']
            predicted_x = target.x + target.velocity_x * time_to_target * 0.5
            predicted_y = target.y + target.velocity_y * time_to_target * 0.5
            
            # Calculate velocity vector
            dx = predicted_x - spawn_x
            dy = predicted_y - spawn_y
        else:
            # Aim straight ahead
            dx = math.cos(math.radians(owner.heading))
            dy = math.sin(math.radians(owner.heading))
        
        # Normalize and apply speed
        length = math.sqrt(dx**2 + dy**2)
        if length > 0:
            velocity_x = (dx / length) * template['speed'] + owner.velocity_x
            velocity_y = (dy / length) * template['speed'] + owner.velocity_y
        else:
            velocity_x = owner.velocity_x
            velocity_y = owner.velocity_y
        
        # Apply aim offset
        velocity_x += aim_offset[0]
        velocity_y += aim_offset[1]
        
        # Create projectile
        projectile = Projectile(
            projectile_id=projectile_id,
            owner_id=owner.ship_id,
            projectile_type=projectile_type,
            x=spawn_x,
            y=spawn_y,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            damage=template['damage'],
            range_remaining=template['range'],
            color=template['color'],
            size=template['size'],
            collision_radius=template['collision_radius']
        )
        
        # Add to system
        self.projectiles[projectile_id] = projectile
        self.projectiles_fired += 1
        
        # Update ship fire time
        owner.last_fire_time = time.time()
        
        logger.debug(f"🚀 Projectile fired: {projectile_id} from {owner.ship_id}")
        return projectile_id
    
    def update(self, dt: float, ships: List[SpaceShip]) -> List[ImpactResult]:
        """Update all projectiles and check collisions"""
        impact_results = []
        
        # Update projectiles
        projectiles_to_remove = []
        for projectile_id, projectile in self.projectiles.items():
            # Update projectile physics
            if not projectile.update(dt):
                projectiles_to_remove.append(projectile_id)
                continue
            
            # Check collisions with ships
            for ship in ships:
                impact = self.collision_detector.check_projectile_ship_collision(projectile, ship)
                if impact:
                    # Apply damage to ship
                    ship.take_damage(impact.damage_dealt)
                    
                    # Mark projectile as impacted
                    projectile.has_impacted = True
                    projectiles_to_remove.append(projectile_id)
                    
                    # Record impact
                    impact_results.append(impact)
                    self.projectiles_impacted += 1
                    
                    logger.debug(f"🚀 Impact: {projectile.projectile_id} -> {ship.ship_id} for {impact.damage_dealt:.1f} damage")
                    break
        
        # Remove expired/impacted projectiles
        for projectile_id in projectiles_to_remove:
            if projectile_id in self.projectiles:
                del self.projectiles[projectile_id]
        
        return impact_results
    
    def get_active_projectiles(self) -> List[Projectile]:
        """Get list of active projectiles"""
        return list(self.projectiles.values())
    
    def get_projectile_count(self) -> int:
        """Get number of active projectiles"""
        return len(self.projectiles)
    
    def clear_all_projectiles(self):
        """Clear all projectiles"""
        self.projectiles.clear()
        logger.debug("🚀 All projectiles cleared")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get projectile system statistics"""
        collision_stats = self.collision_detector.get_collision_stats()
        
        return {
            'active_projectiles': len(self.projectiles),
            'projectiles_fired': self.projectiles_fired,
            'projectiles_impacted': self.projectiles_impacted,
            'accuracy_rate': (self.projectiles_impacted / self.projectiles_fired * 100) if self.projectiles_fired > 0 else 0,
            'collision_stats': collision_stats
        }


# Global projectile system instance
projectile_system = None

def initialize_projectile_system() -> ProjectileSystem:
    """Initialize global projectile system"""
    global projectile_system
    projectile_system = ProjectileSystem()
    logger.info("🚀 Global Projectile System initialized")
    return projectile_system
