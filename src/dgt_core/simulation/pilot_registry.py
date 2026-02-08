"""
DGT Pilot Registry - ADR 138 Implementation
Vessel-Brain Binding System for Elite Pilot Management

Tracks elite genomes, pilot experience, and performance metrics.
Provides the "Football Manager in Space" pilot scouting system.
"""

import os
import json
import time
import pickle
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from loguru import logger


class PilotSpecialization(Enum):
    """Pilot specialization based on performance patterns"""
    INTERCEPTOR = "interceptor"  # High thrust, agile combat
    HEAVY = "heavy"             # Tank, sustained combat
    SCOUT = "scout"              # Evasion, reconnaissance
    BOMBER = "bomber"           # Precision strikes
    UNIVERSAL = "universal"     # Balanced performance


@dataclass
class PilotStats:
    """Comprehensive pilot performance statistics"""
    # Core metrics
    fitness: float = 0.0
    accuracy: float = 0.0
    aggression: float = 0.0      # Combat engagement rate
    precision: float = 0.0       # Shot accuracy vs damage
    evasion: float = 0.0         # Damage avoidance
    efficiency: float = 0.0      # Resource management
    
    # Combat record
    confirmed_kills: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    total_battles: int = 0
    
    # Experience
    prestige_points: int = 0
    hire_count: int = 0          # Times hired by commanders
    total_service_time: float = 0.0
    
    # Genetic traits
    genome_complexity: int = 0
    novelty_score: float = 0.0
    
    def get_win_rate(self) -> float:
        """Calculate win rate"""
        if self.total_battles == 0:
            return 0.0
        return self.battles_won / self.total_battles
    
    def get_kd_ratio(self) -> float:
        """Calculate K/D ratio"""
        if self.battles_lost == 0:
            return float('inf') if self.confirmed_kills > 0 else 0.0
        return self.confirmed_kills / self.battles_lost
    
    def get_combat_rating(self) -> float:
        """Overall combat rating (0-100)"""
        return (
            self.fitness * 0.3 +
            self.accuracy * 20 +
            self.aggression * 15 +
            self.precision * 15 +
            self.evasion * 15 +
            self.efficiency * 15
        ) / 100


@dataclass
class ElitePilot:
    """Elite pilot with vessel-brain binding"""
    # Identity
    pilot_id: str
    genome_id: str
    call_sign: str
    generation: int
    
    # Performance
    stats: PilotStats
    specialization: PilotSpecialization
    
    # Economics
    base_cost: int = 100
    current_cost: int = 100
    availability: bool = True
    
    # Metadata
    created_at: float = 0.0
    last_battle: float = 0.0
    genome_file: str = ""
    metadata_file: str = ""
    
    def __post_init__(self):
        """Initialize timestamps and calculate combat rating"""
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.current_cost == 100:
            # Dynamic pricing based on performance
            self.current_cost = self.base_cost + int(self.get_combat_rating() * 2)
    
    def update_battle_record(self, won: bool, kills: int, damage_dealt: float, 
                           damage_taken: float, battle_time: float):
        """Update pilot after battle"""
        self.stats.total_battles += 1
        self.stats.total_service_time += battle_time
        self.last_battle = time.time()
        
        if won:
            self.stats.battles_won += 1
            self.stats.prestige_points += 25
            self.current_cost = min(10000, self.current_cost + 10)  # Price increase
        else:
            self.stats.battles_lost += 1
            self.stats.prestige_points += 5
            self.current_cost = max(50, self.current_cost - 5)   # Price decrease
        
        self.stats.confirmed_kills += kills
        
        # Update combat metrics
        if battle_time > 0:
            self.stats.aggression = min(1.0, kills / battle_time)
            self.stats.evasion = max(0.0, 1.0 - (damage_taken / (damage_dealt + 1)))
            self.stats.efficiency = min(1.0, damage_dealt / (damage_taken + 1))
    
    def calculate_compatibility(self, ship_class: str) -> float:
        """Calculate pilot compatibility with ship class (0.0-1.0)"""
        compatibility_map = {
            "interceptor": {
                PilotSpecialization.INTERCEPTOR: 1.0,
                PilotSpecialization.SCOUT: 0.8,
                PilotSpecialization.UNIVERSAL: 0.7,
                PilotSpecialization.BOMBER: 0.5,
                PilotSpecialization.HEAVY: 0.3
            },
            "heavy": {
                PilotSpecialization.HEAVY: 1.0,
                PilotSpecialization.UNIVERSAL: 0.8,
                PilotSpecialization.BOMBER: 0.7,
                PilotSpecialization.INTERCEPTOR: 0.4,
                PilotSpecialization.SCOUT: 0.3
            },
            "scout": {
                PilotSpecialization.SCOUT: 1.0,
                PilotSpecialization.INTERCEPTOR: 0.8,
                PilotSpecialization.UNIVERSAL: 0.7,
                PilotSpecialization.HEAVY: 0.3,
                PilotSpecialization.BOMBER: 0.2
            },
            "bomber": {
                PilotSpecialization.BOMBER: 1.0,
                PilotSpecialization.HEAVY: 0.8,
                PilotSpecialization.UNIVERSAL: 0.7,
                PilotSpecialization.INTERCEPTOR: 0.5,
                PilotSpecialization.SCOUT: 0.4
            }
        }
        
        return compatibility_map.get(ship_class, {}).get(self.specialization, 0.5)


