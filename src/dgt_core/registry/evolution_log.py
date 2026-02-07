"""
DGT Evolution Log - ADR 125: Genetic Persistence Protocol
Ported and refactored from TurboShells for DGT distributed architecture
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import yaml

from loguru import logger


class GeneticSignature:
    """Hash-based genetic signature to prevent ghost turtles"""
    
    @staticmethod
    def create_signature(genome_data: Dict[str, Any]) -> str:
        """Create unique signature from genetic data"""
        # Sort genome data for consistent hashing
        sorted_data = json.dumps(genome_data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]
    
    @staticmethod
    def verify_signature(genome_data: Dict[str, Any], signature: str) -> bool:
        """Verify genetic signature matches data"""
        expected = GeneticSignature.create_signature(genome_data)
        return expected == signature


@dataclass
class EvolutionEntry:
    """Single evolution log entry"""
    timestamp: float
    generation: int
    turtle_id: str
    genetic_signature: str
    fitness_score: float
    shell_pattern: str
    primary_color: str
    secondary_color: str
    speed: float
    stamina: float
    intelligence: float
    genome_data: Dict[str, Any]
    parent_signatures: List[str] = None
    
    def __post_init__(self):
        if self.parent_signatures is None:
            self.parent_signatures = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionEntry':
        """Create from dictionary"""
        return cls(**data)


class EvolutionLog:
    """Evolution log manager for genetic persistence"""
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path(__file__).parent.parent.parent.parent / "data" / "evolution_log.yaml"
        self.entries: List[EvolutionEntry] = []
        self._ensure_log_directory()
        self._load_existing_log()
        
        logger.info(f"🧬 Evolution Log initialized: {self.log_path}")
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_existing_log(self):
        """Load existing evolution log"""
        if not self.log_path.exists():
            logger.info("🧬 No existing evolution log, starting fresh")
            return
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data and 'entries' in data:
                for entry_data in data['entries']:
                    entry = EvolutionEntry.from_dict(entry_data)
                    self.entries.append(entry)
                
                logger.info(f"🧬 Loaded {len(self.entries)} evolution entries")
            
        except Exception as e:
            logger.error(f"🧬 Failed to load evolution log: {e}")
            self.entries = []
    
    def _save_log(self):
        """Save evolution log to file"""
        try:
            data = {
                'metadata': {
                    'total_entries': len(self.entries),
                    'last_updated': time.time(),
                    'version': '1.0'
                },
                'entries': [entry.to_dict() for entry in self.entries]
            }
            
            with open(self.log_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            
            logger.debug(f"🧬 Saved {len(self.entries)} entries to evolution log")
            
        except Exception as e:
            logger.error(f"🧬 Failed to save evolution log: {e}")
    
    def log_turtle_birth(self, turtle_data: Dict[str, Any]) -> bool:
        """Log a new turtle birth"""
        try:
            # Create genetic signature
            signature = GeneticSignature.create_signature(turtle_data['genome_data'])
            
            # Check for duplicates (ghost turtles)
            if self._signature_exists(signature):
                logger.warning(f"🧬 Ghost turtle detected: {turtle_data['turtle_id']}")
                return False
            
            # Create evolution entry
            entry = EvolutionEntry(
                timestamp=time.time(),
                generation=turtle_data.get('generation', 0),
                turtle_id=turtle_data['turtle_id'],
                genetic_signature=signature,
                fitness_score=turtle_data.get('fitness_score', 0.0),
                shell_pattern=turtle_data.get('shell_pattern', ''),
                primary_color=turtle_data.get('primary_color', ''),
                secondary_color=turtle_data.get('secondary_color', ''),
                speed=turtle_data.get('speed', 0.0),
                stamina=turtle_data.get('stamina', 0.0),
                intelligence=turtle_data.get('intelligence', 0.0),
                genome_data=turtle_data['genome_data'],
                parent_signatures=turtle_data.get('parent_signatures', [])
            )
            
            self.entries.append(entry)
            
            # Auto-save every 5 entries
            if len(self.entries) % 5 == 0:
                self._save_log()
            
            logger.debug(f"🧬 Logged turtle birth: {turtle_data['turtle_id']} (Gen {entry.generation})")
            return True
            
        except Exception as e:
            logger.error(f"🧬 Failed to log turtle birth: {e}")
            return False
    
    def _signature_exists(self, signature: str) -> bool:
        """Check if genetic signature already exists"""
        return any(entry.genetic_signature == signature for entry in self.entries)
    
    def get_alpha_turtles(self, generation: Optional[int] = None, limit: int = 10) -> List[EvolutionEntry]:
        """Get alpha turtles by generation or overall"""
        filtered_entries = self.entries
        
        if generation is not None:
            filtered_entries = [e for e in filtered_entries if e.generation == generation]
        
        # Sort by fitness score
        filtered_entries.sort(key=lambda e: e.fitness_score, reverse=True)
        
        return filtered_entries[:limit]
    
    def get_generation_stats(self, generation: int) -> Dict[str, Any]:
        """Get statistics for a specific generation"""
        gen_entries = [e for e in self.entries if e.generation == generation]
        
        if not gen_entries:
            return {}
        
        fitness_scores = [e.fitness_score for e in gen_entries]
        speeds = [e.speed for e in gen_entries]
        
        return {
            'generation': generation,
            'population_size': len(gen_entries),
            'avg_fitness': sum(fitness_scores) / len(fitness_scores),
            'max_fitness': max(fitness_scores),
            'min_fitness': min(fitness_scores),
            'avg_speed': sum(speeds) / len(speeds),
            'max_speed': max(speeds),
            'min_speed': min(speeds),
            'diversity_score': self._calculate_generation_diversity(gen_entries)
        }
    
    def _calculate_generation_diversity(self, entries: List[EvolutionEntry]) -> float:
        """Calculate genetic diversity for a generation"""
        if len(entries) < 2:
            return 0.0
        
        patterns = set(e.shell_pattern for e in entries)
        colors = set(e.primary_color for e in entries)
        
        pattern_diversity = len(patterns) / len(entries)
        color_diversity = len(colors) / len(entries)
        
        return (pattern_diversity + color_diversity) / 2
    
    def get_lineage(self, turtle_id: str) -> List[EvolutionEntry]:
        """Get complete lineage for a turtle"""
        # Find the turtle
        turtle_entry = None
        for entry in self.entries:
            if entry.turtle_id == turtle_id:
                turtle_entry = entry
                break
        
        if not turtle_entry:
            return []
        
        # Build lineage tree
        lineage = [turtle_entry]
        
        # Recursively find parents
        def find_parents(signatures: List[str], depth: int = 0):
            if depth > 10 or not signatures:  # Prevent infinite recursion
                return
            
            for signature in signatures:
                for entry in self.entries:
                    if entry.genetic_signature == signature and entry not in lineage:
                        lineage.append(entry)
                        find_parents(entry.parent_signatures, depth + 1)
        
        find_parents(turtle_entry.parent_signatures)
        
        return lineage
    
    def cleanup_old_entries(self, keep_generations: int = 10):
        """Clean up old entries to prevent log bloat"""
        if not self.entries:
            return
        
        # Find generation threshold
        generations = sorted(set(e.generation for e in self.entries))
        cutoff_generation = max(0, max(generations) - keep_generations)
        
        # Keep alpha turtles from old generations
        alpha_to_keep = []
        for gen in generations:
            if gen <= cutoff_generation:
                alphas = self.get_alpha_turtles(generation=gen, limit=3)
                alpha_to_keep.extend(alphas)
        
        # Filter entries
        original_count = len(self.entries)
        self.entries = [
            e for e in self.entries 
            if e.generation > cutoff_generation or e in alpha_to_keep
        ]
        
        removed_count = original_count - len(self.entries)
        if removed_count > 0:
            logger.info(f"🧬 Cleaned up {removed_count} old evolution entries")
            self._save_log()
    
    def export_generation_data(self, generation: int) -> Dict[str, Any]:
        """Export complete generation data for backup"""
        gen_entries = [e for e in self.entries if e.generation == generation]
        
        return {
            'generation': generation,
            'timestamp': time.time(),
            'entries': [e.to_dict() for e in gen_entries],
            'stats': self.get_generation_stats(generation)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get evolution log summary"""
        if not self.entries:
            return {'total_entries': 0, 'generations': 0}
        
        generations = sorted(set(e.generation for e in self.entries))
        
        return {
            'total_entries': len(self.entries),
            'generations': len(generations),
            'first_generation': generations[0],
            'latest_generation': generations[-1],
            'log_path': str(self.log_path),
            'last_updated': max(e.timestamp for e in self.entries)
        }
