"""
DGT Neuro-Pilot System - ADR 133 Implementation
NEAT-based neuroevolution for space combat AI

Integrates PyPongAI's NEAT core with RogueAsteroid's physics
Creates intelligent ship pilots that learn through evolution
"""

import math
import neat
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from loguru import logger

from .space_physics import SpaceShip, SpaceVoyagerEngine


# Physics constants from RogueAsteroid
ROGUE_PHYSICS = {
    'SHIP_ACCELERATION': 500,      # Pixels per second squared
    'SHIP_MAX_SPEED': 400,         # Maximum speed in pixels per second
    'SHIP_ROTATION_SPEED': 180,    # Degrees per second
    'SHIP_FRICTION': 0.01,         # Velocity reduction per frame
    'BULLET_SPEED': 1200.0,        # pixels per second
    'BULLET_LIFETIME': 0.5         # seconds before despawning
}


@dataclass
class NeuroInput:
    """Neural network input state for ship AI"""
    # Relative targeting information
    target_distance: float = 0.0      # Distance to nearest target
    target_angle: float = 0.0          # Angle to target (-180 to 180)
    target_velocity_x: float = 0.0     # Target's X velocity
    target_velocity_y: float = 0.0     # Target's Y velocity
    
    # Self state
    self_velocity_x: float = 0.0       # Ship's X velocity
    self_velocity_y: float = 0.0       # Ship's Y velocity
    self_heading: float = 0.0          # Ship's current heading
    self_hull_integrity: float = 100.0  # Ship's health percentage
    
    # Tactical awareness
    nearest_threat_distance: float = 999.0  # Distance to nearest threat
    escape_angle: float = 0.0              # Best escape direction


@dataclass
class NeuroOutput:
    """Neural network output control for ship"""
    thrust: float = 0.0      # 0.0 to 1.0 (no thrust to full thrust)
    rotation: float = 0.0    # -1.0 to 1.0 (left to right rotation)
    fire_weapon: float = 0.0  # 0.0 to 1.0 (don't fire to fire)


