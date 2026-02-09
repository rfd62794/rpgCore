"""
DGT Space Physics - ADR 130 Implementation
Real-time Newtonian physics engine for space combat simulation

Refactored for Component-Lite Architecture (ADR 168)
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from src.dgt_core.kernel.components import PhysicsComponent

class CombatIntent(str, Enum):
    """AI combat intent states"""
    PURSUIT = "pursuit"           # Aggressive target chase
    STRAFE = "strafe"             # Broadside maneuvering
    RETREAT = "retreat"           # Tactical withdrawal
    EVADE = "evade"               # Defensive dodging
    LOCKED = "locked"             # Weapon lock achieved


@dataclass
class PIDController:
    """PID controller for smooth rotation and movement"""
    kp: float = 1.0
    ki: float = 0.0
    kd: float = 0.0
    integral: float = 0.0
    previous_error: float = 0.0
    
    def update(self, error: float, dt: float) -> float:
        """Update PID controller and return control output"""
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error * dt
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.previous_error) / dt if dt > 0 else 0.0
        d_term = self.kd * derivative
        
        self.previous_error = error
        
        return p_term + i_term + d_term
    
    def reset(self):
        """Reset PID controller state"""
        self.integral = 0.0
        self.previous_error = 0.0


class SpaceVoyagerEngine:
    """Newtonian physics engine with PID-controlled navigation"""
    
    def __init__(self, thrust_power: float = 0.5, rotation_speed: float = 5.0):
        self.thrust_power = thrust_power
        self.rotation_speed = rotation_speed
        
        # PID controllers for smooth movement
        self.rotation_pid = PIDController(kp=2.0, ki=0.1, kd=0.5)
        self.thrust_pid = PIDController(kp=1.0, ki=0.0, kd=0.2)
        
        # Physics parameters
        self.max_velocity = 10.0
        self.max_angular_velocity = 15.0
        
        # Target tracking
        self.target_position: Optional[Tuple[float, float]] = None
        self.command_confidence: float = 1.0
        
        logger.debug(f"🚀 SpaceVoyagerEngine initialized (Component-Lite)")
    
    def update(self, physics: PhysicsComponent, dt: float = 0.016) -> Dict[str, Any]:
        """Update physics component with Newtonian mechanics"""
        
        # 1. Apply Physics (Inertia & Drag)
        self._apply_physics(physics, dt)
        
        return {
            "x": physics.x,
            "y": physics.y,
            "vx": physics.velocity_x,
            "vy": physics.velocity_y
        }
    
    def _apply_physics(self, physics: PhysicsComponent, dt: float):
        """Apply Newtonian physics and constraints"""
        
        # Apply manual thrust (if set via thrust_input_x/y)
        # F = ma -> a = F/m
        
        if physics.thrust_input_x != 0 or physics.thrust_input_y != 0:
            accel_x = (physics.thrust_input_x * physics.max_thrust) / physics.mass
            accel_y = (physics.thrust_input_y * physics.max_thrust) / physics.mass
            
            physics.velocity_x += accel_x * dt
            physics.velocity_y += accel_y * dt
            
            # Reset specialized input (impulse-like) if needed, 
            # but usually the input persists until changed. 
            # We assume 'thrust_input' is the current throttle state.
        
        # Apply drag (space friction simulation)
        physics.velocity_x *= physics.drag_coefficient
        physics.velocity_y *= physics.drag_coefficient
        
        # Limit maximum velocity
        speed = math.sqrt(physics.velocity_x**2 + physics.velocity_y**2)
        if speed > self.max_velocity:
            scale = self.max_velocity / speed
            physics.velocity_x *= scale
            physics.velocity_y *= scale
        
        # Update position based on velocity
        # Note: 60 is a normalization factor from original code, kept for consistency
        physics.x += physics.velocity_x * dt * 60  
        physics.y += physics.velocity_y * dt * 60

# Global physics engine instance
space_physics_engine = None

def initialize_space_physics() -> SpaceVoyagerEngine:
    """Initialize global space physics engine"""
    global space_physics_engine
    space_physics_engine = SpaceVoyagerEngine()
    logger.info("🚀 Space Physics Engine initialized")
    return space_physics_engine


import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, validator
from loguru import logger


class CombatIntent(str, Enum):
    """AI combat intent states"""
    PURSUIT = "pursuit"           # Aggressive target chase
    STRAFE = "strafe"             # Broadside maneuvering
    RETREAT = "retreat"           # Tactical withdrawal
    EVADE = "evade"               # Defensive dodging
    LOCKED = "locked"             # Weapon lock achieved


@dataclass
class PhysicsVector:
    """2D physics vector with velocity and heading"""
    x: float
    y: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    heading: float = 0.0  # In degrees
    
    def get_speed(self) -> float:
        """Calculate current speed magnitude"""
        return math.sqrt(self.velocity_x**2 + self.velocity_y**2)
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position"""
        return (self.x, self.y)
    
    def get_velocity_vector(self) -> Tuple[float, float]:
        """Get velocity vector"""
        return (self.velocity_x, self.velocity_y)


