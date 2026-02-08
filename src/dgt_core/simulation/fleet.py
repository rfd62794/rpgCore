"""
DGT Fleet Management System - ADR 132 Implementation
Persistent fleet service with team-based combat coordination

Manages groups of ships, team assignments, and fleet-level tactical decisions
Supports modular hardpoints and genetic ship lineage tracking
"""

import uuid
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field
from loguru import logger

from .space_physics import SpaceShip, SpaceVoyagerEngine
from .ship_genetics import ShipGenome, ship_genetic_registry


class TeamAffiliation(str, Enum):
    """Team affiliation for fleet combat"""
    NEUTRAL = "neutral"
    ALPHA = "alpha"        # Blue team
    BETA = "beta"          # Red team
    GAMMA = "gamma"        # Green team
    PIRATE = "pirate"      # Hostile faction


class ShipRole(str, Enum):
    """Combat role classification"""
    INTERCEPTOR = "interceptor"     # Fast attack craft
    FIGHTER = "fighter"             # Balanced combat
    BOMBER = "bomber"              # Heavy assault
    DREADNOUGHT = "dreadnought"    # Capital ship
    SUPPORT = "support"            # Repair/logistics


class HardpointType(str, Enum):
    """Weapon hardpoint types"""
    LASER_CANNON = "laser_cannon"
    PLASMA_TORPEDO = "plasma_torpedo"
    MISSILE_LAUNCHER = "missile_launcher"
    RAILGUN = "railgun"
    POINT_DEFENSE = "point_defense"


@dataclass
class WeaponHardpoint:
    """Weapon hardpoint configuration"""
    hardpoint_id: str
    hardpoint_type: HardpointType
    position_offset: Tuple[float, float]  # Offset from ship center
    firing_arc: float = 360.0  # Degrees of firing arc
    damage_modifier: float = 1.0
    fire_rate_modifier: float = 1.0
    
    def can_fire_at_target(self, ship_heading: float, target_angle: float) -> bool:
        """Check if hardpoint can fire at target angle"""
        angle_diff = abs((target_angle - ship_heading + 180) % 360 - 180)
        return angle_diff <= (self.firing_arc / 2)


@dataclass
class FleetShip:
    """Individual ship within fleet with enhanced properties"""
    ship_id: str
    ship_name: str
    team: TeamAffiliation
    role: ShipRole
    
    # Core ship properties
    ship: SpaceShip
    genome: ShipGenome
    
    # Fleet-specific properties
    hardpoints: List[WeaponHardpoint] = field(default_factory=list)
    combat_effectiveness: float = 1.0
    fleet_position: int = 0  # Position in fleet formation
    
    # State tracking
    last_combat_action: float = 0.0
    enemies_destroyed: int = 0
    damage_dealt: float = 0.0
    
    def __post_init__(self):
        """Initialize hardpoints based on genome"""
        self._generate_hardpoints()
    
    def _generate_hardpoints(self):
        """Generate weapon hardpoints based on ship role and genome"""
        self.hardpoints.clear()
        
        if self.role == ShipRole.INTERCEPTOR:
            # Fast attack - forward-facing weapons
            self.hardpoints.append(WeaponHardpoint(
                hardpoint_id=f"{self.ship_id}_laser_1",
                hardpoint_type=HardpointType.LASER_CANNON,
                position_offset=(10, 0),
                firing_arc=30.0,
                damage_modifier=1.2,
                fire_rate_modifier=1.5
            ))
        elif self.role == ShipRole.FIGHTER:
            # Balanced - multiple weapons
            self.hardpoints.append(WeaponHardpoint(
                hardpoint_id=f"{self.ship_id}_laser_1",
                hardpoint_type=HardpointType.LASER_CANNON,
                position_offset=(8, -3),
                firing_arc=45.0
            ))
            self.hardpoints.append(WeaponHardpoint(
                hardpoint_id=f"{self.ship_id}_laser_2",
                hardpoint_type=HardpointType.LASER_CANNON,
                position_offset=(8, 3),
                firing_arc=45.0
            ))
        elif self.role == ShipRole.DREADNOUGHT:
            # Capital ship - multiple weapon systems
            self.hardpoints.append(WeaponHardpoint(
                hardpoint_id=f"{self.ship_id}_railgun_1",
                hardpoint_type=HardpointType.RAILGUN,
                position_offset=(15, -8),
                firing_arc=60.0,
                damage_modifier=2.0,
                fire_rate_modifier=0.5
            ))
            self.hardpoints.append(WeaponHardpoint(
                hardpoint_id=f"{self.ship_id}_railgun_2",
                hardpoint_type=HardpointType.RAILGUN,
                position_offset=(15, 8),
                firing_arc=60.0,
                damage_modifier=2.0,
                fire_rate_modifier=0.5
            ))
            self.hardpoints.append(WeaponHardpoint(
                hardpoint_id=f"{self.ship_id}_pd_1",
                hardpoint_type=HardpointType.POINT_DEFENSE,
                position_offset=(-5, -10),
                firing_arc=180.0,
                damage_modifier=0.5,
                fire_rate_modifier=3.0
            ))
            self.hardpoints.append(WeaponHardpoint(
                hardpoint_id=f"{self.ship_id}_pd_2",
                hardpoint_type=HardpointType.POINT_DEFENSE,
                position_offset=(-5, 10),
                firing_arc=180.0,
                damage_modifier=0.5,
                fire_rate_modifier=3.0
            ))
    
    def get_active_hardpoints(self) -> List[WeaponHardpoint]:
        """Get hardpoints that can fire"""
        return [hp for hp in self.hardpoints if self.ship.can_fire(time.time())]
    
    def get_fleet_value(self) -> float:
        """Calculate strategic value to fleet"""
        base_value = {
            ShipRole.INTERCEPTOR: 1.0,
            ShipRole.FIGHTER: 2.0,
            ShipRole.BOMBER: 3.0,
            ShipRole.DREADNOUGHT: 10.0,
            ShipRole.SUPPORT: 1.5
        }.get(self.role, 1.0)
        
        # Modify by combat effectiveness
        return base_value * self.combat_effectiveness
    
    def update_combat_stats(self, damage_dealt: float, enemy_destroyed: bool = False):
        """Update combat performance statistics"""
        self.last_combat_action = time.time()
        self.damage_dealt += damage_dealt
        if enemy_destroyed:
            self.enemies_destroyed += 1
            self.combat_effectiveness = min(2.0, self.combat_effectiveness + 0.1)


