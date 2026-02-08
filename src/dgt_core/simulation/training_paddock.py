"""
DGT Training Paddock - ADR 133 Implementation
Headless NEAT training service for fleet evolution

Runs parallel dogfights using multiprocessing
Implements ELO-based ranking and novelty search
"""

import time
import random
import multiprocessing as mp
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from .neuro_pilot import NeuroPilot, NeuroPilotFactory
from .space_physics import SpaceShip, SpaceVoyagerEngine
from .fleet import FleetManager, TeamAffiliation, ShipRole
from .projectile_system import ProjectileSystem, initialize_projectile_system


class TrainingMode(str, Enum):
    """Training mode types"""
    EVOLUTION = "evolution"           # Standard NEAT evolution
    NOVELTY_SEARCH = "novelty"       # Novelty-based evolution
    ELO_RANKING = "elo"              # ELO-based competitive ranking
    HYBRID = "hybrid"                 # Combined approach


@dataclass
class TrainingMatch:
    """Individual training match result"""
    pilot1_id: str
    pilot2_id: str
    winner_id: Optional[str]
    pilot1_fitness: float
    pilot2_fitness: float
    match_duration: float
    shots_fired: int
    hits_scored: int
    novelty_score1: float
    novelty_score2: float


@dataclass
class ELORating:
    """ELO rating system for pilot ranking"""
    pilot_id: str
    rating: float = 1500.0  # Standard ELO starting rating
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    
    def expected_score(self, opponent_rating: float) -> float:
        """Calculate expected score against opponent"""
        return 1.0 / (1.0 + 10.0 ** ((opponent_rating - self.rating) / 400.0))
    
    def update_rating(self, opponent_rating: float, actual_score: float, k_factor: float = 32.0):
        """Update ELO rating based on match result"""
        expected = self.expected_score(opponent_rating)
        self.rating += k_factor * (actual_score - expected)
        self.matches_played += 1
        
        if actual_score > 0.5:
            self.wins += 1
        else:
            self.losses += 1


