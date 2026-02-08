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
from src.dgt_core.generators.ship_wright import ShipWright
from src.dgt_core.kernel.state import ShipGenome
from src.dgt_core.kernel.fleet_roles import FleetRole
from src.dgt_core.simulation.space_physics import SpaceShip


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
    """Sovereign Fleet Commander Service - manages credits and fleet roster with Elite Pilot integration"""
    
    def __init__(self):
        self.credits: int = 1000  # Starting credits
        self.active_fleet: List[FleetMember] = []
        self.reserve_fleet: List[FleetMember] = []  # Unpiloted ships
        self.max_fleet_size: int = 6  # Maximum active fleet members
        self.commander_level: int = 1
        self.total_battles: int = 0
        self.commander_name: str = "Admiral"
        
        # Elite pilot integration
        self.pilot_registry: Optional[PilotRegistry] = None
        self.last_scout_time: float = 0.0
        self.scout_interval: float = 30.0  # Scout every 30 seconds
        self.new_ace_notification: Optional[Dict[str, Any]] = None
        
        # Initialize pilot registry
        self._initialize_pilot_registry()
        
        logger.info(f"🏆 Commander Service initialized: {self.credits} credits")
    
    def _initialize_pilot_registry(self):
        """Initialize pilot registry and start scouting"""
        try:
            self.pilot_registry = initialize_pilot_registry()
            logger.info("🎖️ Pilot registry connected")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize pilot registry: {e}")
    
    def scout_for_new_pilots(self) -> Optional[Dict[str, Any]]:
        """Scout for new elite pilots (called periodically)"""
        if not self.pilot_registry:
            return None
        
        current_time = time.time()
        if current_time - self.last_scout_time < self.scout_interval:
            return None
        
        self.last_scout_time = current_time
        
        # Scan for new pilots
        new_pilots = self.pilot_registry.scan_for_new_pilots()
        
        # Check for new ace notification
        ace_notification = self.pilot_registry.get_new_ace_notification()
        if ace_notification:
            self.new_ace_notification = ace_notification
            logger.info(f"🎖️ New Ace Pilot available: {ace_notification['call_sign']} - Fitness: {ace_notification['fitness']:.2f}")
            return ace_notification
        
        return None
    
    def get_available_elite_pilots(self, ship_class: Optional[ShipRole] = None) -> List[ElitePilot]:
        """Get available elite pilots for hire"""
        if not self.pilot_registry:
            return []
        
        # Filter by credits and availability
        affordable_pilots = self.pilot_registry.get_affordable_pilots(self.credits)
        
        # Filter by ship class compatibility if specified
        if ship_class:
            affordable_pilots = [p for p in affordable_pilots 
                                if p.calculate_compatibility(ship_class.value) > 0.7]
        
        return affordable_pilots
    
    def hire_elite_pilot(self, elite_pilot_id: str, ship_class: ShipRole) -> Tuple[bool, Optional[FleetMember]]:
        """Hire an elite pilot"""
        if not self.pilot_registry:
            return False, None
        
        # Hire from registry
        success, elite_pilot = self.pilot_registry.hire_pilot(elite_pilot_id, self.credits)
        if not success:
            return False, None
        
        # Create fleet member
        fleet_member = FleetMember(
            pilot_id=f"fleet_{elite_pilot.pilot_id}",
            genome_id=elite_pilot.genome_id,
            pilot_name=elite_pilot.call_sign,
            ship_class=ship_class,
            cost=elite_pilot.current_cost,
            acquisition_time=time.time(),
            elite_pilot_id=elite_pilot_id
        )
        
        # Deduct credits and add to fleet
        self.credits -= elite_pilot.current_cost
        self.active_fleet.append(fleet_member)
        
        logger.info(f"🎖️ Hired elite pilot {elite_pilot.call_sign} for {elite_pilot.current_cost} credits")
        return True, fleet_member
    
    def launch_audition(self, elite_pilot_id: str) -> bool:
        """Launch test flight for elite pilot audition"""
        if not self.pilot_registry:
            return False
        
        elite_pilot = self.pilot_registry.elite_pilots.get(elite_pilot_id)
        if not elite_pilot:
            return False
        
        try:
            # Launch view_elite.py in separate process
            script_path = Path(__file__).parent.parent.parent / "view_elite.py"
            genome_file = elite_pilot.metadata_file
            
            logger.info(f"🎬 Launching audition for {elite_pilot.call_sign}")
            
            # Run in background thread to avoid blocking
            def run_audition():
                try:
                    result = subprocess.run([
                        "python", str(script_path), 
                        "--genome", genome_file,
                        "--duration", "60"
                    ], capture_output=True, text=True, timeout=120)  # 2 minute timeout
                    
                    if result.returncode == 0:
                        logger.info(f"🎬 Audition completed for {elite_pilot.call_sign}")
                    else:
                        logger.error(f"❌ Audition failed for {elite_pilot.call_sign}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.error(f"❌ Audition timed out for {elite_pilot.call_sign}")
                except Exception as e:
                    logger.error(f"❌ Audition error for {elite_pilot.call_sign}: {e}")
            
            threading.Thread(target=run_audition, daemon=True).start()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to launch audition: {e}")
            return False
    
    def update_fleet_battle_records(self, battle_results: Dict[str, Dict[str, Any]]):
        """Update fleet member battle records and elite pilot registry"""
        for fleet_member_id, result in battle_results.items():
            # Find fleet member
            fleet_member = next((m for m in self.active_fleet if m.pilot_id == fleet_member_id), None)
            if not fleet_member:
                continue
            
            # Update fleet member stats
            fleet_member.update_stats(result.get('won', False))
            
            # Update elite pilot registry if applicable
            if fleet_member.elite_pilot_id and self.pilot_registry:
                self.pilot_registry.update_pilot_battle_record(
                    fleet_member.elite_pilot_id,
                    result.get('won', False),
                    result.get('kills', 0),
                    result.get('damage_dealt', 0.0),
                    result.get('damage_taken', 0.0),
                    result.get('battle_time', 0.0)
                )
        
        self.total_battles += 1
    
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
        """Get comprehensive fleet status with elite pilot information"""
        # Get basic status
        base_status = {
            'commander_name': self.commander_name,
            'commander_level': self.commander_level,
            'credits': self.credits,
            'fleet_size': len(self.active_fleet),
            'max_fleet_size': self.max_fleet_size,
            'total_battles': self.total_battles,
            'composition': self.get_fleet_composition(),
            'top_performer': self.get_top_performers(1)[0] if self.active_fleet else None
        }
        
        # Add elite pilot information
        if self.pilot_registry:
            available_pilots = len(self.pilot_registry.get_affordable_pilots(self.credits))
            base_status.update({
                'available_elite_pilots': available_pilots,
                'total_elite_pilots': len(self.pilot_registry.elite_pilots),
                'new_ace_notification': self.new_ace_notification
            })
        
        # Add fleet member elite status
        elite_members = [m for m in self.active_fleet if m.elite_pilot_id]
        base_status['elite_fleet_members'] = len(elite_members)
        
        return base_status
    
    def get_fleet_neural_stats(self) -> List[Dict[str, Any]]:
        """Get neural statistics for fleet members"""
        neural_stats = []
        
        for member in self.active_fleet:
            stats = {
                'pilot_id': member.pilot_id,
                'pilot_name': member.pilot_name,
                'ship_class': member.ship_class.value,
                'wins': member.wins,
                'losses': member.losses,
                'kd_ratio': member.kd_ratio,
                'prestige_points': member.prestige_points,
                'is_elite': member.elite_pilot_id is not None
            }
            
            # Add elite pilot performance matrix if available
            if member.elite_pilot_id and self.pilot_registry:
                performance_matrix = self.pilot_registry.get_pilot_performance_matrix(member.elite_pilot_id)
                stats['performance_matrix'] = performance_matrix
                
                # Get elite pilot details
                elite_pilot = self.pilot_registry.elite_pilots.get(member.elite_pilot_id)
                if elite_pilot:
                    stats['elite_details'] = {
                        'call_sign': elite_pilot.call_sign,
                        'generation': elite_pilot.generation,
                        'specialization': elite_pilot.specialization.value,
                        'combat_rating': elite_pilot.stats.combat_rating()
                    }
            
            neural_stats.append(stats)
        
        return neural_stats
    
    def promote_commander(self):
        """Promote commander level"""
        self.commander_level += 1
        self.max_fleet_size = min(12, 6 + self.commander_level)
        self.credits += 500 * self.commander_level  # Level bonus
        
        logger.info(f"🌟 Promoted to Level {self.commander_level}! Fleet size: {self.max_fleet_size}")

    def deploy_ship(self, member: FleetMember) -> Optional[SpaceShip]:
        """
        Hydrate a FleetMember into a physical SpaceShip entity using ShipWright.
        Maps pilot stats (EliteGenome) to ship traits (ShipGenome).
        """
        if not member:
            return None

        # 1. underlying Pilot Stats
        pilot_stats = None
        if member.elite_pilot_id and self.pilot_registry:
            elite = self.pilot_registry.elite_pilots.get(member.elite_pilot_id)
            if elite:
                pilot_stats = elite.stats
        
        # 2. Construct ShipGenome
        genome = ShipGenome(genome_id=member.genome_id)
        
        # Map stats to traits (0.0 - 1.0)
        # Default to 0.5 if no elite stats
        aggression = pilot_stats.aggression if pilot_stats else 0.5
        accuracy = pilot_stats.accuracy if pilot_stats else 0.5
        evasion = pilot_stats.evasion if pilot_stats else 0.5
        
        genome.traits = {
            "aggression": aggression,
            "armor": 1.0 - evasion, # Heavier armor reduces evasion usually, or abstract mapping
            "accuracy": accuracy
        }
        
        # 3. Determine FleetRole
        # Map member.ship_class (ShipRole enum string) to FleetRole enum
        try:
            role_name = member.ship_class.value.upper()
            role = FleetRole[role_name]
        except KeyError:
            role = FleetRole.INTERCEPTOR
            
        # 4. Use ShipWright factory
        physics_params = ShipWright.apply_genetics(genome, role)
        
        # 5. Instantiate SpaceShip
        # Note: SpaceShip accepts mass/max_thrust/turn_rate if we updated it (we did)
        ship = SpaceShip(
            ship_id=member.pilot_id,
            x=0, y=0, # Initial pos, caller should set
            mass=physics_params['mass'],
            max_thrust=physics_params['max_thrust'],
            turn_rate=physics_params.get('turn_rate', 5.0)
        )
        # Cache metadata
        ship.metadata['role'] = role.name
        ship.metadata['pilot_name'] = member.pilot_name
        
        return ship



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
