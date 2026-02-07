"""
DGT Racing Service
Terrain-aware racing system ported from TurboShells
Integrated with DGT's distributed architecture and Universal Packet system
"""

import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml

from loguru import logger
from .genetics import TurboGenome, TerrainType, genetic_registry


@dataclass
class RaceCheckpoint:
    """Race checkpoint with position and terrain"""
    x: float
    y: float
    radius: float = 20.0
    index: int = 0
    terrain_type: TerrainType = TerrainType.NORMAL
    
    def is_reached(self, turtle_x: float, turtle_y: float) -> bool:
        """Check if turtle reached this checkpoint"""
        distance = math.sqrt((turtle_x - self.x) ** 2 + (turtle_y - self.y) ** 2)
        return distance <= self.radius


@dataclass
class RaceTrack:
    """Race track with checkpoints and terrain data"""
    width: int = 800
    height: int = 600
    checkpoints: List[RaceCheckpoint] = field(default_factory=list)
    terrain_map: Dict[str, Any] = field(default_factory=dict)
    total_distance: float = 1000.0
    
    def add_checkpoint(self, x: float, y: float, terrain: TerrainType = TerrainType.NORMAL, radius: float = 20.0):
        """Add checkpoint to track"""
        index = len(self.checkpoints)
        checkpoint = RaceCheckpoint(x=x, y=y, radius=radius, index=index, terrain_type=terrain)
        self.checkpoints.append(checkpoint)
    
    def get_terrain_at(self, x: float, y: float) -> TerrainType:
        """Get terrain type at position"""
        # Check if near any checkpoint
        for checkpoint in self.checkpoints:
            if checkpoint.is_reached(x, y):
                return checkpoint.terrain_type
        
        # Default terrain based on position
        if x < 100 or x > 700 or y < 100 or y > 500:
            return TerrainType.ROCKS
        elif 300 <= x <= 500 and 200 <= y <= 400:
            return TerrainType.WATER
        elif 200 <= x <= 300 or 500 <= x <= 600:
            return TerrainType.GRASS
        elif 100 <= x <= 200 or 600 <= x <= 700:
            return TerrainType.SAND
        else:
            return TerrainType.NORMAL
    
    def generate_oval_track(self):
        """Generate standard oval track with varied terrain"""
        self.checkpoints = []
        
        # Define oval track with terrain variety
        track_points = [
            (150, 150, TerrainType.GRASS),    # Top left - grass
            (400, 100, TerrainType.NORMAL),   # Top center - normal
            (650, 150, TerrainType.ROCKS),    # Top right - rocks
            (750, 300, TerrainType.SAND),     # Right center - sand
            (650, 450, TerrainType.MUD),      # Bottom right - mud
            (400, 500, TerrainType.WATER),    # Bottom center - water
            (150, 450, TerrainType.GRASS),    # Bottom left - grass
            (50, 300, TerrainType.BOOST),     # Left center - boost
            (400, 300, TerrainType.NORMAL),   # Center/finish - normal
        ]
        
        for x, y, terrain in track_points:
            self.add_checkpoint(x, y, terrain)
        
        # Calculate total distance
        self.total_distance = self._calculate_total_distance()
        
        logger.info(f"🏁 Generated oval track: {len(self.checkpoints)} checkpoints, {self.total_distance:.1f}m total")
    
    def _calculate_total_distance(self) -> float:
        """Calculate total track distance"""
        if len(self.checkpoints) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(self.checkpoints)):
            current = self.checkpoints[i]
            next_point = self.checkpoints[(i + 1) % len(self.checkpoints)]
            distance = math.sqrt((next_point.x - current.x) ** 2 + (next_point.y - current.y) ** 2)
            total += distance
        
        return total