class PIDController:
    """PID controller for smooth rotation and movement"""
    
    def __init__(self, kp: float = 1.0, ki: float = 0.0, kd: float = 0.0):
        self.kp = kp  # Proportional gain
        self.ki = ki  # Integral gain
        self.kd = kd  # Derivative gain
        
        self.integral = 0.0
        self.previous_error = 0.0
    
    def update(self, error: float, dt: float) -> float:
        """Update PID controller and return control output"""
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error * dt
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.previous_error) / dt if dt > 0 else 0.0
        d_term = self.kd * derivative
        
        self.previous_error = error
        
        return p_term + i_term + d_term
    
    def reset(self):
        """Reset PID controller state"""
        self.integral = 0.0
        self.previous_error = 0.0


class SpaceVoyagerEngine:
    """Newtonian physics engine with PID-controlled navigation"""
    
    def __init__(self, thrust_power: float = 0.5, rotation_speed: float = 5.0):
        self.thrust_power = thrust_power
        self.rotation_speed = rotation_speed
        
        # PID controllers for smooth movement
        self.rotation_pid = PIDController(kp=2.0, ki=0.1, kd=0.5)
        self.thrust_pid = PIDController(kp=1.0, ki=0.0, kd=0.2)
        
        # Physics parameters
        self.drag_coefficient = 0.98  # Space drag simulation
        self.max_velocity = 10.0
        self.max_angular_velocity = 15.0
        
        # Target tracking
        self.target_id: Optional[str] = None
        self.target_position: Optional[Tuple[float, float]] = None
        
        # Command confidence for smooth targeting
        self.command_confidence: float = 1.0
        self.confidence_decay_rate: float = 0.1  # Confidence decay per second
        self.min_confidence_threshold: float = 0.3  # Minimum confidence to follow commands
        
        logger.debug(f"🚀 SpaceVoyagerEngine initialized: thrust={thrust_power}, rotation={rotation_speed}")
    
    def update(self, ship: 'SpaceShip', target_pos: Optional[Tuple[float, float]] = None, 
               command_confidence: float = 1.0, dt: float = 0.016) -> Dict[str, Any]:
        """Update ship physics with Newtonian mechanics and command confidence"""
        # Update command confidence with decay
        self.command_confidence = max(
            self.min_confidence_threshold,
            command_confidence * (1 - self.confidence_decay_rate * dt)
        )
        
        update_data = {
            'thrust_applied': False,
            'rotation_applied': False,
            'target_locked': False,
            'intent_state': CombatIntent.PURSUIT,
            'command_confidence': self.command_confidence
        }
        
        # Update target position only if confidence is sufficient
        if target_pos and self.command_confidence >= self.min_confidence_threshold:
            self.target_position = target_pos
            update_data['target_locked'] = True
        
        # 1. Automated Target Locking and Rotation
        if self.target_position:
            angle_to_target = self._calculate_angle_to_target(ship, self.target_position)
            rotation_output = self._apply_rotation_control(ship, angle_to_target, dt)
            
            update_data['rotation_applied'] = True
            update_data['target_angle'] = angle_to_target
            
            # Check if locked (within threshold)
            angle_diff = abs((angle_to_target - ship.heading + 180) % 360 - 180)
            if angle_diff < 5.0:  # 5-degree threshold
                update_data['intent_state'] = CombatIntent.LOCKED
        
        # 2. Apply Newtonian Thrust (confidence-weighted)
        if self.target_position and update_data['intent_state'] == CombatIntent.LOCKED:
            # Scale thrust output by command confidence
            thrust_confidence_factor = self.command_confidence
            thrust_output = self._apply_thrust_control(ship, self.target_position, dt * thrust_confidence_factor)
            update_data['thrust_applied'] = True
            update_data['thrust_confidence'] = thrust_confidence_factor
        
        # 3. Apply Physics
        self._apply_physics(ship, dt)
        
        # 4. Update Intent State based on hull integrity
        update_data['intent_state'] = self._determine_combat_intent(ship)
        
        return update_data
    
    def _calculate_angle_to_target(self, ship: 'SpaceShip', target_pos: Tuple[float, float]) -> float:
        """Calculate angle from ship to target"""
        dx = target_pos[0] - ship.x
        dy = target_pos[1] - ship.y
        return math.degrees(math.atan2(dy, dx))
    
    def _apply_rotation_control(self, ship: 'SpaceShip', target_angle: float, dt: float) -> float:
        """Apply PID-controlled rotation towards target with confidence weighting"""
        # Calculate shortest angular path
        angle_diff = (target_angle - ship.heading + 180) % 360 - 180
        
        # Apply confidence weighting to rotation responsiveness
        confidence_weight = 0.3 + (self.command_confidence * 0.7)  # Range: 0.3 to 1.0
        
        # PID control for smooth rotation
        rotation_output = self.rotation_pid.update(angle_diff, dt) * confidence_weight
        
        # Apply rotation with limits
        rotation_change = max(-self.max_angular_velocity, 
                            min(self.max_angular_velocity, rotation_output))
        ship.heading += rotation_change * dt
        
        # Normalize heading to 0-360
        ship.heading = ship.heading % 360
        
        return rotation_output
    
    def _apply_thrust_control(self, ship: 'SpaceShip', target_pos: Tuple[float, float], dt: float) -> float:
        """Apply thrust based on distance to target"""
        # Calculate distance to target
        dx = target_pos[0] - ship.x
        dy = target_pos[1] - ship.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # PID control for thrust (distance-based)
        thrust_output = self.thrust_pid.update(distance, dt)
        
        # Apply thrust in current heading direction
        rad = math.radians(ship.heading)
        thrust_force = min(self.thrust_power, max(0, thrust_output))
        
        ship.velocity_x += math.cos(rad) * thrust_force
        ship.velocity_y += math.sin(rad) * thrust_force
        
        return thrust_force
    
    def _apply_physics(self, ship: 'SpaceShip', dt: float):
        """Apply Newtonian physics and constraints"""
        
        # Apply manual thrust (if set)
        if hasattr(ship, 'thrust_x') and hasattr(ship, 'thrust_y'):
            # Thrust is assumed to be normalized (-1.0 to 1.0) scaled by max_thrust
            # F = ma -> a = F/m
            # We treat thrust_x/y as the FORCE fraction.
            # Actual Force = input * max_thrust
            
            accel_x = (ship.thrust_x * ship.max_thrust) / ship.mass
            accel_y = (ship.thrust_y * ship.max_thrust) / ship.mass
            
            ship.velocity_x += accel_x * dt
            ship.velocity_y += accel_y * dt
            
            # Reset thrust after application (impulse-like for this frame)
            # Or keep it? Usually AI sets it every frame.
            # Let's NOT reset it, assuming the AI/Controller sets it continuously.
        
        # Apply drag (space friction simulation)
        ship.velocity_x *= self.drag_coefficient
        ship.velocity_y *= self.drag_coefficient
        
        # Limit maximum velocity
        speed = ship.get_speed()
        if speed > self.max_velocity:
            scale = self.max_velocity / speed
            ship.velocity_x *= scale
            ship.velocity_y *= scale
        
        # Update position based on velocity
        ship.x += ship.velocity_x * dt * 60  # 60 FPS normalization
        ship.y += ship.velocity_y * dt * 60
    
    def _determine_combat_intent(self, ship: 'SpaceShip') -> CombatIntent:
        """Determine combat intent based on ship state"""
        hull_integrity = getattr(ship, 'hull_integrity', 100.0)
        
        if hull_integrity > 75.0:
            return CombatIntent.PURSUIT
        elif hull_integrity > 50.0:
            return CombatIntent.STRAFE
        elif hull_integrity > 25.0:
            return CombatIntent.EVADE
        else:
            return CombatIntent.RETREAT
    
    def set_target(self, target_id: str, target_position: Tuple[float, float]):
        """Set target for automated tracking"""
        self.target_id = target_id
        self.target_position = target_position
        logger.debug(f"🚀 Target set: {target_id} at {target_position}")
    
    def clear_target(self):
        """Clear current target"""
        self.target_id = None
        self.target_position = None
        self.rotation_pid.reset()
        self.thrust_pid.reset()
        logger.debug("🚀 Target cleared")


