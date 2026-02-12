"""
AI Controller - AsteroidPilot Restoration
Tier 3 Application Logic - Autonomous ship control
"""

import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from foundation.types import Result
from foundation.constants import SOVEREIGN_WIDTH, SOVEREIGN_HEIGHT


class PilotState(Enum):
    """AI Pilot states"""
    SCANNING = "scanning"
    APPROACHING = "approaching"
    EVADE = "evade"
    COLLECTING = "collecting"
    SURVIVING = "surviving"


@dataclass
class Vector2:
    """2D Vector for spatial calculations"""
    x: float
    y: float
    
    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self) -> 'Vector2':
        mag = self.magnitude()
        if mag > 0:
            return Vector2(self.x / mag, self.y / mag)
        return Vector2(0, 0)
    
    def distance_to(self, other: 'Vector2') -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx ** 2 + dy ** 2)
    
    def angle_to(self, other: 'Vector2') -> float:
        """Calculate angle to another vector in radians"""
        dx = other.x - self.x
        dy = other.y - other.y
        return math.atan2(dy, dx)


class AsteroidPilot:
    """
    AI Pilot for autonomous asteroid navigation and collection
    Restored from legacy archive for Three-Tier Architecture
    """
    
    def __init__(self, pilot_id: str = "AI_PILOT_001"):
        self.pilot_id = pilot_id
        self.state = PilotState.SCANNING
        self.position = Vector2(SOVEREIGN_WIDTH / 2, SOVEREIGN_HEIGHT / 2)
        self.velocity = Vector2(0, 0)
        self.angle = 0.0
        
        # AI Parameters
        self.scan_radius = 80.0
        self.approach_distance = 40.0
        self.collect_distance = 15.0
        self.evade_distance = 25.0
        
        # Control outputs
        self.thrust = 0.0
        self.rotation = 0.0
        self.fire_weapon = False
        
        # Target tracking
        self.target_asteroid: Optional[Dict] = None
        self.threats: List[Dict] = []
        
        # Performance metrics
        self.survival_time = 0.0
        self.asteroids_collected = 0
        self.threats_evaded = 0
        
        logger.info(f"🤖 AsteroidPilot initialized: {pilot_id}")
    
    def update(self, dt: float, ship_state: Dict, asteroids: List[Dict]) -> Dict[str, Any]:
        """Update AI pilot decision making"""
        try:
            # Update internal state
            self.position = Vector2(ship_state.get('x', 0), ship_state.get('y', 0))
            self.velocity = Vector2(ship_state.get('vx', 0), ship_state.get('vy', 0))
            self.angle = ship_state.get('angle', 0)
            self.survival_time += dt
            
            # Reset controls
            self.thrust = 0.0
            self.rotation = 0.0
            self.fire_weapon = False
            
            # AI decision making
            self._make_decisions(asteroids)
            
            # Return control inputs
            return {
                'thrust': self.thrust,
                'rotation': self.rotation,
                'fire': self.fire_weapon,
                'state': self.state.value,
                'target': self.target_asteroid['id'] if self.target_asteroid else None
            }
            
        except Exception as e:
            logger.error(f"AI Pilot update failed: {e}")
            return {'thrust': 0, 'rotation': 0, 'fire': False, 'state': 'error', 'target': None}
    
    def update(self, dt: float, entity_state: Dict[str, Any], world_data: Dict[str, Any]) -> Result[ControlInput]:
        """Update AI pilot for controller interface"""
        try:
            # Extract asteroids from world data
            asteroids = world_data.get('asteroids', [])
            
            # Update using legacy interface
            controls = self.update(dt, entity_state, asteroids)
            
            # Convert to ControlInput
            control_input = ControlInput(
                thrust=controls['thrust'],
                rotation=controls['rotation'],
                fire_weapon=controls['fire_weapon'],
                special_action=controls.get('special_action')
            )
            
            return Result(success=True, value=control_input)
            
        except Exception as e:
            return Result(success=False, error=f"AI Controller update failed: {e}")
    
    def activate(self) -> Result[bool]:
        """Activate the AI controller"""
        try:
            self.is_active = True
            logger.info(f"🤖 AI Controller {self.pilot_id} activated")
            return Result(success=True, value=True)
        except Exception as e:
            return Result(success=False, error=f"Failed to activate AI controller: {e}")
    
    def deactivate(self) -> Result[bool]:
        """Deactivate the AI controller"""
        try:
            self.is_active = False
            logger.info(f"🤖 AI Controller {self.pilot_id} deactivated")
            return Result(success=True, value=True)
        except Exception as e:
            return Result(success=False, error=f"Failed to deactivate AI controller: {e}")
    
    def _make_decisions(self, asteroids: List[Dict]) -> None:
        """Core AI decision making logic"""
        # Scan for asteroids and threats
        self._scan_environment(asteroids)
        
        # State-based decision making
        if self.state == PilotState.SCANNING:
            self._handle_scanning()
        elif self.state == PilotState.APPROACHING:
            self._handle_approaching()
        elif self.state == PilotState.EVADE:
            self._handle_evade()
        elif self.state == PilotState.COLLECTING:
            self._handle_collecting()
        elif self.state == PilotState.SURVIVING:
            self._handle_survival()
    
    def _scan_environment(self, asteroids: List[Dict]) -> None:
        """Scan for asteroids and classify threats"""
        self.target_asteroid = None
        self.threats = []
        
        nearby_asteroids = []
        
        for asteroid in asteroids:
            asteroid_pos = Vector2(asteroid['x'], asteroid['y'])
            distance = self.position.distance_to(asteroid_pos)
            
            if distance < self.scan_radius:
                nearby_asteroids.append({
                    'asteroid': asteroid,
                    'distance': distance,
                    'position': asteroid_pos
                })
                
                # Check if it's a threat (too close or too large)
                if distance < self.evade_distance or asteroid.get('size', 1) > 2:
                    self.threats.append({
                        'asteroid': asteroid,
                        'distance': distance,
                        'position': asteroid_pos,
                        'threat_level': self._calculate_threat_level(asteroid, distance)
                    })
        
        # Select target asteroid (closest non-threat)
        non_threats = [a for a in nearby_asteroids if a not in [t['asteroid'] for t in self.threats]]
        if non_threats:
            non_threats.sort(key=lambda a: a['distance'])
            self.target_asteroid = non_threats[0]['asteroid']
        
        # Sort threats by danger level
        self.threats.sort(key=lambda t: t['threat_level'], reverse=True)
    
    def _calculate_threat_level(self, asteroid: Dict, distance: float) -> float:
        """Calculate threat level of an asteroid"""
        size = asteroid.get('size', 1)
        speed = math.sqrt(asteroid.get('vx', 0) ** 2 + asteroid.get('vy', 0) ** 2)
        
        # Threat increases with size and speed, decreases with distance
        threat = (size * speed) / max(distance, 1.0)
        return threat
    
    def _handle_scanning(self) -> None:
        """Handle scanning state"""
        if self.threats:
            # Immediate threat evasion
            self.state = PilotState.EVADE
        elif self.target_asteroid:
            # Found target, approach it
            self.state = PilotState.APPROACHING
        else:
            # No targets, search pattern
            self._execute_search_pattern()
    
    def _handle_approaching(self) -> None:
        """Handle approaching state"""
        if not self.target_asteroid:
            self.state = PilotState.SCANNING
            return
        
        if self.threats:
            # Threat detected, prioritize evasion
            self.state = PilotState.EVADE
            return
        
        target_pos = Vector2(self.target_asteroid['x'], self.target_asteroid['y'])
        distance = self.position.distance_to(target_pos)
        
        if distance < self.collect_distance:
            # Close enough to collect
            self.state = PilotState.COLLECTING
        else:
            # Move towards target
            self._navigate_to_target(target_pos)
    
    def _handle_evade(self) -> None:
        """Handle evasion state"""
        if not self.threats:
            # No more threats, return to scanning
            self.state = PilotState.SCANNING
            return
        
        # Evade highest priority threat
        threat = self.threats[0]
        threat_pos = threat['position']
        
        # Calculate evasion vector (away from threat)
        evade_vector = Vector2(
            self.position.x - threat_pos.x,
            self.position.y - threat_pos.y
        ).normalize()
        
        # Apply thrust in evasion direction
        self.thrust = 1.0
        
        # Rotate to face evasion direction
        target_angle = math.atan2(evade_vector.y, evade_vector.x)
        self._rotate_to_angle(target_angle)
        
        # Check if evaded
        if self.position.distance_to(threat_pos) > self.evade_distance * 1.5:
            self.threats_evaded += 1
            self.threats.pop(0)
    
    def _handle_collecting(self) -> None:
        """Handle collecting state"""
        if not self.target_asteroid:
            self.state = PilotState.SCANNING
            return
        
        target_pos = Vector2(self.target_asteroid['x'], self.target_asteroid['y'])
        distance = self.position.distance_to(target_pos)
        
        if distance < self.collect_distance:
            # Collect the asteroid
            self.asteroids_collected += 1
            self.target_asteroid = None
            self.state = PilotState.SCANNING
            logger.info(f"🤖 AI Pilot collected asteroid! Total: {self.asteroids_collected}")
        else:
            # Move closer
            self._navigate_to_target(target_pos)
    
    def _handle_survival(self) -> None:
        """Handle survival state (low health/emergency)"""
        # Conservative behavior - focus on evasion
        if self.threats:
            self._handle_evade()
        else:
            # Move to safe corner
            safe_corner = Vector2(20, 20)  # Top-left corner
            self._navigate_to_target(safe_corner)
    
    def _navigate_to_target(self, target_pos: Vector2) -> None:
        """Navigate towards a target position"""
        # Calculate direction to target
        direction = Vector2(
            target_pos.x - self.position.x,
            target_pos.y - self.position.y
        ).normalize()
        
        # Apply thrust
        self.thrust = 0.8  # Moderate thrust for precision
        
        # Rotate to face target
        target_angle = math.atan2(direction.y, direction.x)
        self._rotate_to_angle(target_angle)
    
    def _rotate_to_angle(self, target_angle: float) -> None:
        """Rotate towards target angle"""
        # Normalize angles
        current_angle = self.angle % (2 * math.pi)
        target_angle = target_angle % (2 * math.pi)
        
        # Calculate shortest rotation direction
        angle_diff = target_angle - current_angle
        
        # Handle wrap-around
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        # Apply rotation based on angle difference
        rotation_speed = 2.0  # radians per second
        if abs(angle_diff) > 0.1:
            self.rotation = rotation_speed if angle_diff > 0 else -rotation_speed
        else:
            self.rotation = 0.0
    
    def _execute_search_pattern(self) -> None:
        """Execute search pattern when no targets"""
        # Spiral search pattern
        search_time = self.survival_time % 10.0  # 10-second pattern
        search_radius = 30.0
        
        # Calculate spiral position
        angle = search_time * 0.5  # Slow rotation
        radius = search_radius * (search_time / 10.0)  # Expanding radius
        
        target_x = SOVEREIGN_WIDTH / 2 + radius * math.cos(angle)
        target_y = SOVEREIGN_HEIGHT / 2 + radius * math.sin(angle)
        
        target_pos = Vector2(target_x, target_y)
        self._navigate_to_target(target_pos)
    
    def get_status(self) -> Dict[str, Any]:
        """Get pilot status and metrics"""
        return {
            'pilot_id': self.pilot_id,
            'state': self.state.value,
            'position': {'x': self.position.x, 'y': self.position.y},
            'survival_time': self.survival_time,
            'asteroids_collected': self.asteroids_collected,
            'threats_evaded': self.threats_evaded,
            'current_target': self.target_asteroid['id'] if self.target_asteroid else None,
            'active_threats': len(self.threats)
        }


