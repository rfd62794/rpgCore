"""
Space Voyager Engine - Physics Runner for Star-Fleet
ADR 130: Newtonian Physics Engine Integration
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from .space_physics import SpaceVoyagerEngine, CombatIntent
from .ship_genetics import ShipGenome, HullType, WeaponType, EngineType


@dataclass
class SpaceShip:
    """Space ship entity with physics and genetics"""
    ship_id: str
    genome: ShipGenome
    x: float = 0.0
    y: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    heading: float = 0.0
    health: float = 100.0
    max_health: float = 100.0
    armor: float = 50.0
    mass: float = 1.0
    max_thrust: float = 10.0
    weapon_damage: float = 10.0
    fire_rate: float = 1.0
    
    def __post_init__(self):
        # Map genetic traits to physics properties
        self._map_genetics_to_physics()
    
    def _map_genetics_to_physics(self):
        """Map ShipGenome traits to physics properties"""
        # Hull systems affect durability
        self.armor = 50.0 * self.genome.plating_density
        self.max_health = 100.0 * self.genome.structural_integrity
        self.health = self.max_health
        self.mass = 1.0 + (self.genome.plating_density * 0.5)
        
        # Engine systems affect movement
        self.max_thrust = 10.0 * self.genome.thruster_output
        
        # Weapon systems affect combat
        self.weapon_damage = 10.0 * self.genome.weapon_damage
        self.fire_rate = 1.0 * self.genome.fire_rate
    
    def apply_damage(self, damage: float) -> float:
        """Apply damage and return actual damage dealt"""
        # Armor reduces damage
        actual_damage = max(1.0, damage - (self.armor * 0.1))
        self.health = max(0.0, self.health - actual_damage)
        return actual_damage
    
    def is_alive(self) -> bool:
        """Check if ship is still alive"""
        return self.health > 0.0
    
    def get_combat_rating(self) -> float:
        """Calculate overall combat rating"""
        damage_potential = self.weapon_damage * self.fire_rate
        survivability = (self.health / self.max_health) * self.armor
        mobility = self.max_thrust / self.mass
        
        return (damage_potential * 0.5) + (survivability * 0.3) + (mobility * 0.2)


class SpaceVoyagerEngineRunner:
    """Physics runner for Star-Fleet space combat"""
    
    def __init__(self, fleet_size: int = 10):
        self.fleet_size = fleet_size
        self.physics_engine = SpaceVoyagerEngine()
        self.ships: Dict[str, SpaceShip] = {}
        self.simulation_time: float = 0.0
        self.dt: float = 0.016  # 60 FPS
        
        logger.info(f"🚀 SpaceVoyagerEngineRunner initialized: fleet_size={fleet_size}")
    
    def create_fleet_from_genomes(self, genomes: List[ShipGenome]) -> Dict[str, SpaceShip]:
        """Create fleet from list of genomes"""
        fleet = {}
        
        for i, genome in enumerate(genomes):
            ship_id = f"ship_{i:03d}"
            ship = SpaceShip(
                ship_id=ship_id,
                genome=genome,
                x=float(i * 50),  # Spread out ships
                y=float(100 + (i % 2) * 50)
            )
            fleet[ship_id] = ship
        
        self.ships = fleet
        logger.info(f"🚀 Created fleet: {len(fleet)} ships")
        return fleet
    
    def update_simulation(self, target_assignments: Dict[str, Optional[str]], 
                         command_confidence: float = 1.0) -> Dict[str, Any]:
        """Update one frame of simulation"""
        frame_results = {
            'ships_updated': 0,
            'damage_events': [],
            'deaths': [],
            'simulation_time': self.simulation_time
        }
        
        # Update each ship
        for ship_id, ship in self.ships.items():
            if not ship.is_alive():
                continue
            
            # Get target position from assignment
            target_pos = None
            target_ship_id = target_assignments.get(ship_id)
            
            if target_ship_id and target_ship_id in self.ships:
                target_ship = self.ships[target_ship_id]
                if target_ship.is_alive():
                    target_pos = (target_ship.x, target_ship.y)
            
            # Update physics
            update_data = self.physics_engine.update(
                ship, target_pos, command_confidence, self.dt
            )
            
            frame_results['ships_updated'] += 1
            
            # Handle combat if locked on target
            if (update_data.get('intent_state') == CombatIntent.LOCKED and 
                target_ship_id and target_ship_id in self.ships):
                
                target_ship = self.ships[target_ship_id]
                if target_ship.is_alive():
                    # Apply damage based on fire rate
                    if random.random() < (ship.fire_rate * self.dt):
                        damage = ship.apply_damage_to_target(target_ship)
                        frame_results['damage_events'].append({
                            'attacker': ship_id,
                            'target': target_ship_id,
                            'damage': damage
                        })
                        
                        # Check for death
                        if not target_ship.is_alive():
                            frame_results['deaths'].append(target_ship_id)
        
        # Update simulation time
        self.simulation_time += self.dt
        
        return frame_results
    
    def apply_damage_to_target(self, target: SpaceShip) -> float:
        """Apply damage to target ship"""
        base_damage = self.weapon_damage
        
        # Add some randomness
        damage_variance = 0.8 + (random.random() * 0.4)  # 80% to 120%
        actual_damage = base_damage * damage_variance
        
        return target.apply_damage(actual_damage)
    
    def get_fleet_status(self) -> Dict[str, Any]:
        """Get current fleet status"""
        alive_ships = [s for s in self.ships.values() if s.is_alive()]
        dead_ships = [s for s in self.ships.values() if not s.is_alive()]
        
        if not alive_ships:
            return {
                'alive_count': 0,
                'dead_count': len(dead_ships),
                'total_health': 0.0,
                'avg_health': 0.0,
                'fleet_center': (0.0, 0.0)
            }
        
        total_health = sum(s.health for s in alive_ships)
        avg_health = total_health / len(alive_ships)
        
        # Calculate fleet center
        center_x = sum(s.x for s in alive_ships) / len(alive_ships)
        center_y = sum(s.y for s in alive_ships) / len(alive_ships)
        
        return {
            'alive_count': len(alive_ships),
            'dead_count': len(dead_ships),
            'total_health': total_health,
            'avg_health': avg_health,
            'fleet_center': (center_x, center_y)
        }
    
    def reset_simulation(self):
        """Reset simulation state"""
        self.simulation_time = 0.0
        
        # Reset all ships to full health
        for ship in self.ships.values():
            ship.health = ship.max_health
            ship.velocity_x = 0.0
            ship.velocity_y = 0.0
        
        logger.info("🚀 Simulation reset")
    
    def get_ship_positions(self) -> Dict[str, Tuple[float, float]]:
        """Get all ship positions"""
        return {
            ship_id: (ship.x, ship.y) 
            for ship_id, ship in self.ships.items()
            if ship.is_alive()
        }


# Factory function for easy initialization
def create_space_engine_runner(fleet_size: int = 10) -> SpaceVoyagerEngineRunner:
    """Create a SpaceVoyagerEngineRunner instance"""
    return SpaceVoyagerEngineRunner(fleet_size)


# Add missing import for random
import random