class FleetFormation:
    """Fleet formation pattern and positioning"""
    
    def __init__(self, formation_type: str = "line"):
        self.formation_type = formation_type
        self.spacing = 100.0  # Distance between ships
        
    def get_position(self, index: int, total_ships: int, center_x: float, center_y: float) -> Tuple[float, float]:
        """Get position for ship in formation"""
        if self.formation_type == "line":
            # Horizontal line
            x = center_x - (total_ships - 1) * self.spacing / 2 + index * self.spacing
            y = center_y
        elif self.formation_type == "wedge":
            # V-shaped wedge formation
            if index == 0:  # Lead ship
                x, y = center_x, center_y - self.spacing
            else:
                side = 1 if index % 2 == 0 else -1
                offset = (index + 1) // 2
                x = center_x + side * offset * self.spacing
                y = center_y + offset * self.spacing / 2
        elif self.formation_type == "circle":
            # Circular formation
            angle = (2 * math.pi * index) / total_ships
            radius = self.spacing
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
        else:  # Default to line
            x = center_x
            y = center_y + index * self.spacing
        
        return (x, y)


class FleetManager:
    """Manages persistent fleet service and team coordination"""
    
    def __init__(self):
        self.fleets: Dict[str, List[FleetShip]] = {}  # team_id -> ships
        self.all_ships: Dict[str, FleetShip] = {}  # ship_id -> FleetShip
        self.team_relations: Dict[Tuple[TeamAffiliation, TeamAffiliation], bool] = {}
        
        # Fleet statistics
        self.total_battles_fought = 0
        self.total_ships_lost = 0
        self.total_enemies_destroyed = 0
        
        # Initialize team relations (default: hostile to different teams)
        self._initialize_team_relations()
        
        logger.info("🚀 Fleet Manager initialized")
    
    def _initialize_team_relations(self):
        """Initialize default team relationships"""
        teams = list(TeamAffiliation)
        for team1 in teams:
            for team2 in teams:
                if team1 != team2:
                    # Different teams are hostile by default
                    self.team_relations[(team1, team2)] = True
                else:
                    # Same team is friendly
                    self.team_relations[(team1, team2)] = False
    
    def set_team_relation(self, team1: TeamAffiliation, team2: TeamAffiliation, hostile: bool):
        """Set relationship between teams"""
        self.team_relations[(team1, team2)] = hostile
        self.team_relations[(team2, team1)] = hostile  # Symmetric relationship
        logger.debug(f"🚀 Set {team1.value} vs {team2.value}: {'Hostile' if hostile else 'Friendly'}")
    
    def are_hostile(self, team1: TeamAffiliation, team2: TeamAffiliation) -> bool:
        """Check if two teams are hostile"""
        return self.team_relations.get((team1, team2), True)
    
    def create_fleet_ship(self, ship_name: str, team: TeamAffiliation, role: ShipRole,
                         x: float, y: float, heading: float = 0.0,
                         genome: Optional[ShipGenome] = None) -> FleetShip:
        """Create new ship and add to fleet"""
        ship_id = str(uuid.uuid4())
        
        # Generate or use provided genome
        if genome is None:
            genome = self._generate_genome_for_role(role)
        
        # Create base ship
        base_ship = SpaceShip(
            ship_id=ship_id,
            x=x, y=y,
            heading=heading,
            hull_integrity=100.0 + genome.structural_integrity * 50,
            shield_strength=50.0 + genome.shield_frequency * 25,
            weapon_range=300.0 + genome.targeting_system * 50,
            weapon_damage=10.0 * genome.weapon_damage,
            fire_rate=1.0 * genome.fire_rate
        )
        base_ship.physics_engine = SpaceVoyagerEngine(
            thrust_power=0.3 + genome.thruster_output * 0.2,
            rotation_speed=3.0 + genome.initiative * 2.0
        )
        
        # Create fleet ship
        fleet_ship = FleetShip(
            ship_id=ship_id,
            ship_name=ship_name,
            team=team,
            role=role,
            ship=base_ship,
            genome=genome
        )
        
        # Add to fleets
        if team.value not in self.fleets:
            self.fleets[team.value] = []
        
        self.fleets[team.value].append(fleet_ship)
        self.all_ships[ship_id] = fleet_ship
        
        logger.info(f"🚀 Created fleet ship: {ship_name} ({team.value}/{role.value})")
        return fleet_ship
    
    def _generate_genome_for_role(self, role: ShipRole) -> ShipGenome:
        """Generate appropriate genome for ship role"""
        if role == ShipRole.INTERCEPTOR:
            return ship_genetic_registry.generate_random_ship("light_fighter")
        elif role == ShipRole.FIGHTER:
            return ship_genetic_registry.generate_random_ship("medium_cruiser")
        elif role == ShipRole.DREADNOUGHT:
            return ship_genetic_registry.generate_random_ship("heavy_battleship")
        else:
            return ship_genetic_registry.generate_random_ship()
    
    def create_fleet_formation(self, team: TeamAffiliation, formation: FleetFormation,
                              center_x: float, center_y: float, roles: List[ShipRole],
                              ship_names: Optional[List[str]] = None) -> List[FleetShip]:
        """Create fleet in formation"""
        ships = []
        
        for i, role in enumerate(roles):
            x, y = formation.get_position(i, len(roles), center_x, center_y)
            ship_name = ship_names[i] if ship_names and i < len(ship_names) else f"{team.value.capitalize()}_Ship_{i+1}"
            
            ship = self.create_fleet_ship(ship_name, team, role, x, y)
            ship.fleet_position = i
            ships.append(ship)
        
        logger.info(f"🚀 Created {team.value} fleet formation: {len(ships)} ships")
        return ships
    
    def get_team_ships(self, team: TeamAffiliation) -> List[FleetShip]:
        """Get all ships for a team"""
        return [ship for ship in self.all_ships.values() if ship.team == team and not ship.ship.is_destroyed()]
    
    def get_enemy_ships(self, ship: FleetShip) -> List[FleetShip]:
        """Get all enemy ships for a given ship"""
        enemies = []
        for other_ship in self.all_ships.values():
            if (other_ship.ship_id != ship.ship_id and 
                not other_ship.ship.is_destroyed() and
                self.are_hostile(ship.team, other_ship.team)):
                enemies.append(other_ship)
        return enemies
    
    def get_fleet_statistics(self) -> Dict[str, Any]:
        """Get comprehensive fleet statistics"""
        stats = {
            'total_ships': len(self.all_ships),
            'active_ships': len([s for s in self.all_ships.values() if not s.ship.is_destroyed()]),
            'teams': {},
            'total_battles': self.total_battles_fought,
            'total_losses': self.total_ships_lost,
            'total_kills': self.total_enemies_destroyed
        }
        
        for team in TeamAffiliation:
            team_ships = self.get_team_ships(team)
            stats['teams'][team.value] = {
                'count': len(team_ships),
                'total_fleet_value': sum(ship.get_fleet_value() for ship in team_ships),
                'average_effectiveness': sum(ship.combat_effectiveness for ship in team_ships) / len(team_ships) if team_ships else 0
            }
        
        return stats
    
    def update_fleet_state(self):
        """Update fleet state and remove destroyed ships"""
        destroyed_ships = []
        
        for ship_id, fleet_ship in self.all_ships.items():
            if fleet_ship.ship.is_destroyed():
                destroyed_ships.append(ship_id)
                self.total_ships_lost += 1
                logger.info(f"🚀 Fleet ship lost: {fleet_ship.ship_name}")
        
        # Remove destroyed ships
        for ship_id in destroyed_ships:
            fleet_ship = self.all_ships.pop(ship_id, None)
            if fleet_ship:
                team_fleet = self.fleets.get(fleet_ship.team.value, [])
                if fleet_ship in team_fleet:
                    team_fleet.remove(fleet_ship)
    
    def get_combat_log(self) -> List[str]:
        """Get recent combat log entries"""
        log_entries = []
        
        for fleet_ship in self.all_ships.values():
            if fleet_ship.last_combat_action > 0:
                time_since = time.time() - fleet_ship.last_combat_action
                if time_since < 10.0:  # Recent activity
                    entry = f"{fleet_ship.ship_name}: {fleet_ship.damage_dealt:.1f} damage, {fleet_ship.enemies_destroyed} kills"
                    log_entries.append(entry)
        
        return log_entries


# Global fleet manager instance
fleet_manager = None

def initialize_fleet_manager() -> FleetManager:
    """Initialize global fleet manager"""
    global fleet_manager
    fleet_manager = FleetManager()
    logger.info("🚀 Global Fleet Manager initialized")
    return fleet_manager
