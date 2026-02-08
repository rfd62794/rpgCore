"""
Evolution Selection System - Meritocratic Selection with Prestige Bias
ADR 156: Apply Prestige Bias to NEAT Selection Process
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import random

from loguru import logger


@dataclass
class GenomeFitness:
    """Genome with fitness and prestige information"""
    genome_id: str
    fitness: float
    victories: int = 0
    generation: int = 0
    prestige_score: float = 0.0
    
    def calculate_prestige_bias(self) -> float:
        """Calculate prestige bias: 10% bonus per victory"""
        return 1.0 + (self.victories * 0.1)  # 10% per victory


class MeritocraticSelector:
    """Pure math-driven selection with prestige bias for genetic evolution"""
    
    def __init__(self, population_size: int = 50, elite_fraction: float = 0.2):
        self.population_size = population_size
        self.elite_count = max(2, int(population_size * elite_fraction))
        self.prestige_weight = 0.3  # How much prestige influences selection vs raw fitness
        
        logger.debug(f"🧬 MeritocraticSelector initialized: pop_size={population_size}, elite_count={self.elite_count}")
    
    def apply_prestige_bias(self, population: List[GenomeFitness]) -> List[GenomeFitness]:
        """Apply prestige bias to population fitness scores - prevents stagnation"""
        biased_population = []
        
        for genome in population:
            # Calculate prestige bias (10% per victory)
            prestige_multiplier = genome.calculate_prestige_bias()
            
            # Apply weighted combination of fitness and prestige
            # Prestige bias scales fitness but doesn't completely override it
            biased_fitness = (
                genome.fitness * (1.0 - self.prestige_weight) +
                (genome.fitness * prestige_multiplier) * self.prestige_weight
            )
            
            # Prevent overflow and ensure newcomers can compete
            # Cap prestige bonus to prevent legendary dominance
            max_prestige_bonus = genome.fitness * 2.0  # Max 2x fitness from prestige
            biased_fitness = min(biased_fitness, max_prestige_bonus)
            
            # Create biased genome for selection
            biased_genome = GenomeFitness(
                genome_id=genome.genome_id,
                fitness=biased_fitness,
                victories=genome.victories,
                generation=genome.generation,
                prestige_score=genome.fitness * (prestige_multiplier - 1.0)
            )
            
            biased_population.append(biased_genome)
        
        return biased_population
    
    def select_parents(self, population: List[GenomeFitness], 
                       num_parents: Optional[int] = None) -> List[GenomeFitness]:
        """Select parents using meritocratic selection with prestige bias"""
        if not population:
            return []
        
        if num_parents is None:
            num_parents = len(population) // 2
        
        # Apply prestige bias
        biased_population = self.apply_prestige_bias(population)
        
        # Sort by biased fitness (descending)
        biased_population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Select elite genomes (always included)
        elite_parents = biased_population[:self.elite_count]
        
        # Select remaining parents via tournament selection with bias
        remaining_parents = num_parents - len(elite_parents)
        if remaining_parents > 0:
            tournament_parents = self._tournament_selection(biased_population, remaining_parents)
            elite_parents.extend(tournament_parents)
        
        logger.debug(f"🧬 Selected {len(elite_parents)} parents with prestige bias")
        return elite_parents[:num_parents]
    
    def _tournament_selection(self, population: List[GenomeFitness], 
                             num_selections: int, tournament_size: int = 3) -> List[GenomeFitness]:
        """Tournament selection with prestige-biased fitness"""
        selected = []
        
        for _ in range(num_selections):
            # Random tournament participants
            tournament = random.sample(population, min(tournament_size, len(population)))
            
            # Select winner based on biased fitness
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        return selected
    
    def calculate_survival_probability(self, population: List[GenomeFitness]) -> Dict[str, float]:
        """Calculate survival probability for each genome"""
        if not population:
            return {}
        
        # Apply prestige bias
        biased_population = self.apply_prestige_bias(population)
        
        # Calculate total fitness
        total_fitness = sum(genome.fitness for genome in biased_population)
        
        if total_fitness <= 0:
            # Equal probability if all fitness is zero
            return {genome.genome_id: 1.0 / len(population) for genome in population}
        
        # Probability proportional to biased fitness
        probabilities = {}
        for genome in biased_population:
            probabilities[genome.genome_id] = genome.fitness / total_fitness
        
        return probabilities
    
    def update_victory_counts(self, population: List[GenomeFitness], 
                            victory_records: Dict[str, int]) -> List[GenomeFitness]:
        """Update victory counts from battle results"""
        updated_population = []
        
        for genome in population:
            victories = victory_records.get(genome.genome_id, 0)
            
            updated_genome = GenomeFitness(
                genome_id=genome.genome_id,
                fitness=genome.fitness,
                victories=victories,
                generation=genome.generation,
                prestige_score=genome.fitness * (victories * 0.1)
            )
            
            updated_population.append(updated_genome)
        
        logger.debug(f"🧬 Updated victory counts for {len(updated_population)} genomes")
        return updated_population
    
    def get_selection_stats(self, population: List[GenomeFitness]) -> Dict[str, float]:
        """Get selection statistics for monitoring"""
        if not population:
            return {}
        
        biased_population = self.apply_prestige_bias(population)
        
        fitnesses = [g.fitness for g in population]
        biased_fitnesses = [g.fitness for g in biased_population]
        victories = [g.victories for g in population]
        
        return {
            "population_size": len(population),
            "avg_fitness": np.mean(fitnesses),
            "avg_biased_fitness": np.mean(biased_fitnesses),
            "fitness_std": np.std(fitnesses),
            "total_victories": sum(victories),
            "avg_victories": np.mean(victories),
            "max_victories": max(victories) if victories else 0,
            "prestige_impact": np.mean(biased_fitnesses) - np.mean(fitnesses)
        }


# Factory function for easy initialization
def create_meritocratic_selector(population_size: int = 50, 
                                elite_fraction: float = 0.2) -> MeritocraticSelector:
    """Create a MeritocraticSelector instance"""
    return MeritocraticSelector(population_size, elite_fraction)


# Global selector instance
meritocratic_selector = create_meritocratic_selector()