class HumanController(BaseController):
    """
    Human controller for keyboard/miyoo input
    Complements the AI Controller for dual-track gameplay
    """
    
    def __init__(self, controller_id: str = "HUMAN_PLAYER"):
        self.controller_id = controller_id
        self.thrust = 0.0
        self.rotation = 0.0
        self.fire_weapon = False
        
        # Input state
        self.keys_pressed = set()
        
        logger.info(f"👤 HumanController initialized: {controller_id}")
    
    def update(self, dt: float, ship_state: Dict, asteroids: List[Dict]) -> Dict[str, Any]:
        """Update human controller based on input"""
        # This would be connected to actual input system
        # For now, return neutral controls
        return {
            'thrust': self.thrust,
            'rotation': self.rotation,
            'fire': self.fire_weapon,
            'state': 'human_control',
            'target': None
        }
    
    def handle_key_press(self, key: str) -> None:
        """Handle key press events"""
        self.keys_pressed.add(key)
        self._update_controls_from_keys()
    
    def handle_key_release(self, key: str) -> None:
        """Handle key release events"""
        self.keys_pressed.discard(key)
        self._update_controls_from_keys()
    
    def _update_controls_from_keys(self) -> None:
        """Update controls based on current key state"""
        self.thrust = 0.0
        self.rotation = 0.0
        self.fire_weapon = False
        
        if 'w' in self.keys_pressed or 'up' in self.keys_pressed:
            self.thrust = 1.0
        if 'a' in self.keys_pressed or 'left' in self.keys_pressed:
            self.rotation = -2.0
        if 'd' in self.keys_pressed or 'right' in self.keys_pressed:
            self.rotation = 2.0
        if ' ' in self.keys_pressed or 'enter' in self.keys_pressed:
            self.fire_weapon = True


def create_ai_controller(pilot_id: str = "AI_PILOT_001") -> AsteroidPilot:
    """Factory function to create AI controller"""
    return AsteroidPilot(pilot_id)


def create_human_controller(controller_id: str = "HUMAN_PLAYER") -> HumanController:
    """Factory function to create human controller"""
    return HumanController(controller_id)