@dataclass
class RacerState:
    """Current state of a racing turtle"""
    turtle_id: str
    genome: TurboGenome
    x: float = 0.0
    y: float = 0.0
    current_checkpoint: int = 0
    race_time: float = 0.0
    distance_traveled: float = 0.0
    current_speed: float = 0.0
    stamina_remaining: float = 100.0
    finished: bool = False
    finish_time: Optional[float] = None
    position: int = 0
    
    def update_position(self, dt: float, terrain: TerrainType):
        """Update racer position based on terrain and genetics"""
        if self.finished:
            return
        
        # Calculate effective speed on terrain
        base_speed = self.genome.calculate_speed_on_terrain(terrain)
        
        # Apply stamina effects
        stamina_factor = max(0.3, self.stamina_remaining / 100.0)
        effective_speed = base_speed * stamina_factor
        
        # Apply intelligence (strategy)
        intelligence_factor = 0.9 + (self.genome.intelligence * 0.1)
        final_speed = effective_speed * intelligence_factor
        
        # Update position
        if self.current_checkpoint < len(self.checkpoints) - 1:
            target = self.checkpoints[self.current_checkpoint + 1]
            dx = target.x - self.x
            dy = target.y - self.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            if distance > 0:
                # Move towards next checkpoint
                move_distance = final_speed * dt * 50  # Scale factor for visible movement
                if move_distance >= distance:
                    # Reached checkpoint
                    self.x = target.x
                    self.y = target.y
                    self.current_checkpoint += 1
                    self.distance_traveled += distance
                else:
                    # Move towards checkpoint
                    ratio = move_distance / distance
                    self.x += dx * ratio
                    self.y += dy * ratio
                    self.distance_traveled += move_distance
        
        # Update stamina
        stamina_drain = self._calculate_stamina_drain(terrain)
        self.stamina_remaining = max(0, self.stamina_remaining - stamina_drain * dt)
        
        # Update current speed for display
        self.current_speed = final_speed
        
        # Update race time
        self.race_time += dt
        
        # Check if finished
        if self.current_checkpoint >= len(self.checkpoints) - 1:
            self.finished = True
            self.finish_time = self.race_time
    
    def _calculate_stamina_drain(self, terrain: TerrainType) -> float:
        """Calculate stamina drain based on terrain"""
        drain_multipliers = {
            TerrainType.NORMAL: 1.0,
            TerrainType.GRASS: 0.9,
            TerrainType.WATER: 1.2,
            TerrainType.SAND: 1.4,
            TerrainType.MUD: 2.0,
            TerrainType.ROCKS: 1.3,
            TerrainType.BOOST: 0.8
        }
        
        base_drain = 2.0  # Base stamina drain per second
        terrain_multiplier = drain_multipliers.get(terrain, 1.0)
        
        return base_drain * terrain_multiplier / self.genome.stamina


