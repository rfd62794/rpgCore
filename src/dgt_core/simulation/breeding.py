"""
DGT Genetic Breeding Service
Volume 3: Creative Genesis - TurboShells Mutation Logic

Implements server-side genetic simulation for turtle breeding
with Universal Turtle Packet compliance (ADR 122)
"""

import json
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import math
import hashlib

from loguru import logger
from ..registry.evolution_log import EvolutionLog, GeneticSignature


class ShellPattern(Enum):
    """Shell pattern genetic traits"""
    SOLID = "solid"
    STRIPED = "striped"
    SPOTTED = "spotted"
    SPIRAL = "spiral"
    CAMOUFLAGE = "camouflage"


class ColorGene(Enum):
    """Color genetic markers"""
    EMERALD = "#00FF00"
    SAPPHIRE = "#0000FF"
    RUBY = "#FF0000"
    AMBER = "#FFB000"
    OBSIDIAN = "#303030"
    PEARL = "#F8F8FF"
    GOLD = "#FFD700"
    TURQUOISE = "#40E0D0"


@dataclass
class TurtleGenome:
    """Genetic makeup of a turtle"""
    # Physical traits (dominant/recessive pairs)
    shell_pattern: Tuple[ShellPattern, ShellPattern]
    color_primary: Tuple[ColorGene, ColorGene]
    color_secondary: Tuple[ColorGene, ColorGene]
    
    # Performance traits (polygenic)
    speed_genes: List[float]  # 5 genes affecting speed
    stamina_genes: List[float]  # 3 genes affecting stamina
    intelligence_genes: List[float]  # 4 genes affecting intelligence
    
    # Mutation markers
    mutation_rate: float
    generation: int
    
    def get_dominant_pattern(self) -> ShellPattern:
        """Get dominant shell pattern"""
        return self.shell_pattern[0] if random.random() > 0.5 else self.shell_pattern[1]
    
    def get_dominant_color(self) -> ColorGene:
        """Get dominant primary color"""
        return self.color_primary[0] if random.random() > 0.5 else self.color_primary[1]
    
    def get_secondary_color(self) -> ColorGene:
        """Get dominant secondary color"""
        return self.color_secondary[0] if random.random() > 0.5 else self.color_secondary[1]
    
    def calculate_speed(self) -> float:
        """Calculate phenotypic speed from genes"""
        base_speed = sum(self.speed_genes) / len(self.speed_genes)
        # Add environmental factor
        return base_speed * random.uniform(0.8, 1.2)
    
    def calculate_fitness(self) -> float:
        """Calculate overall fitness score"""
        speed = self.calculate_speed()
        stamina = sum(self.stamina_genes) / len(self.stamina_genes)
        intelligence = sum(self.intelligence_genes) / len(self.intelligence_genes)
        
        # Weighted fitness formula
        return (speed * 0.4 + stamina * 0.3 + intelligence * 0.3) * random.uniform(0.9, 1.1)