class PilotRegistry:
    """Central registry for elite pilot management"""
    
    def __init__(self, registry_path: str = "src/dgt_core/registry/brains"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # Pilot database
        self.elite_pilots: Dict[str, ElitePilot] = {}
        self.pilot_index: Dict[str, str] = {}  # genome_id -> pilot_id mapping
        
        # Performance tracking
        self.average_fitness: float = 0.0
        self.total_pilots: int = 0
        
        # Load existing registry
        self.load_registry()
        
        logger.info(f"🎖️ PilotRegistry initialized: {len(self.elite_pilots)} pilots")
    
    def scan_for_new_pilots(self) -> List[ElitePilot]:
        """Scan registry directory for new elite genomes"""
        new_pilots = []
        
        # Find all elite genome JSON files
        elite_files = list(self.registry_path.glob("elite_genome_*.json"))
        
        for file_path in elite_files:
            try:
                with open(file_path, 'r') as f:
                    elite_data = json.load(f)
                
                genome_id = elite_data['genome_id']
                
                # Check if pilot already exists
                if genome_id in self.pilot_index:
                    continue
                
                # Create new elite pilot
                pilot = self._create_pilot_from_elite_data(elite_data, file_path.name)
                
                # Add to registry
                self.elite_pilots[pilot.pilot_id] = pilot
                self.pilot_index[genome_id] = pilot.pilot_id
                
                new_pilots.append(pilot)
                
                logger.info(f"🎖️ New elite pilot discovered: {pilot.call_sign} (Gen {pilot.generation})")
                
            except Exception as e:
                logger.error(f"❌ Failed to load elite data from {file_path}: {e}")
        
        # Update statistics
        self._update_statistics()
        
        # Save registry
        if new_pilots:
            self.save_registry()
        
        return new_pilots
    
    def _create_pilot_from_elite_data(self, elite_data: Dict[str, Any], metadata_file: str) -> ElitePilot:
        """Create elite pilot from elite genome data"""
        # Extract performance stats
        perf_stats = elite_data.get('performance_stats', {})
        
        # Create pilot stats
        stats = PilotStats(
            fitness=elite_data.get('fitness', 0.0),
            accuracy=perf_stats.get('accuracy', 0.0),
            genome_complexity=perf_stats.get('genome_complexity', 0),
            novelty_score=perf_stats.get('novelty_score', 0.0)
        )
        
        # Determine specialization based on performance patterns
        specialization = self._determine_specialization(stats)
        
        # Generate call sign
        call_sign = self._generate_call_sign(elite_data.get('generation', 0))
        
        # Create elite pilot
        pilot = ElitePilot(
            pilot_id=f"pilot_{elite_data['genome_id']}",
            genome_id=elite_data['genome_id'],
            call_sign=call_sign,
            generation=elite_data.get('generation', 0),
            stats=stats,
            specialization=specialization,
            created_at=elite_data.get('timestamp', time.time()),
            genome_file=elite_data.get('genome_file', ''),
            metadata_file=metadata_file
        )
        
        return pilot
    
    def _determine_specialization(self, stats: PilotStats) -> PilotSpecialization:
        """Determine pilot specialization based on stats"""
        # Simple heuristic based on available stats
        if stats.accuracy > 0.8:
            return PilotSpecialization.BOMBER
        elif stats.novelty_score > 0.5:
            return PilotSpecialization.SCOUT
        elif stats.fitness > 100:
            return PilotSpecialization.INTERCEPTOR
        else:
            return PilotSpecialization.UNIVERSAL
    
    def _generate_call_sign(self, generation: int) -> str:
        """Generate unique call sign for pilot"""
        prefixes = ["ACE", "VIPER", "PHANTOM", "RAVEN", "GHOST", "SHADOW", "STRIKE", "THUNDER"]
        suffixes = ["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT"]
        
        prefix = prefixes[generation % len(prefixes)]
        suffix = suffixes[self.total_pilots % len(suffixes)]
        number = (self.total_pilots // len(suffixes)) + 1
        
        return f"{prefix}-{suffix}-{number:02d}"
    
    def _update_statistics(self):
        """Update registry statistics"""
        if not self.elite_pilots:
            self.average_fitness = 0.0
            self.total_pilots = 0
            return
        
        fitnesses = [pilot.stats.fitness for pilot in self.elite_pilots.values()]
        self.average_fitness = sum(fitnesses) / len(fitnesses)
        self.total_pilots = len(self.elite_pilots)
    
    def get_top_pilots(self, limit: int = 10, ship_class: Optional[str] = None) -> List[ElitePilot]:
        """Get top pilots by performance"""
        pilots = list(self.elite_pilots.values())
        
        # Filter by ship compatibility if specified
        if ship_class:
            pilots = [p for p in pilots if p.calculate_compatibility(ship_class) > 0.7]
        
        # Sort by combat rating
        pilots.sort(key=lambda p: p.stats.combat_rating(), reverse=True)
        
        return pilots[:limit]
    
    def get_affordable_pilots(self, credits: int) -> List[ElitePilot]:
        """Get pilots that can be hired with available credits"""
        return [p for p in self.elite_pilots.values() 
                if p.availability and p.current_cost <= credits]
    
    def hire_pilot(self, pilot_id: str, commander_credits: int) -> Tuple[bool, Optional[ElitePilot]]:
        """Hire a pilot"""
        pilot = self.elite_pilots.get(pilot_id)
        if not pilot:
            return False, None
        
        if not pilot.availability:
            return False, None
        
        if pilot.current_cost > commander_credits:
            return False, None
        
        # Hire pilot
        pilot.availability = False
        pilot.stats.hire_count += 1
        
        logger.info(f"🎖️ Pilot hired: {pilot.call_sign} for {pilot.current_cost} credits")
        
        self.save_registry()
        return True, pilot
    
    def release_pilot(self, pilot_id: str):
        """Release pilot back to available pool"""
        pilot = self.elite_pilots.get(pilot_id)
        if pilot:
            pilot.availability = True
            logger.info(f"🎖️ Pilot released: {pilot.call_sign}")
            self.save_registry()
    
    def update_pilot_battle_record(self, pilot_id: str, won: bool, kills: int, 
                                 damage_dealt: float, damage_taken: float, battle_time: float):
        """Update pilot battle record"""
        pilot = self.elite_pilots.get(pilot_id)
        if pilot:
            pilot.update_battle_record(won, kills, damage_dealt, damage_taken, battle_time)
            self.save_registry()
    
    def get_pilot_performance_matrix(self, pilot_id: str) -> Dict[str, float]:
        """Get performance matrix for spider chart visualization"""
        pilot = self.elite_pilots.get(pilot_id)
        if not pilot:
            return {}
        
        return {
            'Aggression': pilot.stats.aggression * 100,
            'Precision': pilot.stats.precision * 100,
            'Evasion': pilot.stats.evasion * 100,
            'Efficiency': pilot.stats.efficiency * 100,
            'Accuracy': pilot.stats.accuracy * 100,
            'Combat Rating': pilot.stats.combat_rating()
        }
    
    def save_registry(self):
        """Save registry to disk"""
        registry_data = {
            'pilots': {pid: asdict(pilot) for pid, pilot in self.elite_pilots.items()},
            'pilot_index': self.pilot_index,
            'statistics': {
                'average_fitness': self.average_fitness,
                'total_pilots': self.total_pilots,
                'last_updated': time.time()
            }
        }
        
        registry_file = self.registry_path / "pilot_registry.json"
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2, default=str)
        
        logger.debug(f"🎖️ Pilot registry saved: {len(self.elite_pilots)} pilots")
    
    def load_registry(self):
        """Load registry from disk"""
        registry_file = self.registry_path / "pilot_registry.json"
        
        if not registry_file.exists():
            logger.info("🎖️ No existing registry found, starting fresh")
            return
        
        try:
            with open(registry_file, 'r') as f:
                registry_data = json.load(f)
            
            # Load pilots
            pilots_data = registry_data.get('pilots', {})
            for pilot_id, pilot_dict in pilots_data.items():
                # Convert stats dict to PilotStats
                stats_dict = pilot_dict.pop('stats', {})
                stats = PilotStats(**stats_dict)
                
                # Convert specialization string to enum
                spec_str = pilot_dict.pop('specialization', 'universal')
                specialization = PilotSpecialization(spec_str)
                
                # Create pilot
                pilot = ElitePilot(
                    stats=stats,
                    specialization=specialization,
                    **pilot_dict
                )
                
                self.elite_pilots[pilot_id] = pilot
            
            # Load index
            self.pilot_index = registry_data.get('pilot_index', {})
            
            # Load statistics
            stats = registry_data.get('statistics', {})
            self.average_fitness = stats.get('average_fitness', 0.0)
            self.total_pilots = stats.get('total_pilots', 0)
            
            logger.info(f"🎖️ Pilot registry loaded: {len(self.elite_pilots)} pilots")
            
        except Exception as e:
            logger.error(f"❌ Failed to load pilot registry: {e}")
    
    def get_new_ace_notification(self) -> Optional[Dict[str, Any]]:
        """Check for new ace pilot above average fitness"""
        for pilot in self.elite_pilots.values():
            if (pilot.stats.fitness > self.average_fitness * 1.5 and 
                pilot.stats.hire_count == 0 and
                pilot.availability):
                
                return {
                    'pilot_id': pilot.pilot_id,
                    'call_sign': pilot.call_sign,
                    'fitness': pilot.stats.fitness,
                    'generation': pilot.generation,
                    'cost': pilot.current_cost,
                    'specialization': pilot.specialization.value
                }
        
        return None


# Global pilot registry
pilot_registry = None

def initialize_pilot_registry(registry_path: str = "src/dgt_core/registry/brains") -> PilotRegistry:
    """Initialize global pilot registry"""
    global pilot_registry
    pilot_registry = PilotRegistry(registry_path)
    
    # Scan for new pilots
    new_pilots = pilot_registry.scan_for_new_pilots()
    if new_pilots:
        logger.info(f"🎖️ Discovered {len(new_pilots)} new elite pilots")
    
    return pilot_registry

def get_pilot_registry() -> Optional[PilotRegistry]:
    """Get global pilot registry"""
    return pilot_registry