class RacingService:
    """Server-side racing service with terrain awareness"""
    
    def __init__(self, track: Optional[RaceTrack] = None):
        self.track = track or RaceTrack()
        self.track.generate_oval_track()
        self.racers: Dict[str, RacerState] = {}
        self.race_active = False
        self.race_start_time = 0.0
        self.race_results: List[Dict[str, Any]] = []
        self.checkpoint_interval = 0.1  # Update every 100ms
        
        logger.info("🏁 Racing Service initialized")
    
    def register_racer(self, turtle_id: str, genome: TurboGenome, start_position: Optional[Tuple[float, float]] = None):
        """Register a turtle for racing"""
        if start_position is None:
            # Start at first checkpoint
            start_position = (self.track.checkpoints[0].x, self.track.checkpoints[0].y)
        
        racer = RacerState(
            turtle_id=turtle_id,
            genome=genome,
            x=start_position[0],
            y=start_position[1],
            current_checkpoint=0
        )
        
        self.racers[turtle_id] = racer
        logger.debug(f"🏁 Registered racer: {turtle_id}")
    
    def start_race(self) -> bool:
        """Start the race if enough racers are registered"""
        if len(self.racers) < 2:
            logger.warning("🏁 Need at least 2 racers to start")
            return False
        
        self.race_active = True
        self.race_start_time = time.time()
        self.race_results = []
        
        # Reset all racers
        for racer in self.racers.values():
            racer.current_checkpoint = 0
            racer.race_time = 0.0
            racer.distance_traveled = 0.0
            racer.stamina_remaining = 100.0
            racer.finished = False
            racer.finish_time = None
            racer.position = 0
            # Reset to start position
            racer.x = self.track.checkpoints[0].x
            racer.y = self.track.checkpoints[0].y
        
        logger.info(f"🏁 Race started with {len(self.racers)} racers")
        return True
    
    def update_race(self, dt: float) -> Dict[str, Any]:
        """Update race state and return results"""
        if not self.race_active:
            return {}
        
        # Update each racer
        for turtle_id, racer in self.racers.items():
            # Get current terrain
            terrain = self.track.get_terrain_at(racer.x, racer.y)
            
            # Update position
            racer.update_position(dt, terrain)
        
        # Update positions (ranking)
        self._update_positions()
        
        # Check if race is finished
        if self._is_race_finished():
            self._finish_race()
        
        # Return current race state
        return self._get_race_state()
    
    def _update_positions(self):
        """Update racer positions based on progress"""
        # Sort by checkpoint progress and distance
        sorted_racers = sorted(
            self.racers.values(),
            key=lambda r: (r.current_checkpoint, r.distance_traveled, -r.race_time),
            reverse=True
        )
        
        for i, racer in enumerate(sorted_racers):
            racer.position = i + 1
    
    def _is_race_finished(self) -> bool:
        """Check if all racers have finished"""
        return all(racer.finished for racer in self.racers.values())
    
    def _finish_race(self):
        """Finish the race and record results"""
        self.race_active = False
        
        # Sort by finish time
        finished_racers = [r for r in self.racers.values() if r.finished]
        finished_racers.sort(key=lambda r: r.finish_time or float('inf'))
        
        # Record results
        self.race_results = []
        for i, racer in enumerate(finished_racers):
            result = {
                'position': i + 1,
                'turtle_id': racer.turtle_id,
                'finish_time': racer.finish_time,
                'distance_traveled': racer.distance_traveled,
                'avg_speed': racer.distance_traveled / (racer.finish_time or 1.0),
                'genetic_signature': racer.genome.genetic_signature,
                'fitness_score': racer.genome.calculate_fitness()
            }
            self.race_results.append(result)
        
        logger.info(f"🏁 Race finished! Winner: {self.race_results[0]['turtle_id']}")
    
    def _get_race_state(self) -> Dict[str, Any]:
        """Get current race state for broadcasting"""
        return {
            'race_active': self.race_active,
            'race_time': time.time() - self.race_start_time if self.race_active else 0,
            'racers': {
                turtle_id: {
                    'position': racer.position,
                    'x': racer.x,
                    'y': racer.y,
                    'current_checkpoint': racer.current_checkpoint,
                    'speed': racer.current_speed,
                    'stamina': racer.stamina_remaining,
                    'distance': racer.distance_traveled,
                    'finished': racer.finished,
                    'finish_time': racer.finish_time
                }
                for turtle_id, racer in self.racers.items()
            },
            'track_info': {
                'total_checkpoints': len(self.track.checkpoints),
                'total_distance': self.track.total_distance,
                'width': self.track.width,
                'height': self.track.height
            }
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get current leaderboard"""
        if not self.race_active and self.race_results:
            # Return finished race results
            return self.race_results[:limit]
        
        # Return current positions
        current_positions = []
        for racer in sorted(self.racers.values(), key=lambda r: r.position):
            current_positions.append({
                'position': racer.position,
                'turtle_id': racer.turtle_id,
                'checkpoint': racer.current_checkpoint,
                'distance': racer.distance_traveled,
                'speed': racer.current_speed,
                'stamina': racer.stamina_remaining
            })
        
        return current_positions[:limit]
    
    def save_race_log(self, filename: Optional[str] = None):
        """Save race results to YAML log"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"race_log_{timestamp}.yaml"
        
        race_data = {
            'timestamp': time.time(),
            'track_info': {
                'total_distance': self.track.total_distance,
                'checkpoints': len(self.track.checkpoints),
                'width': self.track.width,
                'height': self.track.height
            },
            'participants': [
                {
                    'turtle_id': racer.turtle_id,
                    'genetic_signature': racer.genome.genetic_signature,
                    'fitness_score': racer.genome.calculate_fitness()
                }
                for racer in self.racers.values()
            ],
            'results': self.race_results
        }
        
        try:
            with open(filename, 'w') as f:
                yaml.dump(race_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"🏁 Race log saved: {filename}")
            
        except Exception as e:
            logger.error(f"🏁 Failed to save race log: {e}")
    
    def get_terrain_at_position(self, x: float, y: float) -> TerrainType:
        """Get terrain type at specific position"""
        return self.track.get_terrain_at(x, y)
    
    def cleanup_race(self):
        """Clean up race data"""
        self.racers.clear()
        self.race_active = False
        self.race_results = []
        logger.debug("🏁 Race data cleaned up")