class HeadlessBattle:
    """Headless battle simulation for training"""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.projectile_system = initialize_projectile_system()
        
    def run_dogfight(self, pilot1: NeuroPilot, pilot2: NeuroPilot, 
                    max_duration: float = 30.0) -> TrainingMatch:
        """Run a single dogfight between two pilots"""
        # Create ships for both pilots
        ship1 = self._create_training_ship(pilot1.genome.key, 200, 300, 0)
        ship2 = self._create_training_ship(pilot2.genome.key, 600, 300, 180)
        
        # Reset pilot statistics
        pilot1.fitness = 0.0
        pilot2.fitness = 0.0
        pilot1.hits_scored = 0
        pilot2.hits_scored = 0
        pilot1.shots_fired = 0
        pilot2.shots_fired = 0
        pilot1.damage_dealt = 0.0
        pilot2.damage_dealt = 0.0
        pilot1.damage_taken = 0.0
        pilot2.damage_taken = 0.0
        pilot1.enemies_destroyed = 0
        pilot2.enemies_destroyed = 0
        
        # Battle simulation
        start_time = time.time()
        battle_time = 0.0
        dt = 1.0 / 60.0
        
        while battle_time < max_duration:
            battle_time += dt
            
            # Get targets and threats
            targets1 = [ship2] if not ship2.is_destroyed() else []
            threats1 = [ship2] if not ship2.is_destroyed() else []
            targets2 = [ship1] if not ship1.is_destroyed() else []
            threats2 = [ship1] if not ship1.is_destroyed() else []
            
            # Get neural actions
            action1 = pilot1.get_action(ship1, targets1, threats1)
            action2 = pilot2.get_action(ship2, targets2, threats2)
            
            # Apply actions
            pilot1.apply_action(ship1, action1, dt)
            pilot2.apply_action(ship2, action2, dt)
            
            # Handle weapon firing
            if pilot1.should_fire_weapon(action1, ship1):
                if self.projectile_system.fire_projectile(ship1, ship2):
                    pilot1.shots_fired += 1
            
            if pilot2.should_fire_weapon(action2, ship2):
                if self.projectile_system.fire_projectile(ship2, ship1):
                    pilot2.shots_fired += 1
            
            # Update projectiles
            active_ships = [ship for ship in [ship1, ship2] if not ship.is_destroyed()]
            impacts = self.projectile_system.update(dt, active_ships)
            
            # Handle impacts
            for impact in impacts:
                if impact.target_id == ship1.ship_id:
                    ship1.take_damage(impact.damage_dealt)
                    pilot1.damage_taken += impact.damage_dealt
                    if ship2.ship_id == impact.projectile_id.split('_')[0]:
                        pilot2.damage_dealt += impact.damage_dealt
                        pilot2.hits_scored += 1
                elif impact.target_id == ship2.ship_id:
                    ship2.take_damage(impact.damage_dealt)
                    pilot2.damage_taken += impact.damage_dealt
                    if ship1.ship_id == impact.projectile_id.split('_')[0]:
                        pilot1.damage_dealt += impact.damage_dealt
                        pilot1.hits_scored += 1
            
            # Keep ships in bounds
            self._keep_ship_in_bounds(ship1)
            self._keep_ship_in_bounds(ship2)
            
            # Update fitness
            pilot1.update_fitness(False, 0, 0, not ship1.is_destroyed(), 0)
            pilot2.update_fitness(False, 0, 0, not ship2.is_destroyed(), 0)
            
            # Check for battle end
            if ship1.is_destroyed() or ship2.is_destroyed():
                break
        
        # Determine winner and calculate final fitness
        winner = None
        if ship1.is_destroyed() and not ship2.is_destroyed():
            winner = pilot2.genome.key
            pilot2.update_fitness(True, 0, 0, True, 1)
            pilot1.update_fitness(False, 0, 0, False, 0)
        elif ship2.is_destroyed() and not ship1.is_destroyed():
            winner = pilot1.genome.key
            pilot1.update_fitness(True, 0, 0, True, 1)
            pilot2.update_fitness(False, 0, 0, False, 0)
        else:
            # Draw - both survived
            pilot1.update_fitness(False, 0, 0, True, 0)
            pilot2.update_fitness(False, 0, 0, True, 0)
        
        # Calculate novelty scores
        all_behaviors = [pilot1.behavior_history, pilot2.behavior_history]
        novelty1 = pilot1.calculate_novelty_score(all_behaviors)
        novelty2 = pilot2.calculate_novelty_score(all_behaviors)
        
        return TrainingMatch(
            pilot1_id=pilot1.genome.key,
            pilot2_id=pilot2.genome.key,
            winner_id=winner,
            pilot1_fitness=pilot1.fitness,
            pilot2_fitness=pilot2.fitness,
            match_duration=battle_time,
            shots_fired=pilot1.shots_fired + pilot2.shots_fired,
            hits_scored=pilot1.hits_scored + pilot2.hits_scored,
            novelty_score1=novelty1,
            novelty_score2=novelty2
        )
    
    def _create_training_ship(self, ship_id: str, x: float, y: float, heading: float) -> SpaceShip:
        """Create a training ship with balanced stats"""
        ship = SpaceShip(
            ship_id=ship_id,
            x=x, y=y,
            heading=heading,
            hull_integrity=150.0,
            shield_strength=75.0,
            weapon_range=350.0,
            weapon_damage=8.0,
            fire_rate=1.5
        )
        ship.physics_engine = SpaceVoyagerEngine(thrust_power=0.4, rotation_speed=4.0)
        return ship
    
    def _keep_ship_in_bounds(self, ship: SpaceShip):
        """Keep ship within battle arena"""
        margin = 50
        if ship.x < margin:
            ship.x = margin
            ship.velocity_x = abs(ship.velocity_x) * 0.5
        elif ship.x > self.width - margin:
            ship.x = self.width - margin
            ship.velocity_x = -abs(ship.velocity_x) * 0.5
        
        if ship.y < margin:
            ship.y = margin
            ship.velocity_y = abs(ship.velocity_y) * 0.5
        elif ship.y > self.height - margin:
            ship.y = self.height - margin
            ship.velocity_y = -abs(ship.velocity_y) * 0.5


