"""
DGT Headless Simulation Server - ADR 136 Implementation
Hyperspeed Training Pipeline for Neuro-Evolution

Runs NEAT training at 100x real-time speed without rendering.
Leverages multiprocessing for parallel evaluation across CPU cores.
"""

import os
import json
import time
import pickle
import multiprocessing as mp
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from loguru import logger

from .neuro_pilot import NeuroPilot, NeuroPilotFactory
from .space_physics import SpaceShip, SpaceVoyagerEngine
from .projectile_system import ProjectileSystem
from ..engines.body.ship_renderer import ShipDNA, ShipClass


@dataclass
class HeadlessConfig:
    """Configuration for headless training"""
    pop_size: int = 50
    num_processes: int = None  # Auto-detect CPU cores
    sim_duration: float = 30.0  # Simulated seconds per evaluation
    sim_dt: float = 0.1  # Physics timestep (10Hz)
    fitness_threshold: float = 200000.0  # Auto-stop threshold
    snapshot_interval: int = 5  # Save every N generations
    headless_mode: bool = True
    enable_logging: bool = False


@dataclass
class EliteGenome:
    """Serializable elite genome data"""
    generation: int
    fitness: float
    genome_id: str
    timestamp: float
    performance_stats: Dict[str, Any]
    genome_data: bytes  # Pickled genome


class HeadlessArena:
    """Single headless arena for pilot evaluation"""
    
    def __init__(self, arena_id: int, config: HeadlessConfig):
        self.arena_id = arena_id
        self.config = config
        self.projectile_system = ProjectileSystem()
        
    def evaluate_pilot(self, pilot: NeuroPilot, opponents: List[NeuroPilot]) -> Dict[str, Any]:
        """Evaluate a single pilot against opponents in headless mode"""
        # Create pilot's ship
        ship = SpaceShip(
            ship_id=pilot.genome.key,
            x=500, y=350,
            heading=0,
            velocity_x=0.0, velocity_y=0.0,
            hull_integrity=200.0,
            shield_strength=100.0,
            weapon_range=400.0,
            weapon_damage=25.0,
            fire_rate=2.0
        )
        ship.engine = SpaceVoyagerEngine(thrust_power=0.5, rotation_speed=5.0)
        
        # Create opponent ships
        opponent_ships = []
        for i, opp in enumerate(opponents):
            opp_ship = SpaceShip(
                ship_id=f"opp_{i}",
                x=200 + i * 150, y=350,
                heading=180 if i % 2 else 0,
                velocity_x=0.0, velocity_y=0.0,
                hull_integrity=200.0,
                shield_strength=100.0,
                weapon_range=400.0,
                weapon_damage=25.0,
                fire_rate=2.0
            )
            opp_ship.engine = SpaceVoyagerEngine(thrust_power=0.5, rotation_speed=5.0)
            opponent_ships.append(opp_ship)
        
        # Reset pilot stats
        pilot.fitness = 0.0
        pilot.hits_scored = 0
        pilot.shots_fired = 0
        pilot.damage_dealt = 0.0
        pilot.damage_taken = 0.0
        pilot.enemies_destroyed = 0
        
        # Run simulation
        sim_time = 0.0
        total_steps = int(self.config.sim_duration / self.config.sim_dt)
        
        while sim_time < self.config.sim_duration and not ship.is_destroyed():
            # Get targets (all opponents)
            targets = [s for s in opponent_ships if not s.is_destroyed()]
            if not targets:
                break
            
            # Get neural action
            action = pilot.get_action(ship, targets, targets)
            
            # Apply action
            pilot.apply_action(ship, action, self.config.sim_dt)
            
            # Handle weapon firing
            if pilot.should_fire_weapon(action, ship):
                if targets:
                    target = targets[0]
                    proj_id = self.projectile_system.fire_projectile(ship, target)
                    if proj_id:
                        pilot.shots_fired += 1
            
            # Update projectiles
            impacts = self.projectile_system.update(self.config.sim_dt, [ship] + opponent_ships)
            
            # Handle impacts
            for impact in impacts:
                if impact.target_id == ship.ship_id:
                    pilot.damage_taken += impact.damage_dealt
                    pilot.update_fitness(False, 0, impact.damage_dealt, False, 0)
                else:
                    pilot.damage_dealt += impact.damage_dealt
                    pilot.update_fitness(True, 0, 0, False, 0)
                    
                    # Check for destruction
                    target_ship = next((s for s in opponent_ships if s.ship_id == impact.target_id), None)
                    if target_ship and target_ship.is_destroyed():
                        pilot.enemies_destroyed += 1
                        pilot.update_fitness(True, 0, 0, True, 1)
            
            sim_time += self.config.sim_dt
        
        # Return performance stats
        return pilot.get_performance_stats()