class NeuroPilot:
    """NEAT-based neural pilot for space combat"""
    
    def __init__(self, genome, config):
        """Initialize neuro pilot with NEAT genome"""
        self.genome = genome
        self.config = config
        self.net = neat.nn.FeedForwardNetwork.create(genome, config)
        
        # Performance tracking
        self.fitness = 0.0
        self.hits_scored = 0
        self.shots_fired = 0
        self.survival_time = 0.0
        self.damage_dealt = 0.0
        self.damage_taken = 0.0
        
        # Novelty tracking (from PyPongAI)
        self.behavior_history = []
        self.novelty_score = 0.0
        self.last_behavior = None
        
        # Movement pattern memory
        self.last_action = NeuroOutput()
        self.action_history = []
        self.position_history = []
        self.velocity_history = []
        
        # Combat statistics
        self.enemies_destroyed = 0
        self.accuracy = 0.0
        self.tactical_score = 0.0
        
        logger.debug(f"🧠 NeuroPilot initialized with fitness: {self.fitness}")
    
    def calculate_neural_inputs(self, ship: SpaceShip, targets: List[SpaceShip], 
                               threats: List[SpaceShip]) -> NeuroInput:
        """Calculate neural network inputs from game state"""
        inputs = NeuroInput()
        
        # Find nearest target
        if targets:
            nearest_target = min(targets, key=lambda t: self._distance_to(ship, t))
            inputs.target_distance = self._distance_to(ship, nearest_target)
            inputs.target_angle = self._angle_to(ship, nearest_target)
            inputs.target_velocity_x = nearest_target.velocity_x
            inputs.target_velocity_y = nearest_target.velocity_y
        else:
            inputs.target_distance = 999.0
            inputs.target_angle = 0.0
            inputs.target_velocity_x = 0.0
            inputs.target_velocity_y = 0.0
        
        # Self state
        inputs.self_velocity_x = ship.velocity_x
        inputs.self_velocity_y = ship.velocity_y
        inputs.self_heading = ship.heading
        inputs.hull_integrity = ship.hull_integrity
        
        # Threat assessment
        if threats:
            nearest_threat = min(threats, key=lambda t: self._distance_to(ship, t))
            inputs.nearest_threat_distance = self._distance_to(ship, nearest_threat)
            inputs.escape_angle = self._angle_to(ship, nearest_threat) + 180  # Opposite direction
        else:
            inputs.nearest_threat_distance = 999.0
            inputs.escape_angle = 0.0
        
        return inputs
    
    def get_action(self, ship: SpaceShip, targets: List[SpaceShip], 
                   threats: List[SpaceShip]) -> NeuroOutput:
        """Get neural network action for current state"""
        # Calculate inputs
        inputs = self.calculate_neural_inputs(ship, targets, threats)
        
        # Convert to neural network input array with enhanced features
        input_array = [
            # Target information
            self._normalize_distance(inputs.target_distance, 0, 600),
            self._normalize_angle(inputs.target_angle),
            self._normalize_velocity(inputs.target_velocity_x),
            self._normalize_velocity(inputs.target_velocity_y),
            
            # Self state with enhanced movement awareness
            self._normalize_velocity(inputs.self_velocity_x),
            self._normalize_velocity(inputs.self_velocity_y),
            self._normalize_angle(inputs.self_heading),
            self._normalize_health(inputs.hull_integrity),
            
            # Tactical awareness
            self._normalize_distance(inputs.nearest_threat_distance, 0, 600),
            self._normalize_angle(inputs.escape_angle),
            
            # Movement pattern memory (last action feedback)
        ]
        
        # Add movement pattern memory (only 1 input to stay within 11 total)
        if hasattr(self, 'last_action'):
            prev_thrust = self.last_action.thrust
        else:
            prev_thrust = 0.0
        
        input_array.append(prev_thrust)
        
        # Feed through neural network
        output = self.net.activate(input_array)
        
        # Convert neural outputs to actions with enhanced control
        action = NeuroOutput()
        action.thrust = max(0.0, min(1.0, output[0]))  # Clamp to [0, 1]
        action.rotation = max(-1.0, min(1.0, output[1]))  # Clamp to [-1, 1]
        action.fire_weapon = max(0.0, min(1.0, output[2]))  # Clamp to [0, 1]
        
        # Add movement pattern memory
        self.last_action = action
        
        # Track behavior for novelty scoring
        current_behavior = (action.thrust, action.rotation, action.fire_weapon)
        self.behavior_history.append(current_behavior)
        if len(self.behavior_history) > 100:  # Keep last 100 behaviors
            self.behavior_history.pop(0)
        
        return action
    
    def apply_action(self, ship: SpaceShip, action: NeuroOutput, dt: float):
        """Apply neural network action to ship physics"""
        # Track movement patterns
        self.action_history.append(action)
        self.position_history.append((ship.x, ship.y))
        self.velocity_history.append((ship.velocity_x, ship.velocity_y))
        
        # Keep history manageable
        if len(self.action_history) > 50:
            self.action_history.pop(0)
        if len(self.position_history) > 50:
            self.position_history.pop(0)
        if len(self.velocity_history) > 50:
            self.velocity_history.pop(0)
        
        # Apply rotation (from RogueAsteroid physics)
        if abs(action.rotation) > 0.1:  # Dead zone to prevent jitter
            rotation_amount = action.rotation * ROGUE_PHYSICS['SHIP_ROTATION_SPEED'] * dt
            ship.heading += rotation_amount
            ship.heading = ship.heading % 360
        
        # Apply thrust (from RogueAsteroid physics)
        if action.thrust > 0.1:  # Dead zone
            thrust_force = action.thrust * ROGUE_PHYSICS['SHIP_ACCELERATION'] * dt
            rad = math.radians(ship.heading)
            ship.velocity_x += math.cos(rad) * thrust_force
            ship.velocity_y += math.sin(rad) * thrust_force
        
        # Apply friction (space drag from RogueAsteroid)
        ship.velocity_x *= (1.0 - ROGUE_PHYSICS['SHIP_FRICTION'])
        ship.velocity_y *= (1.0 - ROGUE_PHYSICS['SHIP_FRICTION'])
        
        # Limit maximum speed (from RogueAsteroid)
        speed = math.sqrt(ship.velocity_x**2 + ship.velocity_y**2)
        if speed > ROGUE_PHYSICS['SHIP_MAX_SPEED']:
            scale = ROGUE_PHYSICS['SHIP_MAX_SPEED'] / speed
            ship.velocity_x *= scale
            ship.velocity_y *= scale
        
        # Update position
        ship.x += ship.velocity_x * dt
        ship.y += ship.velocity_y * dt
    
    def should_fire_weapon(self, action: NeuroOutput, ship: SpaceShip) -> bool:
        """Determine if ship should fire weapon"""
        return action.fire_weapon > 0.5 and ship.can_fire(time.time())
    
    def update_fitness(self, hit_scored: bool, damage_dealt: float, damage_taken: float, 
                      survived: bool, enemies_destroyed: int, generation: int = 0):
        """Update pilot fitness based on performance with dynamic pressure"""
        # Base fitness components
        if hit_scored:
            self.hits_scored += 1
            self.fitness += 10.0
        
        self.damage_dealt += damage_dealt
        self.fitness += damage_dealt * 0.1
        
        self.damage_taken += damage_taken
        self.fitness -= damage_taken * 0.05
        
        if survived:
            self.survival_time += 1.0
            self.fitness += 1.0  # Small bonus for surviving
        
        self.enemies_destroyed += enemies_destroyed
        self.fitness += enemies_destroyed * 50.0
        
        # Update accuracy
        self.shots_fired += 1
        if self.shots_fired > 0:
            self.accuracy = self.hits_scored / self.shots_fired
            self.fitness += self.accuracy * 20.0  # Accuracy bonus
        
        # Dynamic pressure based on generation
        if generation > 10:
            # Increase pressure in later generations
            pressure_multiplier = 1.0 + (generation / 50.0)  # Up to 2x pressure
            self.fitness *= pressure_multiplier
        
        # Pattern diversity bonus (encourages varied flight patterns)
        pattern_diversity = self._calculate_pattern_diversity()
        self.fitness += pattern_diversity * 5.0
        
        # Movement efficiency bonus (rewards smooth, purposeful movement)
        movement_efficiency = self._calculate_movement_efficiency()
        self.fitness += movement_efficiency * 3.0
        
        # Tactical score (combination of factors)
        self.tactical_score = (self.enemies_destroyed * 10 + 
                              self.accuracy * 5 + 
                              (self.damage_dealt - self.damage_taken) * 0.1)
    
    def _calculate_pattern_diversity(self) -> float:
        """Calculate diversity of movement patterns"""
        if len(self.action_history) < 10:
            return 0.0
        
        # Analyze recent actions for diversity
        recent_actions = self.action_history[-10:]
        thrust_changes = sum(1 for i in range(1, len(recent_actions)) 
                          if abs(recent_actions[i].thrust - recent_actions[i-1].thrust) > 0.1)
        rotation_changes = sum(1 for i in range(1, len(recent_actions)) 
                            if abs(recent_actions[i].rotation - recent_actions[i-1].rotation) > 0.1)
        
        # Reward diverse patterns
        diversity_score = (thrust_changes + rotation_changes) / 20.0
        return min(1.0, diversity_score)
    
    def _calculate_movement_efficiency(self) -> float:
        """Calculate movement efficiency (smooth, purposeful movement)"""
        if len(self.position_history) < 5:
            return 0.0
        
        # Calculate movement smoothness
        recent_positions = self.position_history[-5:]
        if len(recent_positions) < 2:
            return 0.0
        
        # Check for jittery movement (penalty)
        position_changes = []
        for i in range(1, len(recent_positions)):
            dx = recent_positions[i][0] - recent_positions[i-1][0]
            dy = recent_positions[i][1] - recent_positions[i-1][1]
            distance = math.sqrt(dx**2 + dy**2)
            position_changes.append(distance)
        
        # Reward smooth, consistent movement
        if position_changes:
            avg_movement = sum(position_changes) / len(position_changes)
            variance = sum((x - avg_movement)**2 for x in position_changes) / len(position_changes)
            efficiency = max(0.0, 1.0 - variance / (avg_movement + 1.0))
            return efficiency
        
        return 0.0
    
    def calculate_novelty_score(self, all_behaviors: List[List]) -> float:
        """Calculate novelty score based on behavior diversity (from PyPongAI)"""
        if not self.behavior_history:
            return 0.0
        
        novelty = 0.0
        for behavior in self.behavior_history[-20:]:  # Check last 20 behaviors
            # Count how many other pilots have similar behaviors
            similar_count = 0
            for other_behaviors in all_behaviors:
                if other_behaviors and behavior in other_behaviors[-20:]:
                    similar_count += 1
            
            # Novelty is inversely proportional to similarity
            if similar_count > 0:
                novelty += 1.0 / similar_count
        
        self.novelty_score = novelty / len(self.behavior_history[-20:])
        return self.novelty_score
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            'fitness': self.fitness,
            'hits_scored': self.hits_scored,
            'shots_fired': self.shots_fired,
            'accuracy': self.accuracy,
            'survival_time': self.survival_time,
            'damage_dealt': self.damage_dealt,
            'damage_taken': self.damage_taken,
            'enemies_destroyed': self.enemies_destroyed,
            'tactical_score': self.tactical_score,
            'novelty_score': self.novelty_score,
            'genome_complexity': len(self.genome.connections) if hasattr(self.genome, 'connections') else 0
        }
    
    # Helper methods for normalization
    def _distance_to(self, ship1: SpaceShip, ship2: SpaceShip) -> float:
        """Calculate distance between two ships"""
        dx = ship2.x - ship1.x
        dy = ship2.y - ship1.y
        return math.sqrt(dx**2 + dy**2)
    
    def _angle_to(self, ship1: SpaceShip, ship2: SpaceShip) -> float:
        """Calculate angle from ship1 to ship2"""
        dx = ship2.x - ship1.x
        dy = ship2.y - ship1.y
        angle = math.degrees(math.atan2(dy, dx))
        return (angle - ship1.heading + 180) % 360 - 180
    
    def _normalize_distance(self, distance: float, min_dist: float, max_dist: float) -> float:
        """Normalize distance to [-1, 1] range"""
        if max_dist - min_dist == 0:
            return 0.0
        normalized = (distance - min_dist) / (max_dist - min_dist)
        return max(-1.0, min(1.0, normalized * 2 - 1))
    
    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle to [-1, 1] range"""
        return max(-1.0, min(1.0, angle / 180.0))
    
    def _normalize_velocity(self, velocity: float) -> float:
        """Normalize velocity to [-1, 1] range"""
        max_vel = ROGUE_PHYSICS['SHIP_MAX_SPEED']
        return max(-1.0, min(1.0, velocity / max_vel))
    
    def _normalize_health(self, health: float) -> float:
        """Normalize health to [-1, 1] range"""
        return max(-1.0, min(1.0, (health - 50) / 50))  # 0-100 health mapped to -1 to 1


class NeuroPilotFactory:
    """Factory for creating and managing neuro pilots"""
    
    def __init__(self, config_path: str = "neat_config.txt"):
        """Initialize neuro pilot factory with NEAT configuration"""
        self.config_path = config_path
        self.config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                 neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                 config_path)
        
        # Create initial population
        self.population = neat.Population(self.config)
        self.current_generation = 0
        
        logger.info(f"🧠 NeuroPilotFactory initialized with config: {config_path}")
    
    def create_pilot(self, genome=None) -> NeuroPilot:
        """Create a new neuro pilot"""
        if genome is None:
            genome = self.config.genome_type.new()
            self.config.genome_type.new_genome(genome, self.config.genome_config)
        
        return NeuroPilot(genome, self.config)
    
    def create_population(self, size: int = 50) -> List[NeuroPilot]:
        """Create initial population of neuro pilots"""
        pilots = []
        for genome in self.population.population.values():
            pilots.append(self.create_pilot(genome))
        
        logger.info(f"🧠 Created population of {len(pilots)} neuro pilots")
        return pilots
    
    def evolve_population(self, pilots: List[NeuroPilot]) -> List[NeuroPilot]:
        """Evolve population to next generation"""
        # Extract fitness values
        fitness_dict = {}
        for pilot in pilots:
            fitness_dict[pilot.genome.key] = pilot.fitness
        
        # Set fitness for all genomes in the current population
        for genome_key, fitness in fitness_dict.items():
            if genome_key in self.population.population:
                self.population.population[genome_key].fitness = fitness
        
        # Evolve to next generation using NEAT's built-in methods
        try:
            # Use the population's evolve method which handles everything
            self.population.population = self.population.reproduction.reproduce(
                self.config.species_set.species, self.config.genome_type, 
                self.config.species_set.species, self.config, fitness_dict
            )
        except Exception as e:
            logger.error(f"🧠 NEAT evolution error: {e}")
            # Fallback: create new random population if evolution fails
            self.population = neat.Population(self.config)
        
        # Create new pilots from evolved genomes
        new_pilots = []
        for genome in self.population.population.values():
            new_pilots.append(self.create_pilot(genome))
        
        self.current_generation += 1
        logger.info(f"🧠 Evolved to generation {self.current_generation}")
        
        return new_pilots
    
    def get_best_pilot(self, pilots: List[NeuroPilot]) -> NeuroPilot:
        """Get the best performing pilot from population"""
        return max(pilots, key=lambda p: p.fitness)
    
    def save_best_genome(self, pilot: NeuroPilot, filename: str = "best_pilot.pkl"):
        """Save the best performing genome"""
        import pickle
        
        with open(filename, 'wb') as f:
            pickle.dump(pilot.genome, f)
        
        logger.info(f"🧠 Saved best genome to {filename}")
    
    def load_genome(self, filename: str) -> NeuroPilot:
        """Load a saved genome"""
        import pickle
        
        with open(filename, 'rb') as f:
            genome = pickle.load(f)
        
        return self.create_pilot(genome)
    
    def _serialize_pilot(self, pilot: NeuroPilot) -> Dict:
        """Serialize pilot for multiprocessing using Universal Packet Enforcement (ADR 122)"""
        # Create a simple serializable representation - NO NEAT OBJECTS
        return {
            'pilot_id': pilot.genome.key,
            'fitness': pilot.fitness,
            'hits_scored': pilot.hits_scored,
            'shots_fired': pilot.shots_fired,
            'enemies_destroyed': pilot.enemies_destroyed,
            'accuracy': pilot.accuracy,
            'tactical_score': pilot.tactical_score,
            'novelty_score': pilot.novelty_score
            # Note: We DO NOT serialize the neural network itself
            # The client reconstructs behavior from the physics state
        }
    
    @staticmethod
    def _create_pilot_from_data(pilot_data: Dict) -> NeuroPilot:
        """Create pilot from serialized data using Universal Packet Enforcement (ADR 122)"""
        # For multiprocessing, we only need pilot statistics
        # The actual neural network stays on the server side
        # This method is used for fitness tracking only
        
        # Create a dummy pilot for statistics (neural network not needed for client)
        factory = NeuroPilotFactory("neat_config_minimal.txt")
        
        # Create a minimal genome for identification
        genome = neat.DefaultGenome(pilot_data['pilot_id'])
        
        # Create pilot with the genome
        pilot = factory.create_pilot(genome)
        
        # Restore statistics
        pilot.fitness = pilot_data.get('fitness', 0.0)
        pilot.hits_scored = pilot_data.get('hits_scored', 0)
        pilot.shots_fired = pilot_data.get('shots_fired', 0)
        pilot.enemies_destroyed = pilot_data.get('enemies_destroyed', 0)
        pilot.accuracy = pilot_data.get('accuracy', 0.0)
        pilot.tactical_score = pilot_data.get('tactical_score', 0.0)
        pilot.novelty_score = pilot_data.get('novelty_score', 0.0)
        
        return pilot


# Global neuro pilot factory
neuro_pilot_factory = None

def initialize_neuro_pilot_factory(config_path: str = "neat_config_minimal.txt") -> NeuroPilotFactory:
    """Initialize global neuro pilot factory"""
    global neuro_pilot_factory
    neuro_pilot_factory = NeuroPilotFactory(config_path)
    logger.info("🧠 Global NeuroPilotFactory initialized")
    return neuro_pilot_factory