@dataclass
class UniversalTurtlePacket:
    """Universal Turtle Packet - ADR 122 Compliance"""
    packet_version: str = "1.0"
    timestamp: float = 0.0
    turtle_id: str = ""
    generation: int = 0
    
    # Physical appearance
    shell_pattern: str = ""
    primary_color: str = ""
    secondary_color: str = ""
    
    # Performance stats
    speed: float = 0.0
    stamina: float = 0.0
    intelligence: float = 0.0
    fitness_score: float = 0.0
    
    # Genetic data (for breeding)
    genome_serialized: str = ""  # JSON string of TurtleGenome
    
    # Metadata
    parent_ids: List[str] = None
    birth_time: float = 0.0
    mutations: List[str] = None
    
    def __post_init__(self):
        if self.parent_ids is None:
            self.parent_ids = []
        if self.mutations is None:
            self.mutations = []
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.birth_time == 0.0:
            self.birth_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniversalTurtlePacket':
        """Create from dictionary"""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(self.to_dict(), separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'UniversalTurtlePacket':
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class GeneticBreedingService:
    """Server-side genetic breeding simulation service"""
    
    def __init__(self, mutation_rate: float = 0.1, population_size: int = 20):
        self.mutation_rate = mutation_rate
        self.population_size = population_size
        self.turtles: Dict[str, TurtleGenome] = {}
        self.generation_counter = 0
        self.last_breeding_time = 0.0
        self.breeding_interval = 5.0  # 5 seconds between generations
        self.last_culling_time = 0.0
        self.culling_interval = 10.0  # 10 seconds between culling
        
        # Evolution logging (ADR 125)
        self.evolution_log = EvolutionLog()
        
        # Initialize founder population
        self._create_founder_population()
        
        logger.info(f"Genetic Breeding Service initialized with {len(self.turtles)} founders")
    
    def _create_founder_population(self):
        """Create initial founder population with diverse genetics"""
        patterns = list(ShellPattern)
        colors = list(ColorGene)
        
        for i in range(self.population_size // 2):  # Start with half population
            turtle_id = f"founder_{i}"
            
            # Random genetics
            genome = TurtleGenome(
                shell_pattern=(random.choice(patterns), random.choice(patterns)),
                color_primary=(random.choice(colors), random.choice(colors)),
                color_secondary=(random.choice(colors), random.choice(colors)),
                speed_genes=[random.uniform(0.3, 1.0) for _ in range(5)],
                stamina_genes=[random.uniform(0.3, 1.0) for _ in range(3)],
                intelligence_genes=[random.uniform(0.3, 1.0) for _ in range(4)],
                mutation_rate=self.mutation_rate,
                generation=0
            )
            
            self.turtles[turtle_id] = genome
        
        logger.info(f"Created {len(self.turtles)} founder turtles")
    
    def breed_turtles(self, parent1_id: str, parent2_id: str) -> Optional[str]:
        """Breed two turtles to create offspring"""
        if parent1_id not in self.turtles or parent2_id not in self.turtles:
            logger.warning(f"Invalid breeding pair: {parent1_id}, {parent2_id}")
            return None
        
        parent1 = self.turtles[parent1_id]
        parent2 = self.turtles[parent2_id]
        
        # Create offspring through genetic crossover
        offspring_genome = self._crossover(parent1, parent2)
        
        # Create genetic signature to prevent ghost turtles
        genome_data = {
            'shell_pattern': [p.value for p in offspring_genome.shell_pattern],
            'color_primary': [c.value for c in offspring_genome.color_primary],
            'color_secondary': [c.value for c in offspring_genome.color_secondary],
            'speed_genes': offspring_genome.speed_genes,
            'stamina_genes': offspring_genome.stamina_genes,
            'intelligence_genes': offspring_genome.intelligence_genes,
            'mutation_rate': offspring_genome.mutation_rate,
            'generation': offspring_genome.generation
        }
        
        genetic_signature = GeneticSignature.create_signature(genome_data)
        offspring_id = f"gen{self.generation_counter}_{genetic_signature}"
        
        # Apply mutations
        if random.random() < offspring_genome.mutation_rate:
            offspring_genome = self._mutate(offspring_genome)
            logger.info(f"Mutation occurred in {offspring_id}")
        
        self.turtles[offspring_id] = offspring_genome
        
        # Log to evolution registry (ADR 125)
        parent_signatures = [
            GeneticSignature.create_signature({
                'shell_pattern': [p.value for p in parent1.shell_pattern],
                'color_primary': [c.value for c in parent1.color_primary],
                'speed_genes': parent1.speed_genes,
                'stamina_genes': parent1.stamina_genes,
                'intelligence_genes': parent1.intelligence_genes,
                'generation': parent1.generation
            }),
            GeneticSignature.create_signature({
                'shell_pattern': [p.value for p in parent2.shell_pattern],
                'color_primary': [c.value for c in parent2.color_primary],
                'speed_genes': parent2.speed_genes,
                'stamina_genes': parent2.stamina_genes,
                'intelligence_genes': parent2.intelligence_genes,
                'generation': parent2.generation
            })
        ]
        
        turtle_data = {
            'turtle_id': offspring_id,
            'generation': offspring_genome.generation,
            'genome_data': genome_data,
            'parent_signatures': parent_signatures,
            'fitness_score': offspring_genome.calculate_fitness(),
            'shell_pattern': offspring_genome.get_dominant_pattern().value,
            'primary_color': offspring_genome.get_dominant_color().value,
            'secondary_color': offspring_genome.get_secondary_color().value,
            'speed': offspring_genome.calculate_speed(),
            'stamina': sum(offspring_genome.stamina_genes) / len(offspring_genome.stamina_genes),
            'intelligence': sum(offspring_genome.intelligence_genes) / len(offspring_genome.intelligence_genes)
        }
        
        self.evolution_log.log_turtle_birth(turtle_data)
        
        logger.debug(f"Bred {parent1_id} + {parent2_id} -> {offspring_id}")
        return offspring_id
    
    def _crossover(self, parent1: TurtleGenome, parent2: TurtleGenome) -> TurtleGenome:
        """Genetic crossover between two parents"""
        def crossover_gene(gene1, gene2):
            return gene1 if random.random() > 0.5 else gene2
        
        def crossover_polygenic(genes1, genes2):
            return [
                genes1[i] if random.random() > 0.5 else genes2[i]
                for i in range(len(genes1))
            ]
        
        return TurtleGenome(
            shell_pattern=(
                crossover_gene(parent1.shell_pattern[0], parent2.shell_pattern[0]),
                crossover_gene(parent1.shell_pattern[1], parent2.shell_pattern[1])
            ),
            color_primary=(
                crossover_gene(parent1.color_primary[0], parent2.color_primary[0]),
                crossover_gene(parent1.color_primary[1], parent2.color_primary[1])
            ),
            color_secondary=(
                crossover_gene(parent1.color_secondary[0], parent2.color_secondary[0]),
                crossover_gene(parent1.color_secondary[1], parent2.color_secondary[1])
            ),
            speed_genes=crossover_polygenic(parent1.speed_genes, parent2.speed_genes),
            stamina_genes=crossover_polygenic(parent1.stamina_genes, parent2.stamina_genes),
            intelligence_genes=crossover_polygenic(parent1.intelligence_genes, parent2.intelligence_genes),
            mutation_rate=(parent1.mutation_rate + parent2.mutation_rate) / 2,
            generation=max(parent1.generation, parent2.generation) + 1
        )
    
    def _mutate(self, genome: TurtleGenome) -> TurtleGenome:
        """Apply random mutations to genome"""
        mutated = TurtleGenome(
            shell_pattern=genome.shell_pattern,
            color_primary=genome.color_primary,
            color_secondary=genome.color_secondary,
            speed_genes=genome.speed_genes.copy(),
            stamina_genes=genome.stamina_genes.copy(),
            intelligence_genes=genome.intelligence_genes.copy(),
            mutation_rate=genome.mutation_rate,
            generation=genome.generation
        )
        
        mutation_type = random.choice(['pattern', 'color', 'speed', 'stamina', 'intelligence'])
        
        if mutation_type == 'pattern' and random.random() < 0.3:
            patterns = list(ShellPattern)
            mutated.shell_pattern = (
                random.choice(patterns),
                mutated.shell_pattern[1]
            )
        
        elif mutation_type == 'color' and random.random() < 0.3:
            colors = list(ColorGene)
            if random.random() < 0.5:
                mutated.color_primary = (
                    random.choice(colors),
                    mutated.color_primary[1]
                )
            else:
                mutated.color_secondary = (
                    random.choice(colors),
                    mutated.color_secondary[1]
                )
        
        elif mutation_type == 'speed':
            idx = random.randint(0, len(mutated.speed_genes) - 1)
            mutated.speed_genes[idx] *= random.uniform(0.8, 1.2)
            mutated.speed_genes[idx] = max(0.1, min(2.0, mutated.speed_genes[idx]))
        
        elif mutation_type == 'stamina':
            idx = random.randint(0, len(mutated.stamina_genes) - 1)
            mutated.stamina_genes[idx] *= random.uniform(0.8, 1.2)
            mutated.stamina_genes[idx] = max(0.1, min(2.0, mutated.stamina_genes[idx]))
        
        elif mutation_type == 'intelligence':
            idx = random.randint(0, len(mutated.intelligence_genes) - 1)
            mutated.intelligence_genes[idx] *= random.uniform(0.8, 1.2)
            mutated.intelligence_genes[idx] = max(0.1, min(2.0, mutated.intelligence_genes[idx]))
        
        return mutated
    
    def select_breeding_pairs(self) -> List[Tuple[str, str]]:
        """Select breeding pairs based on fitness"""
        # Calculate fitness for all turtles
        fitness_scores = [
            (turtle_id, genome.calculate_fitness())
            for turtle_id, genome in self.turtles.items()
        ]
        
        # Sort by fitness (descending)
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select top 50% for breeding
        breeding_candidates = fitness_scores[:len(fitness_scores) // 2]
        
        # Create pairs (tournament selection)
        pairs = []
        candidate_ids = [tid for tid, _ in breeding_candidates]
        
        while len(candidate_ids) >= 2:
            parent1 = candidate_ids.pop(0)
            parent2 = candidate_ids.pop(0)
            pairs.append((parent1, parent2))
        
        return pairs
    
    def evolve_generation(self) -> List[str]:
        """Evolve to next generation"""
        current_time = time.time()
        
        if current_time - self.last_breeding_time < self.breeding_interval:
            return []
        
        self.generation_counter += 1
        self.last_breeding_time = current_time
        
        # Select breeding pairs
        pairs = self.select_breeding_pairs()
        
        # Breed new generation
        new_offspring = []
        for parent1, parent2 in pairs:
            offspring_id = self.breed_turtles(parent1, parent2)
            if offspring_id:
                new_offspring.append(offspring_id)
        
        # Remove old generation (keep only top performers)
        self._cull_population()
        
        logger.info(f"Generation {self.generation_counter}: {len(new_offspring)} offspring born")
        return new_offspring
    
    def _cull_population(self):
        """Remove weakest turtles to maintain population size"""
        if len(self.turtles) <= self.population_size:
            return
        
        # Calculate fitness and sort
        fitness_scores = [
            (turtle_id, genome.calculate_fitness())
            for turtle_id, genome in self.turtles.items()
        ]
        fitness_scores.sort(key=lambda x: x[1])
        
        # Remove weakest turtles
        turtles_to_remove = fitness_scores[:len(self.turtles) - self.population_size]
        for turtle_id, _ in turtles_to_remove:
            del self.turtles[turtle_id]
        
        logger.debug(f"Culled {len(turtles_to_remove)} weak turtles")
    
    def get_alpha_turtle(self) -> Optional[Tuple[str, TurtleGenome]]:
        """Get the alpha turtle (highest fitness)"""
        if not self.turtles:
            return None
        
        best_turtle = max(
            self.turtles.items(),
            key=lambda x: x[1].calculate_fitness()
        )
        
        return best_turtle
    
    def create_turtle_packet(self, turtle_id: str) -> Optional[UniversalTurtlePacket]:
        """Create Universal Turtle Packet for client consumption"""
        if turtle_id not in self.turtles:
            return None
        
        genome = self.turtles[turtle_id]
        
        packet = UniversalTurtlePacket(
            turtle_id=turtle_id,
            generation=genome.generation,
            shell_pattern=genome.get_dominant_pattern().value,
            primary_color=genome.get_dominant_color().value,
            secondary_color=genome.get_secondary_color().value,
            speed=genome.calculate_speed(),
            stamina=sum(genome.stamina_genes) / len(genome.stamina_genes),
            intelligence=sum(genome.intelligence_genes) / len(genome.intelligence_genes),
            fitness_score=genome.calculate_fitness(),
            genome_serialized=json.dumps({
                'shell_pattern': [p.value for p in genome.shell_pattern],
                'color_primary': [c.value for c in genome.color_primary],
                'color_secondary': [c.value for c in genome.color_secondary],
                'speed_genes': genome.speed_genes,
                'stamina_genes': genome.stamina_genes,
                'intelligence_genes': genome.intelligence_genes,
                'mutation_rate': genome.mutation_rate,
                'generation': genome.generation
            })
        )
        
        return packet
    
    def get_population_stats(self) -> Dict[str, Any]:
        """Get population statistics"""
        if not self.turtles:
            return {}
        
        fitness_scores = [genome.calculate_fitness() for genome in self.turtles.values()]
        speeds = [genome.calculate_speed() for genome in self.turtles.values()]
        
        return {
            'population_size': len(self.turtles),
            'generation': self.generation_counter,
            'avg_fitness': sum(fitness_scores) / len(fitness_scores),
            'max_fitness': max(fitness_scores),
            'min_fitness': min(fitness_scores),
            'avg_speed': sum(speeds) / len(speeds),
            'max_speed': max(speeds),
            'min_speed': min(speeds),
            'diversity_score': self._calculate_diversity()
        }
    
    def _calculate_diversity(self) -> float:
        """Calculate genetic diversity score"""
        if len(self.turtles) < 2:
            return 0.0
        
        # Simple diversity metric based on trait variance
        patterns = [genome.get_dominant_pattern() for genome in self.turtles.values()]
        colors = [genome.get_dominant_color() for genome in self.turtles.values()]
        
        pattern_diversity = len(set(patterns)) / len(patterns)
        color_diversity = len(set(colors)) / len(colors)
        
        return (pattern_diversity + color_diversity) / 2
    
    def update(self, dt: float) -> List[UniversalTurtlePacket]:
        """Update breeding service and return new turtle packets"""
        # Evolve generation if it's time
        new_offspring = self.evolve_generation()
        
        # Cull population if it's time (bottom 20% every 10 seconds)
        current_time = time.time()
        if current_time - self.last_culling_time >= self.culling_interval:
            self._cull_bottom_performers()
            self.last_culling_time = current_time
        
        # Create packets for new turtles
        packets = []
        for offspring_id in new_offspring:
            packet = self.create_turtle_packet(offspring_id)
            if packet:
                packets.append(packet)
        
        return packets
    
    def _cull_bottom_performers(self):
        """Cull bottom 20% of performers to make room for new mutations"""
        if len(self.turtles) <= self.population_size // 2:
            return
        
        # Calculate fitness for all turtles
        fitness_scores = [
            (turtle_id, genome.calculate_fitness())
            for turtle_id, genome in self.turtles.items()
        ]
        
        # Sort by fitness (ascending - worst first)
        fitness_scores.sort(key=lambda x: x[1])
        
        # Calculate how many to cull (bottom 20%)
        cull_count = max(1, int(len(self.turtles) * 0.2))
        turtles_to_cull = fitness_scores[:cull_count]
        
        # Remove worst performers
        for turtle_id, fitness in turtles_to_cull:
            del self.turtles[turtle_id]
        
        logger.info(f"🧬 Culled {len(turtles_to_cull)} bottom performers (fitness < {fitness_scores[cull_count-1][1]:.3f})")
    
    def fitness_test(self, distance: float = 100.0) -> Dict[str, float]:
        """Simulate fitness test (100-meter dash) for current generation"""
        results = {}
        
        for turtle_id, genome in self.turtles.items():
            # Calculate race time based on speed and stamina
            speed = genome.calculate_speed()
            stamina = sum(genome.stamina_genes) / len(genome.stamina_genes)
            intelligence = sum(genome.intelligence_genes) / len(genome.intelligence_genes)
            
            # Race simulation: time = distance / (speed * stamina_factor * intelligence_factor)
            stamina_factor = 0.8 + (stamina * 0.4)  # Stamina affects endurance
            intelligence_factor = 0.9 + (intelligence * 0.2)  # Intelligence affects strategy
            
            effective_speed = speed * stamina_factor * intelligence_factor
            race_time = distance / effective_speed if effective_speed > 0 else float('inf')
            
            # Add small random variation (environmental factors)
            race_time *= random.uniform(0.95, 1.05)
            
            results[turtle_id] = race_time
        
        # Sort by race time (fastest first)
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1]))
        
        logger.info(f"🏁 Fitness test completed: {len(sorted_results)} turtles raced {distance}m")
        
        return sorted_results