@dataclass
class SpaceShip:
    """Space ship with physics properties"""
    ship_id: str
    x: float
    y: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    heading: float = 0.0
    hull_integrity: float = 100.0
    shield_strength: float = 50.0
    
    # Combat properties
    weapon_range: float = 200.0
    weapon_damage: float = 10.0
    fire_rate: float = 1.0  # Shots per second
    last_fire_time: float = 0.0

    # Physics properties (ShipGenome)
    mass: float = 10.0
    max_thrust: float = 100.0
    turn_rate: float = 5.0
    
    # Tactcs Inputs (Admiral Layer)
    tactical_target: Optional[Tuple[float, float]] = None # (x, y) of focus target
    fleet_center: Optional[Tuple[float, float]] = None   # (x, y) of formation center
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Manual Control Inputs
    thrust_x: float = 0.0
    thrust_y: float = 0.0

    # Physics engine
    physics_engine: Optional[SpaceVoyagerEngine] = None
    
    def get_speed(self) -> float:
        """Calculate current speed"""
        return math.sqrt(self.velocity_x**2 + self.velocity_y**2)
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position"""
        return (self.x, self.y)
    
    def get_velocity_vector(self) -> Tuple[float, float]:
        """Get velocity vector"""
        return (self.velocity_x, self.velocity_y)
    
    def take_damage(self, damage: float):
        """Apply damage to ship"""
        # Shields absorb damage first
        if self.shield_strength > 0:
            shield_damage = min(self.shield_strength, damage)
            self.shield_strength -= shield_damage
            damage -= shield_damage
        
        # Apply remaining damage to hull
        self.hull_integrity = max(0, self.hull_integrity - damage)
        
        logger.debug(f"🚀 Ship {self.ship_id} took {damage} damage: hull={self.hull_integrity:.1f}, shields={self.shield_strength:.1f}")
    
    def is_destroyed(self) -> bool:
        """Check if ship is destroyed"""
        return self.hull_integrity <= 0
    
    def can_fire(self, current_time: float) -> bool:
        """Check if weapon can fire"""
        return current_time - self.last_fire_time >= (1.0 / self.fire_rate)
    
    def fire_weapon(self, current_time: float) -> bool:
        """Fire weapon if ready"""
        if self.can_fire(current_time):
            self.last_fire_time = current_time
            return True
        return False


class TargetingSystem:
    """Automated targeting system for combat"""
    
    def __init__(self, max_range: float = 300.0):
        self.max_range = max_range
        self.cone_angle = 45.0  # Targeting cone angle in degrees
        
    def find_nearest_enemy(self, ship: SpaceShip, all_ships: List[SpaceShip]) -> Optional[SpaceShip]:
        """Find nearest enemy ship within range"""
        nearest_enemy = None
        nearest_distance = float('inf')
        
        for other_ship in all_ships:
            if other_ship.ship_id == ship.ship_id or other_ship.is_destroyed():
                continue
            
            # Calculate distance
            dx = other_ship.x - ship.x
            dy = other_ship.y - ship.y
            distance = math.sqrt(dx**2 + dy**2)
            
            # Check if within range and closer than current nearest
            if distance <= self.max_range and distance < nearest_distance:
                # Check if within targeting cone
                if self._is_in_targeting_cone(ship, other_ship):
                    nearest_enemy = other_ship
                    nearest_distance = distance
        
        return nearest_enemy
    
    def _is_in_targeting_cone(self, ship: SpaceShip, target: SpaceShip) -> bool:
        """Check if target is within ship's targeting cone"""
        # Calculate angle to target
        dx = target.x - ship.x
        dy = target.y - ship.y
        angle_to_target = math.degrees(math.atan2(dy, dx))
        
        # Calculate angle difference
        angle_diff = abs((angle_to_target - ship.heading + 180) % 360 - 180)
        
        return angle_diff <= (self.cone_angle / 2)
    
    def get_lock_on_time(self, ship: SpaceShip, target: SpaceShip) -> float:
        """Calculate time needed to achieve weapon lock"""
        dx = target.x - ship.x
        dy = target.y - ship.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Lock time increases with distance and target movement
        target_speed = target.get_speed()
        lock_time = 0.5 + (distance / self.max_range) * 1.5 + (target_speed / 10.0) * 0.5
        
        return lock_time


# Global physics engine instance
space_physics_engine = None

def initialize_space_physics() -> SpaceVoyagerEngine:
    """Initialize global space physics engine"""
    global space_physics_engine
    space_physics_engine = SpaceVoyagerEngine()
    logger.info("🚀 Space Physics Engine initialized")
    return space_physics_engine
