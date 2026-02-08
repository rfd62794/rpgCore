"""
DGT Fleet Service - ADR 135 & 138 Implementation
Commander's Deck for Tactical Fleet Management with Elite Pilot Integration

Manages player credits, roster, and pilot acquisition
for the Sovereign Fleet Commander game loop.
Now integrates with Pilot Registry for elite pilot scouting.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import time
import subprocess
import threading
from pathlib import Path

from loguru import logger

from .pilot_registry import PilotRegistry, ElitePilot, initialize_pilot_registry, get_pilot_registry


class ShipRole(Enum):
    """Ship roles for tactical assignments"""
    INTERCEPTOR = "interceptor"
    HEAVY = "heavy"
    SCOUT = "scout"
    BOMBER = "bomber"


class FleetStatus(Enum):
    """Fleet member status"""
    DOCKED = "docked"
    DEPLOYED = "deployed"
    REPAIRING = "repairing"
    TRAINING = "training"


@dataclass
class FleetMember:
    """Individual fleet member with pilot and ship data"""
    pilot_id: str
    genome_id: str
    pilot_name: str
    ship_class: ShipRole
    prestige_points: int = 0
    wins: int = 0
    losses: int = 0
    kd_ratio: float = 0.0
    status: FleetStatus = FleetStatus.DOCKED
    cost: int = 100  # Base cost to hire
    acquisition_time: float = 0.0  # When this pilot was acquired
    elite_pilot_id: Optional[str] = None  # Link to elite pilot registry
    
    def __post_init__(self):
        """Calculate K/D ratio after initialization"""
        if self.losses > 0:
            self.kd_ratio = self.wins / self.losses
    
    def update_stats(self, win: bool):
        """Update pilot statistics after battle"""
        if win:
            self.wins += 1
            self.prestige_points += 25
        else:
            self.losses += 1
            self.prestige_points += 5
        
        # Recalculate K/D ratio
        if self.losses > 0:
            self.kd_ratio = self.wins / self.losses
        elif self.wins > 0:
            self.kd_ratio = float('inf')
        else:
            self.kd_ratio = 0.0


class CommanderService:
    """Sovereign Fleet Commander Service - manages credits and fleet roster"""
    
    def __init__(self):
        self.credits: int = 1000  # Starting credits
        self.active_fleet: List[FleetMember] = []
        self.reserve_fleet: List[FleetMember] = []  # Unpiloted ships
        self.max_fleet_size: int = 6  # Maximum active fleet members
        self.commander_level: int = 1
        self.total_battles: int = 0
        self.commander_name: str = "Admiral"
        
        logger.info(f"🏆 Commander Service initialized: {self.credits} credits")
    
    def purchase_pilot(self, pilot_data: Dict[str, Any]) -> bool:
        """Purchase a new pilot and add to fleet"""
        cost = pilot_data.get('cost', 100)
        
        if self.credits < cost:
            logger.warning(f"💸 Insufficient credits: need {cost}, have {self.credits}")
            return False
        
        if len(self.active_fleet) >= self.max_fleet_size:
            logger.warning(f"🚫 Fleet full: max size {self.max_fleet_size}")
            return False
        
        # Create fleet member
        fleet_member = FleetMember(
            pilot_id=pilot_data['pilot_id'],
            genome_id=pilot_data['genome_id'],
            pilot_name=pilot_data.get('pilot_name', f"Pilot_{pilot_data['pilot_id']}"),
            ship_class=ShipRole(pilot_data.get('ship_class', 'interceptor')),
            cost=cost,
            acquisition_time=time.time()
        )
        
        # Deduct credits and add to fleet
        self.credits -= cost
        self.active_fleet.append(fleet_member)
        
        logger.info(f"🎖️ Purchased pilot {fleet_member.pilot_name} for {cost} credits")
        return True
    
    def dismiss_pilot(self, pilot_id: str) -> bool:
        """Dismiss a pilot and get partial refund"""
        for i, member in enumerate(self.active_fleet):
            if member.pilot_id == pilot_id:
                # Calculate refund (50% of cost)
                refund = member.cost // 2
                self.credits += refund
                
                # Remove from active fleet
                dismissed = self.active_fleet.pop(i)
                self.reserve_fleet.append(dismissed)
                
                logger.info(f"👋 Dismissed pilot {dismissed.pilot_name}, refunded {refund} credits")
                return True
        
        logger.warning(f"❌ Pilot {pilot_id} not found in active fleet")
        return False
    
    def get_top_performers(self, limit: int = 3) -> List[FleetMember]:
        """Get top performing pilots by prestige points"""
        return sorted(self.active_fleet, key=lambda m: m.prestige_points, reverse=True)[:limit]
    
    def get_fleet_composition(self) -> Dict[str, int]:
        """Get fleet composition by ship class"""
        composition = {}
        for member in self.active_fleet:
            role = member.ship_class.value
            composition[role] = composition.get(role, 0) + 1
        return composition
    
    def award_battle_rewards(self, battle_results: Dict[str, bool]):
        """Award credits and prestige after battle"""
        for pilot_id, won in battle_results.items():
            for member in self.active_fleet:
                if member.pilot_id == pilot_id:
                    if won:
                        # Victory bonus
                        self.credits += 50
                        member.prestige_points += 10
                    else:
                        # Participation bonus
                        self.credits += 10
                        member.prestige_points += 2
                    break
        
        self.total_battles += 1
        logger.info(f"🏆 Battle rewards awarded: {len(battle_results)} pilots")
    
    def can_afford(self, cost: int) -> bool:
        """Check if commander can afford purchase"""
        return self.credits >= cost
    
    def get_fleet_status(self) -> Dict[str, Any]:
        """Get comprehensive fleet status"""
        return {
            'commander_name': self.commander_name,
            'commander_level': self.commander_level,
            'credits': self.credits,
            'fleet_size': len(self.active_fleet),
            'max_fleet_size': self.max_fleet_size,
            'total_battles': self.total_battles,
            'composition': self.get_fleet_composition(),
            'top_performer': self.get_top_performers(1)[0] if self.active_fleet else None
        }
    
    def promote_commander(self):
        """Promote commander level"""
        self.commander_level += 1
        self.max_fleet_size = min(12, 6 + self.commander_level)
        self.credits += 500 * self.commander_level  # Level bonus
        
        logger.info(f"🌟 Promoted to Level {self.commander_level}! Fleet size: {self.max_fleet_size}")


# Global commander service instance
commander_service = None

def initialize_commander_service() -> CommanderService:
    """Initialize global commander service"""
    global commander_service
    commander_service = CommanderService()
    logger.info("🏆 Global Commander Service initialized")
    return commander_service

def get_commander_service() -> Optional[CommanderService]:
    """Get global commander service instance"""
    return commander_service
