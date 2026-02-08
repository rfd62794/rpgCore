"""
Admiral Service - Tactical Command System
Moved to tactics namespace for Single Responsibility Principle
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import math
import numpy as np

from src.dgt_core.simulation.space_physics import SpaceShip
from .targeting import tactical_targeting


class FleetOrder(Enum):
    """Tactical orders for the fleet"""
    FREE_ENGAGE = auto()  # Default: pilots choose targets
    FOCUS_FIRE = auto()   # All ships attack specific target
    RALLY = auto()        # All ships move to rally point
    DEFEND = auto()       # Protect a specific VIP


@dataclass
class CommandSignal:
    """Command signal with confidence for smooth targeting"""
    order: FleetOrder
    target_id: Optional[str] = None
    target_position: Optional[Tuple[float, float]] = None
    rally_point: Optional[Tuple[float, float]] = None
    confidence: float = 1.0
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class AdmiralService:
    """Tactical Layer Analysis Engine - Pure Math-Driven Command"""
    
    def __init__(self, fleet_id: str):
        self.fleet_id = fleet_id
        self.current_order: FleetOrder = FleetOrder.FREE_ENGAGE
        self.current_signal: Optional[CommandSignal] = None
        self.command_history: List[CommandSignal] = []
        self.max_history = 10
        
        # Fleet DPS calculation for targeting escalation
        self.fleet_dps: float = 0.0
        
        logger.debug(f"🎖️ AdmiralService initialized: {fleet_id}")
    
    def issue_order(self, order: FleetOrder, target_id: Optional[str] = None, 
                   target_position: Optional[Tuple[float, float]] = None,
                   rally_point: Optional[Tuple[float, float]] = None,
                   confidence: float = 1.0) -> CommandSignal:
        """Issue a new fleet-wide order with confidence"""
        signal = CommandSignal(
            order=order,
            target_id=target_id,
            target_position=target_position,
            rally_point=rally_point,
            confidence=confidence
        )
        
        self.current_order = order
        self.current_signal = signal
        
        # Add to history
        self.command_history.append(signal)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        
        logger.debug(f"🎖️ Order issued: {order.name} (confidence={confidence:.2f})")
        return signal
    
    def calculate_fleet_center(self, ships: List[SpaceShip]) -> Tuple[float, float]:
        """Calculate the centroid of the fleet using numpy"""
        if not ships:
            return (0.0, 0.0)
        
        positions = np.array([[s.x, s.y] for s in ships])
        center = np.mean(positions, axis=0)
        
        return tuple(center)
    
    def calculate_fleet_dps(self, ships: List[SpaceShip]) -> float:
        """Calculate total fleet DPS for targeting escalation"""
        total_dps = 0.0
        
        for ship in ships:
            # Simplified DPS calculation based on ship attributes
            # In full implementation, would use actual weapon systems
            base_dps = 10.0
            if hasattr(ship, 'weapon_damage'):
                base_dps = ship.weapon_damage
            
            # Apply modifiers
            if hasattr(ship, 'fire_rate'):
                total_dps += base_dps * ship.fire_rate
            else:
                total_dps += base_dps
        
        self.fleet_dps = total_dps
        tactical_targeting.update_fleet_dps(total_dps)
        
        return total_dps
    
    def get_tactical_inputs(self, ship: SpaceShip, fleet_center: Tuple[float, float], 
                           target_map: Dict[str, SpaceShip]) -> Dict[str, float]:
        """
        Calculate NEAT inputs for the "Admiral" layer.
        Returns normalized vectors (-1.0 to 1.0) using numpy for efficiency.
        """
        inputs = {}
        
        # 1. Vector to Fleet Center (Formation Keeping)
        ship_pos = np.array([ship.x, ship.y])
        center_pos = np.array(fleet_center)
        
        to_center = center_pos - ship_pos
        dist_center = np.linalg.norm(to_center) + 0.001
        
        inputs['vec_fleet_center_x'] = to_center[0] / dist_center
        inputs['vec_fleet_center_y'] = to_center[1] / dist_center
        
        # 2. Vector to Focus Target (Admiral's Command)
        if (self.current_order == FleetOrder.FOCUS_FIRE and 
            self.current_signal and self.current_signal.target_id):
            
            target = target_map.get(self.current_signal.target_id)
            if target:
                target_pos = np.array([target.x, target.y])
                to_target = target_pos - ship_pos
                dist_target = np.linalg.norm(to_target) + 0.001
                
                inputs['vec_focus_target_x'] = to_target[0] / dist_target
                inputs['vec_focus_target_y'] = to_target[1] / dist_target
                inputs['command_confidence'] = self.current_signal.confidence
            else:
                # Target lost/destroyed -> Fallback to 0
                inputs['vec_focus_target_x'] = 0.0
                inputs['vec_focus_target_y'] = 0.0
                inputs['command_confidence'] = 0.0
        else:
            inputs['vec_focus_target_x'] = 0.0
            inputs['vec_focus_target_y'] = 0.0
            inputs['command_confidence'] = 0.0
        
        # 3. Order type indicators
        inputs['order_free_engage'] = 1.0 if self.current_order == FleetOrder.FREE_ENGAGE else 0.0
        inputs['order_focus_fire'] = 1.0 if self.current_order == FleetOrder.FOCUS_FIRE else 0.0
        inputs['order_rally'] = 1.0 if self.current_order == FleetOrder.RALLY else 0.0
        inputs['order_defend'] = 1.0 if self.current_order == FleetOrder.DEFEND else 0.0
        
        return inputs
    
    def update_targeting_for_fleet(self, ships: List[SpaceShip], 
                                 targets: Dict[str, SpaceShip]) -> Dict[str, Optional[str]]:
        """Update targeting assignments for entire fleet"""
        assignments = {}
        
        # Update targets in tactical system
        for target_id, target in targets.items():
            if hasattr(target, 'armor') and hasattr(target, 'health'):
                tactical_targeting.add_target(
                    ship_id=target_id,
                    position=(target.x, target.y),
                    armor=getattr(target, 'armor', 50.0),
                    current_health=getattr(target, 'health', 100.0),
                    max_health=getattr(target, 'max_health', 100.0)
                )
        
        # Assign each ship
        for ship in ships:
            preferred_target = None
            
            # If focus fire order, prefer the commanded target
            if (self.current_order == FleetOrder.FOCUS_FIRE and 
                self.current_signal and self.current_signal.target_id):
                preferred_target = self.current_signal.target_id
            
            # Get assignment from tactical system
            assigned_target = tactical_targeting.assign_ship(
                ship_id=str(id(ship)),  # Use ship object ID as unique identifier
                preferred_target=preferred_target
            )
            
            assignments[str(id(ship))] = assigned_target
        
        return assignments
    
    def get_command_summary(self) -> Dict[str, any]:
        """Get summary of current command state"""
        if not self.current_signal:
            return {"status": "no_command"}
        
        return {
            "current_order": self.current_order.name,
            "target_id": self.current_signal.target_id,
            "confidence": self.current_signal.confidence,
            "fleet_dps": self.fleet_dps,
            "command_age": time.time() - self.current_signal.timestamp,
            "targeting_summary": tactical_targeting.get_targeting_summary()
        }


# Factory function for easy initialization
def create_admiral_service(fleet_id: str) -> AdmiralService:
    """Create an AdmiralService instance"""
    return AdmiralService(fleet_id)
