"""
Stakes Manager - Enforces Permadeath and Resource Scarcity
ADR 170: Hardware Burn & Permadeath Mechanics
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from ..kernel.universal_registry import UniversalRegistry
from ..kernel.models import StoryFragment, asset_registry
from ..simulation.space_physics import PhysicsState


class ResourceStatus(str, Enum):
    """Resource status levels"""
    FULL = "full"
    OPERATIONAL = "operational"
    LOW = "low"
    CRITICAL = "critical"
    DEPLETED = "depleted"


class DeathCause(str, Enum):
    """Causes of permadeath"""
    COMBAT_DESTRUCTION = "combat_destruction"
    RESOURCE_DEPLETION = "resource_depletion"
    ABANDONED = "abandoned"
    SYSTEM_FAILURE = "system_failure"


@dataclass
class ResourceMetrics:
    """Resource tracking for individual ships"""
    ship_id: str
    fuel_level: float = 100.0  # 0-100%
    thermal_load: float = 0.0   # 0-100%
    hull_integrity: float = 100.0  # 0-100%
    last_update: float = 0.0
    
    # Resource consumption rates
    fuel_consumption_rate: float = 0.5  # % per second during thrust
    thermal_generation_rate: float = 0.3  # % per second during combat
    thermal_dissipation_rate: float = 0.1  # % per second during idle
    
    def get_status(self) -> ResourceStatus:
        """Get current resource status"""
        if self.fuel_level <= 0 or self.thermal_load >= 100:
            return ResourceStatus.DEPLETED
        elif self.fuel_level < 20 or self.thermal_load > 80:
            return ResourceStatus.CRITICAL
        elif self.fuel_level < 50 or self.thermal_load > 60:
            return ResourceStatus.LOW
        else:
            return ResourceStatus.OPERATIONAL
    
    def is_operational(self) -> bool:
        """Check if ship can operate"""
        return (self.fuel_level > 0 and 
                self.thermal_load < 100 and 
                self.hull_integrity > 0)


class StakesManager:
    """Enforces Permadeath and Resource Scarcity"""
    
    def __init__(self, registry: UniversalRegistry, max_chassis_slots: int = 3):
        self.registry = registry
        self.max_chassis_slots = max_chassis_slots
        self.resource_metrics: Dict[str, ResourceMetrics] = {}
        self.graveyard: List[Dict[str, Any]] = []
        
        # Resource costs
        self.refuel_cost_per_percent = 10.0  # Credits per % fuel
        self.repair_cost_per_percent = 15.0  # Credits per % hull
        self.thermal_cooling_cost = 50.0  # Credits for full thermal reset
        
        logger.info(f"⚰️ StakesManager initialized: {max_chassis_slots} chassis slots")
    
    def register_ship(self, ship_id: str, initial_fuel: float = 100.0, initial_hull: float = 100.0):
        """Register a ship for resource tracking"""
        metrics = ResourceMetrics(
            ship_id=ship_id,
            fuel_level=initial_fuel,
            hull_integrity=initial_hull,
            last_update=time.time()
        )
        
        self.resource_metrics[ship_id] = metrics
        logger.debug(f"⚰️ Registered ship {ship_id} for resource tracking")
    
    def update_resources(self, ship_id: str, physics_state: PhysicsState, in_combat: bool = False):
        """Update resource consumption based on physics state"""
        if ship_id not in self.resource_metrics:
            self.register_ship(ship_id)
        
        metrics = self.resource_metrics[ship_id]
        current_time = time.time()
        delta_time = current_time - metrics.last_update
        
        if delta_time <= 0:
            return
        
        # Fuel consumption (only when thrusting)
        if physics_state.thrust_active:
            fuel_consumption = metrics.fuel_consumption_rate * delta_time
            metrics.fuel_level = max(0, metrics.fuel_level - fuel_consumption)
        
        # Thermal load management
        if in_combat:
            thermal_generation = metrics.thermal_generation_rate * delta_time
            metrics.thermal_load = min(100, metrics.thermal_load + thermal_generation)
        else:
            thermal_dissipation = metrics.thermal_dissipation_rate * delta_time
            metrics.thermal_load = max(0, metrics.thermal_load - thermal_dissipation)
        
        metrics.last_update = current_time
        
        # Check for resource depletion
        if not metrics.is_operational():
            self.handle_resource_depletion(ship_id)
    
    def apply_damage(self, ship_id: str, damage_amount: float):
        """Apply combat damage to hull integrity"""
        if ship_id not in self.resource_metrics:
            self.register_ship(ship_id)
        
        metrics = self.resource_metrics[ship_id]
        metrics.hull_integrity = max(0, metrics.hull_integrity - damage_amount)
        
        # Check for destruction
        if metrics.hull_integrity <= 0:
            self.process_death(ship_id, DeathCause.COMBAT_DESTRUCTION)
    
    def handle_resource_depletion(self, ship_id: str):
        """Handle resource depletion (non-combat death)"""
        logger.warning(f"⚰️ RESOURCE DEPLETION: Ship {ship_id} out of fuel/thermal capacity")
        
        # Disable ship in physics engine
        # This would integrate with the actual physics engine
        logger.info(f"⚰️ Disabling ship {ship_id} - drifting in space")
        
        # Give player time to recover before permadeath
        # Start a countdown timer for extraction
        self.start_extraction_countdown(ship_id)
    
    def start_extraction_countdown(self, ship_id: str, timeout_seconds: float = 60.0):
        """Start countdown for ship extraction before permadeath"""
        logger.warning(f"⚰️ EXTRACTION COUNTDOWN: Ship {ship_id} has {timeout_seconds}s to be recalled")
        
        # This would integrate with the UI to show countdown
        # For now, just log the urgency
        logger.critical(f"⚰️ RECALL SHIP {ship_id} NOW OR FACE PERMADEATH!")
    
    def process_death(self, ship_id: str, cause: DeathCause):
        """Process permadeath - move to graveyard"""
        logger.critical(f"⚰️ PERMADEATH DETECTED: Ship {ship_id} scrubbed from active duty")
        
        try:
            # Get ship data from registry
            ship_data = self.registry.get_ship_summary(ship_id)
            if not ship_data:
                ship_data = {"ship_id": ship_id, "unknown": True}
            
            # Create graveyard entry
            grave_entry = {
                "ship_id": ship_id,
                "death_time": time.time(),
                "death_cause": cause.value,
                "final_generation": ship_data.get("generation", 0),
                "total_victories": ship_data.get("total_victories", 0),
                "total_xp": ship_data.get("total_xp", 0),
                "last_engine_type": ship_data.get("last_engine_type", "unknown"),
                "epitaph": self.generate_epitaph(ship_data, cause)
            }
            
            # Move to graveyard
            self.graveyard.append(grave_entry)
            
            # Remove from active registry
            self.registry.move_to_graveyard(ship_id)
            
            # Remove from resource tracking
            if ship_id in self.resource_metrics:
                del self.resource_metrics[ship_id]
            
            # Generate funeral rite story
            self.generate_funeral_rite(grave_entry)
            
            logger.info(f"⚰️ Ship {ship_id} moved to graveyard - {len(self.graveyard)} total")
            
        except Exception as e:
            logger.error(f"⚰️ Failed to process death for {ship_id}: {e}")
    
    def generate_epitaph(self, ship_data: Dict[str, Any], cause: DeathCause) -> str:
        """Generate epitaph for fallen ship"""
        generation = ship_data.get("generation", 0)
        victories = ship_data.get("total_victories", 0)
        
        if cause == DeathCause.COMBAT_DESTRUCTION:
            return f"Gen-{generation} warrior, {victories} victories, fell in glorious combat"
        elif cause == DeathCause.RESOURCE_DEPLETION:
            return f"Gen-{generation} pioneer, {victories} victories, lost to the void"
        elif cause == DeathCause.ABANDONED:
            return f"Gen-{generation} explorer, {victories} victories, abandoned in the dark"
        else:
            return f"Gen-{generation} veteran, {victories} victories, systems failed"
    
    def generate_funeral_rite(self, grave_entry: Dict[str, Any]):
        """Generate funeral rite story fragment"""
        try:
            funeral_story = StoryFragment(
                fragment_id=f"funeral_{grave_entry['ship_id']}_{int(grave_entry['death_time'])}",
                title=f"Funeral Rite: {grave_entry['ship_id']}",
                content=f"The ship {grave_entry['ship_id']} has been lost to the void. "
                       f"{grave_entry['epitaph']}. "
                       f"They served for {grave_entry['total_victories']} victories "
                       f"and achieved Gen-{grave_entry['final_generation']} status. "
                       f"Their sacrifice will be remembered.",
                fragment_type="funeral_rite",
                mood="somber",
                setting="graveyard",
                tags=["perma", "death", "memorial", grave_entry['death_cause']],
                entity_references=[grave_entry['ship_id']]
            )
            
            # Store funeral story
            # This would integrate with the story system
            logger.info(f"⚰️ Generated funeral rite for {grave_entry['ship_id']}")
            
        except Exception as e:
            logger.error(f"⚰️ Failed to generate funeral rite: {e}")
    
    def refuel_ship(self, ship_id: str, fuel_amount: float, credits: float) -> bool:
        """Refuel ship if player has enough credits"""
        if ship_id not in self.resource_metrics:
            logger.warning(f"⚰️ Cannot refuel unknown ship: {ship_id}")
            return False
        
        cost = fuel_amount * self.refuel_cost_per_percent
        if credits < cost:
            logger.warning(f"⚰️ Insufficient credits for refuel: need {cost}, have {credits}")
            return False
        
        metrics = self.resource_metrics[ship_id]
        metrics.fuel_level = min(100, metrics.fuel_level + fuel_amount)
        
        logger.info(f"⚰️ Refueled {ship_id}: +{fuel_amount:.1f}% fuel, cost {cost:.0f} credits")
        return True
    
    def repair_ship(self, ship_id: str, repair_amount: float, credits: float) -> bool:
        """Repair ship hull if player has enough credits"""
        if ship_id not in self.resource_metrics:
            logger.warning(f"⚰️ Cannot repair unknown ship: {ship_id}")
            return False
        
        cost = repair_amount * self.repair_cost_per_percent
        if credits < cost:
            logger.warning(f"⚰️ Insufficient credits for repair: need {cost}, have {credits}")
            return False
        
        metrics = self.resource_metrics[ship_id]
        metrics.hull_integrity = min(100, metrics.hull_integrity + repair_amount)
        
        logger.info(f"⚰️ Repaired {ship_id}: +{repair_amount:.1f}% hull, cost {cost:.0f} credits")
        return True
    
    def cool_thermal_system(self, ship_id: str, credits: float) -> bool:
        """Cool thermal system if player has enough credits"""
        if ship_id not in self.resource_metrics:
            logger.warning(f"⚰️ Cannot cool unknown ship: {ship_id}")
            return False
        
        if credits < self.thermal_cooling_cost:
            logger.warning(f"⚰️ Insufficient credits for cooling: need {self.thermal_cooling_cost}, have {credits}")
            return False
        
        metrics = self.resource_metrics[ship_id]
        metrics.thermal_load = 0.0
        
        logger.info(f"⚰️ Cooled thermal system for {ship_id}, cost {self.thermal_cooling_cost} credits")
        return True
    
    def get_resource_status(self, ship_id: str) -> Optional[ResourceMetrics]:
        """Get current resource status for ship"""
        return self.resource_metrics.get(ship_id)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all ships and graveyard"""
        active_ships = {}
        for ship_id, metrics in self.resource_metrics.items():
            active_ships[ship_id] = {
                "status": metrics.get_status().value,
                "fuel": metrics.fuel_level,
                "thermal": metrics.thermal_load,
                "hull": metrics.hull_integrity,
                "operational": metrics.is_operational()
            }
        
        return {
            "active_ships": active_ships,
            "graveyard_count": len(self.graveyard),
            "chassis_slots": self.max_chassis_slots,
            "available_slots": self.max_chassis_slots - len(self.resource_metrics)
        }
    
    def get_graveyard(self) -> List[Dict[str, Any]]:
        """Get graveyard entries"""
        return self.graveyard.copy()
    
    def can_deploy_new_ship(self) -> bool:
        """Check if player can deploy a new ship"""
        return len(self.resource_metrics) < self.max_chassis_slots
    
    def get_refit_costs(self, ship_id: str) -> Dict[str, float]:
        """Get refit costs for a ship"""
        if ship_id not in self.resource_metrics:
            return {}
        
        metrics = self.resource_metrics[ship_id]
        
        return {
            "refuel_to_full": (100 - metrics.fuel_level) * self.refuel_cost_per_percent,
            "repair_to_full": (100 - metrics.hull_integrity) * self.repair_cost_per_percent,
            "thermal_cooling": self.thermal_cooling_cost if metrics.thermal_load > 0 else 0
        }


# Factory function for easy initialization
def create_stakes_manager(registry: UniversalRegistry, max_chassis_slots: int = 3) -> StakesManager:
    """Create a StakesManager instance"""
    return StakesManager(registry, max_chassis_slots)