class TrainingPaddock:
    """Main training service for neuro-pilot evolution"""
    
    def __init__(self, population_size: int = 50, num_processes: int = None):
        self.population_size = population_size
        self.num_processes = num_processes or min(mp.cpu_count(), 8)
        
        # Initialize NEAT factory with config
        self.pilot_factory = NeuroPilotFactory("neat_config_minimal.txt")
        self.pilots = self.pilot_factory.create_population(population_size)
        
        # ELO ratings
        self.elo_ratings: Dict[str, ELORating] = {}
        for pilot in self.pilots:
            self.elo_ratings[pilot.genome.key] = ELORating(pilot.genome.key)
        
        # Training statistics
        self.current_generation = 0
        self.total_matches = 0
        self.training_history: List[TrainingMatch] = []
        
        # Training parameters
        self.training_mode = TrainingMode.HYBRID
        self.novelty_weight = 0.3  # Weight for novelty in fitness
        self.elo_weight = 0.2      # Weight for ELO in fitness
        
        logger.info(f"🧠 TrainingPaddock initialized: {population_size} pilots, {self.num_processes} processes")
    
    def run_training_generation(self, num_matches: int = 100) -> List[TrainingMatch]:
        """Run one generation of training matches"""
        logger.info(f"🧠 Running generation {self.current_generation} with {num_matches} matches")
        
        # Generate tournament brackets based on ELO ratings
        matches = self._generate_tournament_matches(num_matches)
        
        # Run matches sequentially (single process to avoid pickling issues)
        all_matches = []
        for match in matches:
            pilot1 = next(p for p in self.pilots if p.genome.key == match[0])
            pilot2 = next(p for p in self.pilots if p.genome.key == match[1])
            
            # Run single match
            battle = HeadlessBattle()
            match_result = battle.run_dogfight(pilot1, pilot2)
            all_matches.append(match_result)
        
        # Update ELO ratings
        self._update_elo_ratings(all_matches)
        
        # Update training history
        self.training_history.extend(all_matches)
        self.total_matches += len(all_matches)
        
        # Calculate novelty scores and adjust fitness
        self._apply_novelty_selection()
        
        logger.info(f"🧠 Generation {self.current_generation} complete: {len(all_matches)} matches")
        return all_matches
    
    def evolve_population(self) -> List[NeuroPilot]:
        """Evolve population to next generation"""
        logger.info(f"🧠 Evolving population from generation {self.current_generation}")
        
        # Evolve using NEAT
        self.pilots = self.pilot_factory.evolve_population(self.pilots)
        
        # Update ELO ratings for new genomes
        for pilot in self.pilots:
            if pilot.genome.key not in self.elo_ratings:
                self.elo_ratings[pilot.genome.key] = ELORating(pilot.genome.key)
        
        self.current_generation += 1
        return self.pilots
    
    def _generate_tournament_matches(self, num_matches: int) -> List[Tuple[str, str]]:
        """Generate tournament matches based on ELO ratings"""
        matches = []
        pilot_ids = list(self.elo_ratings.keys())
        
        # Sort by ELO rating for tournament pairing
        sorted_pilots = sorted(pilot_ids, key=lambda pid: self.elo_ratings[pid].rating)
        
        # Generate matches using tournament pairing
        for i in range(num_matches):
            if self.training_mode == TrainingMode.ELO_RANKING:
                # Pair similar ELO ratings
                idx1 = i % len(sorted_pilots)
                idx2 = (i + len(sorted_pilots) // 2) % len(sorted_pilots)
            else:
                # Random pairing with some ELO bias
                idx1 = random.randint(0, len(sorted_pilots) - 1)
                idx2 = random.randint(0, len(sorted_pilots) - 1)
                while idx2 == idx1:
                    idx2 = random.randint(0, len(sorted_pilots) - 1)
            
            matches.append((sorted_pilots[idx1], sorted_pilots[idx2]))
        
        return matches
    
    def _run_single_match_worker(self, pilot1: NeuroPilot, pilot2: NeuroPilot) -> TrainingMatch:
        """Worker function for running single match (for multiprocessing)"""
        battle = HeadlessBattle()
        return battle.run_dogfight(pilot1, pilot2)
    
    def _update_elo_ratings(self, matches: List[TrainingMatch]):
        """Update ELO ratings based on match results"""
        for match in matches:
            if match.winner_id:
                winner_elo = self.elo_ratings[match.winner_id]
                loser_id = match.pilot2_id if match.winner_id == match.pilot1_id else match.pilot1_id
                loser_elo = self.elo_ratings[loser_id]
                
                # Update ratings
                winner_elo.update_rating(loser_elo.rating, 1.0)
                loser_elo.update_rating(winner_elo.rating, 0.0)
            else:
                # Draw - both get small adjustment
                elo1 = self.elo_ratings[match.pilot1_id]
                elo2 = self.elo_ratings[match.pilot2_id]
                
                elo1.update_rating(elo2.rating, 0.5)
                elo2.update_rating(elo1.rating, 0.5)
    
    def _apply_novelty_selection(self):
        """Apply novelty selection to fitness scores"""
        if self.training_mode in [TrainingMode.NOVELTY_SEARCH, TrainingMode.HYBRID]:
            # Calculate novelty scores for all pilots
            all_behaviors = [pilot.behavior_history for pilot in self.pilots]
            
            for pilot in self.pilots:
                novelty = pilot.calculate_novelty_score(all_behaviors)
                
                # Adjust fitness based on novelty
                novelty_bonus = novelty * self.novelty_weight * 50.0
                pilot.fitness += novelty_bonus
    
    def get_best_pilots(self, top_n: int = 5) -> List[NeuroPilot]:
        """Get top performing pilots"""
        return sorted(self.pilots, key=lambda p: p.fitness, reverse=True)[:top_n]
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get comprehensive training statistics"""
        best_pilots = self.get_best_pilots(5)
        
        return {
            'generation': self.current_generation,
            'population_size': len(self.pilots),
            'total_matches': self.total_matches,
            'training_mode': self.training_mode.value,
            'top_fitness': best_pilots[0].fitness if best_pilots else 0,
            'average_fitness': sum(p.fitness for p in self.pilots) / len(self.pilots),
            'top_elo': max(self.elo_ratings.values(), key=lambda e: e.rating).rating,
            'average_elo': sum(e.rating for e in self.elo_ratings.values()) / len(self.elo_ratings),
            'best_pilots': [p.get_performance_stats() for p in best_pilots]
        }
    
    def save_best_pilots(self, num_pilots: int = 5):
        """Save the best performing pilots"""
        best_pilots = self.get_best_pilots(num_pilots)
        
        for i, pilot in enumerate(best_pilots):
            filename = f"generation_{self.current_generation}_rank_{i+1}.pkl"
            self.pilot_factory.save_best_genome(pilot, filename)
        
        logger.info(f"🧠 Saved top {num_pilots} pilots from generation {self.current_generation}")


# Global training paddock instance
training_paddock = None

def initialize_training_paddock(population_size: int = 50, num_processes: int = None) -> TrainingPaddock:
    """Initialize global training paddock"""
    global training_paddock
    training_paddock = TrainingPaddock(population_size, num_processes)
    logger.info("🧠 Global TrainingPaddock initialized")
    return training_paddock