class HeadlessSimulationServer:
    """Hyperspeed headless simulation server for NEAT training"""
    
    def __init__(self, config: HeadlessConfig):
        self.config = config
        self.pilot_factory = NeuroPilotFactory("neat_config_minimal.txt")
        self.current_generation = 0
        self.elite_genomes: List[EliteGenome] = []
        
        # Auto-detect CPU cores if not specified
        if self.config.num_processes is None:
            self.config.num_processes = mp.cpu_count()
        
        # Create registry directory
        self.registry_path = Path("src/dgt_core/registry/brains")
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🚀 HeadlessSimulationServer initialized: {self.config.num_processes} cores")
    
    def run_headless_generation(self, pilots: List[NeuroPilot]) -> List[NeuroPilot]:
        """Run one generation of headless training with multiprocessing"""
        logger.info(f"🧠 Running Generation {self.current_generation} with {len(pilots)} pilots")
        
        # Create pilot groups for parallel evaluation
        pilot_groups = self._create_pilot_groups(pilots)
        
        # Create arenas for each process
        arenas = [HeadlessArena(i, self.config) for i in range(self.config.num_processes)]
        
        # Evaluate pilots in parallel
        with mp.Pool(self.config.num_processes) as pool:
            # Map evaluation tasks to processes
            results = pool.starmap(
                self._evaluate_pilot_group,
                [(arena, group) for arena, group in zip(arenas, pilot_groups)]
            )
        
        # Collect results
        all_stats = []
        for group_stats in results:
            all_stats.extend(group_stats)
        
        # Update pilot fitnesses
        for i, pilot in enumerate(pilots):
            if i < len(all_stats):
                pilot.fitness = all_stats[i]['fitness']
                pilot.hits_scored = all_stats[i]['hits_scored']
                pilot.shots_fired = all_stats[i]['shots_fired']
                pilot.enemies_destroyed = all_stats[i]['enemies_destroyed']
        
        # Find elite pilot
        elite_pilot = max(pilots, key=lambda p: p.fitness)
        
        # Save elite genome
        if self.current_generation % self.config.snapshot_interval == 0:
            self._save_elite_genome(elite_pilot)
        
        # Check fitness threshold
        if elite_pilot.fitness >= self.config.fitness_threshold:
            logger.info(f"🏆 Fitness threshold reached: {elite_pilot.fitness}")
            self._save_elite_genome(elite_pilot, final=True)
            return pilots
        
        self.current_generation += 1
        return pilots
    
    def _create_pilot_groups(self, pilots: List[NeuroPilot]) -> List[List[NeuroPilot]]:
        """Create groups of pilots for parallel evaluation"""
        groups = []
        pilots_per_group = max(1, len(pilots) // self.config.num_processes)
        
        for i in range(0, len(pilots), pilots_per_group):
            group = pilots[i:i + pilots_per_group]
            # Pad group if necessary
            while len(group) < pilots_per_group:
                group.append(pilots[0])  # Use first pilot as filler
            groups.append(group)
        
        return groups
    
    def _evaluate_pilot_group(self, arena: HeadlessArena, pilots: List[NeuroPilot]) -> List[Dict[str, Any]]:
        """Evaluate a group of pilots in a single arena"""
        stats = []
        
        for pilot in pilots:
            # Create opponents (other pilots in group)
            opponents = [p for p in pilots if p != pilot]
            
            # Evaluate pilot
            pilot_stats = arena.evaluate_pilot(pilot, opponents)
            stats.append(pilot_stats)
        
        return stats
    
    def _save_elite_genome(self, pilot: NeuroPilot, final: bool = False):
        """Save elite genome to registry"""
        # Serialize genome
        genome_bytes = pickle.dumps(pilot.genome)
        
        elite_data = EliteGenome(
            generation=self.current_generation,
            fitness=pilot.fitness,
            genome_id=str(pilot.genome.key),
            timestamp=time.time(),
            performance_stats=pilot.get_performance_stats(),
            genome_data=genome_bytes
        )
        
        # Save to file
        suffix = "_final" if final else ""
        filename = f"elite_genome_gen{self.current_generation}{suffix}.json"
        filepath = self.registry_path / filename
        
        # Convert to JSON-serializable format
        json_data = {
            'generation': elite_data.generation,
            'fitness': elite_data.fitness,
            'genome_id': elite_data.genome_id,
            'timestamp': elite_data.timestamp,
            'performance_stats': elite_data.performance_stats,
            'genome_file': f"genome_{elite_data.genome_id}.pkl"
        }
        
        with open(filepath, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Save genome separately
        genome_filepath = self.registry_path / json_data['genome_file']
        with open(genome_filepath, 'wb') as f:
            f.write(genome_bytes)
        
        self.elite_genomes.append(elite_data)
        
        logger.info(f"💾 Saved elite genome: {filename} (fitness: {pilot.fitness:.2f})")
    
    def load_elite_genome(self, filename: str) -> NeuroPilot:
        """Load elite genome from registry"""
        filepath = self.registry_path / filename
        
        with open(filepath, 'r') as f:
            json_data = json.load(f)
        
        # Load genome
        genome_filepath = self.registry_path / json_data['genome_file']
        with open(genome_filepath, 'rb') as f:
            genome = pickle.load(f)
        
        return self.pilot_factory.create_pilot(genome)
    
    def get_latest_elite(self) -> Optional[NeuroPilot]:
        """Get the latest elite pilot"""
        if not self.elite_genomes:
            # Try to load from disk
            elite_files = list(self.registry_path.glob("elite_genome_*.json"))
            if elite_files:
                latest_file = max(elite_files, key=lambda f: f.stat().st_mtime)
                return self.load_elite_genome(latest_file.name)
            return None
        
        latest = max(self.elite_genomes, key=lambda g: g.generation)
        genome = pickle.loads(latest.genome_data)
        return self.pilot_factory.create_pilot(genome)
    
    def run_training_session(self, max_generations: int = 100) -> NeuroPilot:
        """Run complete training session"""
        logger.info(f"🚀 Starting headless training session: {max_generations} generations")
        
        # Create initial population
        pilots = self.pilot_factory.create_population(self.config.pop_size)
        
        for generation in range(max_generations):
            # Run headless generation
            pilots = self.run_headless_generation(pilots)
            
            # Evolve population
            pilots = self.pilot_factory.evolve_population(pilots)
            
            # Check if we reached fitness threshold
            elite_pilot = max(pilots, key=lambda p: p.fitness)
            if elite_pilot.fitness >= self.config.fitness_threshold:
                logger.info(f"🏆 Training complete: fitness {elite_pilot.fitness}")
                return elite_pilot
        
        # Return best pilot after max generations
        best_pilot = max(pilots, key=lambda p: p.fitness)
        logger.info(f"🏆 Training complete: {max_generations} generations, best fitness {best_pilot.fitness}")
        return best_pilot


# Global headless server
headless_server = None

def initialize_headless_server(config: Optional[HeadlessConfig] = None) -> HeadlessSimulationServer:
    """Initialize global headless simulation server"""
    global headless_server
    headless_server = HeadlessSimulationServer(config or HeadlessConfig())
    logger.info("🚀 Global HeadlessSimulationServer initialized")
    return headless_server

def get_headless_server() -> Optional[HeadlessSimulationServer]:
    """Get global headless simulation server"""
    return headless_server
